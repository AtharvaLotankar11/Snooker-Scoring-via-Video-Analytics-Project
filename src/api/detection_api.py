#!/usr/bin/env python3
"""
Detection API for external integration with the snooker analysis system
"""

import logging
import threading
import time
from typing import List, Optional, Dict, Any, Callable
from collections import deque
import queue
import numpy as np

from ..core import IDetectionAPI, FrameAnalysis, SystemConfig
from ..processing import FrameProcessor, VideoInputHandler
from ..visualization import DebugVisualizer, AnalysisPlotter, RealTimeDisplay

# Optional config management import
try:
    from ..config import ConfigManager
    HAS_CONFIG_MANAGEMENT = True
except ImportError:
    HAS_CONFIG_MANAGEMENT = False

logger = logging.getLogger(__name__)

class DetectionAPI(IDetectionAPI):
    """Main API for snooker ball detection and analysis"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.frame_processor = FrameProcessor(config)
        self.video_handler = VideoInputHandler()
        
        # Analysis state
        self.is_running = False
        self.analysis_thread = None
        self.stop_event = threading.Event()
        self.current_video_source = ""
        
        # Results storage
        self.latest_result = None
        self.result_history = deque(maxlen=100)  # Keep last 100 results
        self.result_lock = threading.Lock()
        
        # Callbacks
        self.frame_callbacks: List[Callable[[FrameAnalysis], None]] = []
        self.event_callbacks: List[Callable[[Dict], None]] = []
        
        # Performance monitoring
        self.performance_stats = {
            'frames_analyzed': 0,
            'analysis_start_time': 0,
            'fps_actual': 0.0,
            'fps_target': 30.0
        }
        
        # Visualization components
        self.debug_visualizer = DebugVisualizer(
            enable_overlay=config.debug_mode,
            save_frames=config.save_debug_frames,
            output_directory=config.output_directory
        )
        self.analysis_plotter = AnalysisPlotter()
        self.real_time_display = None
        
        # Configuration management
        self.config_manager = None
        if HAS_CONFIG_MANAGEMENT:
            self.config_manager = ConfigManager()
            self.config_manager.add_change_callback(self._on_config_change)
    
    def initialize(self) -> bool:
        """Initialize the detection system"""
        try:
            logger.info("Initializing detection system...")
            
            # Initialize frame processor
            if not self.frame_processor.initialize_components():
                logger.error("Failed to initialize frame processor")
                return False
            
            logger.info("✅ Detection system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Detection system initialization failed: {e}")
            return False
    
    def start_analysis(self, video_source: str) -> bool:
        """Start video analysis"""
        if self.is_running:
            logger.warning("Analysis already running")
            return False
        
        try:
            # Open video source
            if not self.video_handler.open_source(video_source):
                logger.error(f"Failed to open video source: {video_source}")
                return False
            
            # Store video source
            self.current_video_source = video_source
            
            # Reset state
            self.stop_event.clear()
            self.performance_stats['frames_analyzed'] = 0
            self.performance_stats['analysis_start_time'] = time.time()
            
            # Start analysis thread
            self.analysis_thread = threading.Thread(
                target=self._analysis_worker,
                name="SnookerAnalysis",
                daemon=True
            )
            
            self.is_running = True
            self.analysis_thread.start()
            
            logger.info(f"✅ Analysis started for: {video_source}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start analysis: {e}")
            self.is_running = False
            return False
    
    def stop_analysis(self) -> None:
        """Stop video analysis"""
        if not self.is_running:
            return
        
        logger.info("Stopping analysis...")
        
        # Signal stop
        self.stop_event.set()
        self.is_running = False
        
        # Wait for thread to finish
        if self.analysis_thread and self.analysis_thread.is_alive():
            self.analysis_thread.join(timeout=5.0)
            if self.analysis_thread.is_alive():
                logger.warning("Analysis thread did not stop gracefully")
        
        # Release video source
        self.video_handler.release()
        
        logger.info("✅ Analysis stopped")
    
    def _analysis_worker(self) -> None:
        """Main analysis worker thread"""
        frame_number = 0
        fps_counter = 0
        fps_start_time = time.time()
        
        try:
            while not self.stop_event.is_set() and self.video_handler.is_opened():
                # Read frame
                ret, frame = self.video_handler.read_frame()
                
                if not ret or frame is None:
                    if self.video_handler.source_type == "file":
                        logger.info("Reached end of video file")
                        break
                    else:
                        # For live sources, continue trying
                        time.sleep(0.01)
                        continue
                
                # Process frame
                try:
                    analysis_result = self.frame_processor.process_frame(frame, frame_number, self.current_video_source)
                    
                    # Store result
                    with self.result_lock:
                        self.latest_result = analysis_result
                        self.result_history.append(analysis_result)
                    
                    # Update performance stats
                    self.performance_stats['frames_analyzed'] += 1
                    
                    # Calculate FPS
                    fps_counter += 1
                    if fps_counter >= 30:  # Update FPS every 30 frames
                        current_time = time.time()
                        elapsed = current_time - fps_start_time
                        if elapsed > 0:
                            self.performance_stats['fps_actual'] = fps_counter / elapsed
                        fps_counter = 0
                        fps_start_time = current_time
                    
                    # Call frame callbacks
                    for callback in self.frame_callbacks:
                        try:
                            callback(analysis_result)
                        except Exception as e:
                            logger.error(f"Frame callback error: {e}")
                    
                    # Check for events and call event callbacks
                    self._check_and_notify_events(analysis_result)
                    
                except Exception as e:
                    logger.error(f"Frame processing error: {e}")
                
                frame_number += 1
                
                # Rate limiting for live sources
                if self.video_handler.source_type in ["camera", "stream"]:
                    target_fps = self.performance_stats['fps_target']
                    if target_fps > 0:
                        time.sleep(max(0, 1.0/target_fps - 0.001))
                
        except Exception as e:
            logger.error(f"Analysis worker error: {e}")
        finally:
            self.is_running = False
            logger.info("Analysis worker finished")
    
    def _check_and_notify_events(self, analysis: FrameAnalysis) -> None:
        """Check for events and notify callbacks"""
        # This is a simplified event detection - in practice, you'd use the trajectory analyzer
        events = []
        
        # Example: Ball potting detection
        for ball in analysis.tracked_balls:
            if hasattr(ball, 'was_potted') and ball.was_potted:
                event = {
                    'type': 'ball_potted',
                    'ball_id': ball.track_id,
                    'ball_type': ball.ball_type.name,
                    'frame': analysis.frame_number,
                    'timestamp': analysis.timestamp
                }
                events.append(event)
        
        # Notify event callbacks
        for event in events:
            for callback in self.event_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Event callback error: {e}")
    
    def get_latest_results(self) -> Optional[FrameAnalysis]:
        """Get latest analysis results"""
        with self.result_lock:
            return self.latest_result
    
    def get_analysis_history(self, num_frames: int = 10) -> List[FrameAnalysis]:
        """Get recent analysis history"""
        with self.result_lock:
            if num_frames <= 0:
                return list(self.result_history)
            else:
                return list(self.result_history)[-num_frames:]
    
    def is_analyzing(self) -> bool:
        """Check if analysis is running"""
        return self.is_running
    
    def add_frame_callback(self, callback: Callable[[FrameAnalysis], None]) -> None:
        """Add callback for frame analysis results"""
        self.frame_callbacks.append(callback)
        logger.debug("Frame callback added")
    
    def add_event_callback(self, callback: Callable[[Dict], None]) -> None:
        """Add callback for detected events"""
        self.event_callbacks.append(callback)
        logger.debug("Event callback added")
    
    def remove_frame_callback(self, callback: Callable[[FrameAnalysis], None]) -> None:
        """Remove frame callback"""
        if callback in self.frame_callbacks:
            self.frame_callbacks.remove(callback)
            logger.debug("Frame callback removed")
    
    def remove_event_callback(self, callback: Callable[[Dict], None]) -> None:
        """Remove event callback"""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
            logger.debug("Event callback removed")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        video_props = self.video_handler.get_video_properties()
        processing_stats = self.frame_processor.get_processing_stats()
        component_status = self.frame_processor.get_component_status()
        
        return {
            'is_analyzing': self.is_analyzing(),
            'video_source': video_props,
            'processing_stats': processing_stats,
            'component_status': component_status,
            'performance': self.performance_stats.copy(),
            'calibration_status': {
                'is_calibrated': self.frame_processor.get_current_calibration().is_calibrated(),
                'calibration_data': self.frame_processor.get_current_calibration()
            }
        }
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """Get detection summary from latest results"""
        latest = self.get_latest_results()
        if not latest:
            return {'error': 'No analysis results available'}
        
        # Format detections for API response
        formatted_detections = self.frame_processor.detection_engine.get_formatted_detections(latest.detections)
        detection_summary = self.frame_processor.detection_engine.get_detection_summary(latest.detections)
        
        # Format tracked balls
        active_tracks = [
            {
                'track_id': ball.track_id,
                'ball_type': ball.ball_type.name,
                'position': {'x': ball.current_position.x, 'y': ball.current_position.y},
                'confidence': ball.confidence_history[-1] if ball.confidence_history else 0.0,
                'trajectory_length': len(ball.trajectory),
                'is_active': ball.is_active
            }
            for ball in latest.tracked_balls if ball.is_active
        ]
        
        return {
            'frame_number': latest.frame_number,
            'timestamp': latest.timestamp,
            'processing_time': latest.processing_time,
            'detections': formatted_detections,
            'detection_summary': detection_summary,
            'tracked_balls': active_tracks,
            'calibration_status': latest.calibration_data.is_calibrated() if latest.calibration_data else False
        }
    
    def update_configuration(self, config_updates: Dict[str, Any]) -> bool:
        """Update system configuration"""
        try:
            # Update detection threshold
            if 'confidence_threshold' in config_updates:
                threshold = config_updates['confidence_threshold']
                self.frame_processor.update_detection_threshold(threshold)
            
            # Update FPS target
            if 'target_fps' in config_updates:
                self.performance_stats['fps_target'] = config_updates['target_fps']
            
            # Update debug mode
            if 'debug_mode' in config_updates:
                self.frame_processor.set_debug_mode(config_updates['debug_mode'])
            
            logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False
    
    def reset_calibration(self) -> bool:
        """Reset table calibration"""
        try:
            self.frame_processor.reset_calibration()
            logger.info("Calibration reset successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reset calibration: {e}")
            return False
    
    def reset_tracking(self) -> bool:
        """Reset ball tracking"""
        try:
            self.frame_processor.tracker.reset_tracking()
            logger.info("Tracking reset successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reset tracking: {e}")
            return False
    
    def export_analysis_data(self, output_path: str, format: str = 'json') -> bool:
        """Export analysis data to file"""
        try:
            import json
            
            # Collect analysis data
            history = self.get_analysis_history(0)  # Get all history
            
            export_data = {
                'metadata': {
                    'export_timestamp': time.time(),
                    'total_frames': len(history),
                    'video_source': self.video_handler.get_video_properties(),
                    'system_config': {
                        'detection_threshold': self.config.detection.confidence_threshold,
                        'tracking_config': {
                            'max_distance': self.config.tracking.max_tracking_distance,
                            'max_disappeared': self.config.tracking.max_disappeared_frames
                        }
                    }
                },
                'analysis_results': []
            }
            
            # Convert analysis results to serializable format
            for analysis in history:
                result_data = {
                    'frame_number': analysis.frame_number,
                    'timestamp': analysis.timestamp,
                    'processing_time': analysis.processing_time,
                    'detections': [
                        {
                            'ball_type': d.get_ball_type().name,
                            'confidence': d.confidence,
                            'position': {'x': d.get_centroid().x, 'y': d.get_centroid().y},
                            'bbox': {'x1': d.bbox.x1, 'y1': d.bbox.y1, 'x2': d.bbox.x2, 'y2': d.bbox.y2}
                        }
                        for d in analysis.detections
                    ],
                    'tracked_balls': [
                        {
                            'track_id': ball.track_id,
                            'ball_type': ball.ball_type.name,
                            'position': {'x': ball.current_position.x, 'y': ball.current_position.y},
                            'trajectory_length': len(ball.trajectory),
                            'is_active': ball.is_active
                        }
                        for ball in analysis.tracked_balls
                    ]
                }
                export_data['analysis_results'].append(result_data)
            
            # Write to file
            with open(output_path, 'w') as f:
                if format.lower() == 'json':
                    json.dump(export_data, f, indent=2)
                else:
                    logger.error(f"Unsupported export format: {format}")
                    return False
            
            logger.info(f"Analysis data exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export analysis data: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_analysis()
    
    # Visualization Methods
    
    def start_real_time_display(self, window_name: str = "Snooker Detection") -> bool:
        """Start real-time visualization display"""
        try:
            if self.real_time_display and self.real_time_display.is_running:
                logger.warning("Real-time display already running")
                return False
            
            self.real_time_display = RealTimeDisplay(window_name)
            
            # Add callback to update display
            def update_display(analysis: FrameAnalysis):
                if hasattr(self.video_handler, 'current_frame') and self.video_handler.current_frame is not None:
                    self.real_time_display.update_frame(self.video_handler.current_frame, analysis)
            
            self.add_frame_callback(update_display)
            
            return self.real_time_display.start()
            
        except Exception as e:
            logger.error(f"Failed to start real-time display: {e}")
            return False
    
    def stop_real_time_display(self) -> None:
        """Stop real-time visualization display"""
        if self.real_time_display:
            self.real_time_display.stop()
            self.real_time_display = None
    
    def create_debug_visualization(self, frame_number: Optional[int] = None) -> Optional[np.ndarray]:
        """Create debug visualization for specific frame or latest frame"""
        try:
            # Get frame and analysis
            if frame_number is not None:
                # Find specific frame in history
                analysis = None
                for hist_analysis in self.result_history:
                    if hist_analysis.frame_number == frame_number:
                        analysis = hist_analysis
                        break
                
                if analysis is None:
                    logger.warning(f"Frame {frame_number} not found in history")
                    return None
            else:
                # Use latest frame
                analysis = self.get_latest_results()
                if analysis is None:
                    logger.warning("No analysis results available")
                    return None
            
            # Get corresponding video frame (this would need to be stored or retrieved)
            # For now, create a placeholder frame
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            
            # Create visualization
            vis_frame = self.debug_visualizer.visualize_frame_analysis(frame, analysis)
            
            return vis_frame
            
        except Exception as e:
            logger.error(f"Failed to create debug visualization: {e}")
            return None
    
    def generate_analysis_plots(self, output_directory: str = "analysis_plots") -> bool:
        """Generate comprehensive analysis plots"""
        try:
            import os
            os.makedirs(output_directory, exist_ok=True)
            
            # Get analysis history
            history = self.get_analysis_history(len(self.result_history))
            
            if not history:
                logger.warning("No analysis history available for plotting")
                return False
            
            # Generate detection statistics plot
            detection_plot = self.analysis_plotter.plot_detection_statistics(
                history, 
                save_path=f"{output_directory}/detection_statistics.png"
            )
            
            # Generate trajectory analysis plot
            all_tracked_balls = []
            for analysis in history:
                all_tracked_balls.extend(analysis.tracked_balls)
            
            if all_tracked_balls:
                trajectory_plot = self.analysis_plotter.plot_trajectory_analysis(
                    all_tracked_balls,
                    save_path=f"{output_directory}/trajectory_analysis.png"
                )
            
            # Generate system performance plot
            error_stats = self.frame_processor.get_error_statistics()
            performance_plot = self.analysis_plotter.plot_system_performance(
                history,
                error_stats,
                save_path=f"{output_directory}/system_performance.png"
            )
            
            # Generate summary report
            summary = self.analysis_plotter.create_detection_summary_report(
                history,
                save_path=f"{output_directory}/detection_summary.json"
            )
            
            logger.info(f"Analysis plots generated in: {output_directory}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate analysis plots: {e}")
            return False
    
    def save_debug_frame(self, frame_number: Optional[int] = None, 
                        output_path: Optional[str] = None) -> bool:
        """Save debug visualization of specific frame"""
        try:
            vis_frame = self.create_debug_visualization(frame_number)
            
            if vis_frame is None:
                return False
            
            if output_path is None:
                timestamp = int(time.time())
                frame_id = frame_number if frame_number is not None else "latest"
                output_path = f"debug_frame_{frame_id}_{timestamp}.jpg"
            
            import cv2
            cv2.imwrite(output_path, vis_frame)
            
            logger.info(f"Debug frame saved: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save debug frame: {e}")
            return False
    
    def set_visualization_options(self, **options) -> None:
        """Set visualization options"""
        # Update debug visualizer options
        if 'enable_overlay' in options:
            self.debug_visualizer.set_visualization_options(enable_overlay=options['enable_overlay'])
        
        if 'save_frames' in options:
            self.debug_visualizer.set_visualization_options(save_frames=options['save_frames'])
        
        # Update real-time display options
        if self.real_time_display:
            display_options = {k: v for k, v in options.items() 
                             if k.startswith('show_')}
            if display_options:
                self.real_time_display.set_visualization_options(**display_options)
    
    def get_visualization_stats(self) -> Dict[str, Any]:
        """Get visualization statistics"""
        stats = {
            "debug_visualizer": self.debug_visualizer.get_visualization_stats(),
            "real_time_display": None
        }
        
        if self.real_time_display:
            stats["real_time_display"] = self.real_time_display.get_display_stats()
        
        return stats
    
    # Configuration Management Methods
    
    def load_config_from_file(self, config_path: str) -> bool:
        """Load configuration from file"""
        if not self.config_manager:
            logger.warning("Configuration management not available")
            return False
        
        try:
            validation_result = self.config_manager.load_from_file(config_path)
            
            if validation_result.is_valid:
                # Update system configuration
                new_system_config = self.config_manager.get_system_config()
                self._update_system_config(new_system_config)
                
                logger.info(f"Configuration loaded: {validation_result.get_summary()}")
                return True
            else:
                logger.error(f"Configuration validation failed: {validation_result.get_summary()}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False
    
    def save_config_to_file(self, config_path: str, format: str = 'yaml') -> bool:
        """Save current configuration to file"""
        if not self.config_manager:
            logger.warning("Configuration management not available")
            return False
        
        try:
            return self.config_manager.save_to_file(config_path, format)
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_config_value(self, key: str, default=None):
        """Get configuration value using dot notation"""
        if not self.config_manager:
            return default
        
        return self.config_manager.get_value(key, default)
    
    def set_config_value(self, key: str, value, validate: bool = True) -> bool:
        """Set configuration value using dot notation"""
        if not self.config_manager:
            logger.warning("Configuration management not available")
            return False
        
        success = self.config_manager.set_value(key, value, validate)
        
        if success:
            # Apply configuration changes
            new_system_config = self.config_manager.get_system_config()
            self._update_system_config(new_system_config)
        
        return success
    
    def update_config(self, updates: dict, validate: bool = True) -> bool:
        """Update multiple configuration values"""
        if not self.config_manager:
            logger.warning("Configuration management not available")
            return False
        
        validation_result = self.config_manager.update_config(updates, validate)
        
        if validation_result.is_valid:
            # Apply configuration changes
            new_system_config = self.config_manager.get_system_config()
            self._update_system_config(new_system_config)
            return True
        else:
            logger.error(f"Configuration update failed: {validation_result.get_summary()}")
            return False
    
    def validate_config(self) -> dict:
        """Validate current configuration"""
        if not self.config_manager:
            return {"is_valid": False, "message": "Configuration management not available"}
        
        validation_result = self.config_manager.validate_current_config()
        
        return {
            "is_valid": validation_result.is_valid,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "summary": validation_result.get_summary()
        }
    
    def reset_config_to_defaults(self) -> bool:
        """Reset configuration to default values"""
        if not self.config_manager:
            logger.warning("Configuration management not available")
            return False
        
        try:
            self.config_manager.reset_to_defaults()
            
            # Apply default configuration
            new_system_config = self.config_manager.get_system_config()
            self._update_system_config(new_system_config)
            
            logger.info("Configuration reset to defaults")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
            return False
    
    def create_config_template(self, output_path: str, format: str = 'yaml') -> bool:
        """Create configuration template file"""
        if not self.config_manager:
            logger.warning("Configuration management not available")
            return False
        
        try:
            self.config_manager.create_config_template(output_path, format)
            return True
        except Exception as e:
            logger.error(f"Failed to create config template: {e}")
            return False
    
    def export_config_documentation(self, output_path: str, format: str = 'markdown') -> bool:
        """Export configuration documentation"""
        if not self.config_manager:
            logger.warning("Configuration management not available")
            return False
        
        try:
            self.config_manager.export_config_documentation(output_path, format)
            return True
        except Exception as e:
            logger.error(f"Failed to export config documentation: {e}")
            return False
    
    def enable_config_auto_reload(self, check_interval: float = 1.0) -> bool:
        """Enable automatic configuration reloading"""
        if not self.config_manager:
            logger.warning("Configuration management not available")
            return False
        
        try:
            self.config_manager.enable_auto_reload(check_interval)
            return True
        except Exception as e:
            logger.error(f"Failed to enable auto-reload: {e}")
            return False
    
    def disable_config_auto_reload(self) -> bool:
        """Disable automatic configuration reloading"""
        if not self.config_manager:
            return False
        
        try:
            self.config_manager.disable_auto_reload()
            return True
        except Exception as e:
            logger.error(f"Failed to disable auto-reload: {e}")
            return False
    
    def get_config_info(self) -> dict:
        """Get configuration management information"""
        if not self.config_manager:
            return {"available": False}
        
        return {
            "available": True,
            "config_file": str(self.config_manager.config_file) if self.config_manager.config_file else None,
            "auto_reload_enabled": self.config_manager._auto_reload,
            "field_documentation": self.config_manager.get_field_documentation()
        }
    
    def _on_config_change(self, new_config: dict) -> None:
        """Handle configuration changes"""
        try:
            # Convert to SystemConfig and update
            new_system_config = self.config_manager.get_system_config()
            self._update_system_config(new_system_config)
            
            logger.info("Configuration updated automatically")
            
        except Exception as e:
            logger.error(f"Failed to apply configuration changes: {e}")
    
    def _update_system_config(self, new_config: SystemConfig) -> None:
        """Update system configuration"""
        # Update main config
        self.config = new_config
        
        # Update frame processor config
        if hasattr(self.frame_processor, 'config'):
            self.frame_processor.config = new_config
        
        # Update detection engine config
        if hasattr(self.frame_processor, 'detection_engine'):
            detection_engine = self.frame_processor.detection_engine
            if hasattr(detection_engine, 'config'):
                detection_engine.config = new_config.detection
            
            # Update confidence threshold
            if hasattr(detection_engine, 'set_confidence_threshold'):
                detection_engine.set_confidence_threshold(new_config.detection.confidence_threshold)
        
        # Update visualization settings
        if self.debug_visualizer:
            self.debug_visualizer.set_visualization_options(
                enable_overlay=new_config.debug_mode,
                save_frames=new_config.save_debug_frames
            )
        
        logger.debug("System configuration updated")