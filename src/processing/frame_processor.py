#!/usr/bin/env python3
"""
Main frame processing pipeline that coordinates detection, calibration, and tracking
"""

import logging
import time
from typing import List, Optional, Dict, Any
import numpy as np

from ..core import (
    IFrameProcessor, FrameAnalysis, Detection, TrackedBall, CalibrationData,
    SystemConfig, DetectionConfig, TrackingConfig, CalibrationConfig,
    ErrorHandler, ErrorSeverity, ErrorCategory, handle_error,
    ModelReloadStrategy, CalibrationRecoveryStrategy, TrackingResetStrategy,
    GracefulDegradationStrategy, FrameSkipStrategy, MemoryCleanupStrategy
)
from ..detection import BallDetectionEngine
from ..calibration import TableCalibrationEngine, CoordinateTransformer
from ..tracking import BallTracker, TrajectoryAnalyzer

logger = logging.getLogger(__name__)

class FrameProcessor(IFrameProcessor):
    """Main processing pipeline that coordinates all components"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.debug_mode = config.debug_mode
        
        # Initialize error handler
        self.error_handler = ErrorHandler()
        
        # Initialize components
        self.detection_engine = BallDetectionEngine(config.detection)
        self.calibration_engine = TableCalibrationEngine(config.calibration)
        self.tracker = BallTracker(config.tracking)
        self.coordinate_transformer = CoordinateTransformer()
        self.trajectory_analyzer = TrajectoryAnalyzer()
        
        # Setup recovery strategies after components are initialized
        self._setup_recovery_strategies()
        
        # Processing statistics
        self.processing_stats = {
            'frames_processed': 0,
            'total_processing_time': 0.0,
            'avg_processing_time': 0.0,
            'detection_failures': 0,
            'calibration_failures': 0,
            'tracking_failures': 0,
            'last_successful_calibration': -1
        }
        
        # Component initialization status
        self.components_initialized = False
        
        # Graceful degradation context
        self.degradation_context = {}
    
    def _setup_recovery_strategies(self) -> None:
        """Setup recovery strategies for different error categories"""
        # Detection recovery strategies
        self.error_handler.register_recovery_strategy(
            ErrorCategory.DETECTION,
            ModelReloadStrategy(self.detection_engine)
        )
        self.error_handler.register_recovery_strategy(
            ErrorCategory.DETECTION,
            GracefulDegradationStrategy("detection")
        )
        
        # Calibration recovery strategies  
        self.error_handler.register_recovery_strategy(
            ErrorCategory.CALIBRATION,
            CalibrationRecoveryStrategy(self.calibration_engine)
        )
        self.error_handler.register_recovery_strategy(
            ErrorCategory.CALIBRATION,
            GracefulDegradationStrategy("calibration")
        )
        
        # Tracking recovery strategies
        self.error_handler.register_recovery_strategy(
            ErrorCategory.TRACKING,
            TrackingResetStrategy(self.tracker)
        )
        self.error_handler.register_recovery_strategy(
            ErrorCategory.TRACKING,
            GracefulDegradationStrategy("tracking")
        )
        
        # General system recovery strategies
        self.error_handler.register_recovery_strategy(
            ErrorCategory.DATA_PROCESSING,
            FrameSkipStrategy()
        )
        self.error_handler.register_recovery_strategy(
            ErrorCategory.SYSTEM,
            MemoryCleanupStrategy()
        )
        
    def initialize_components(self) -> bool:
        """Initialize all processing components"""
        try:
            # Load detection model
            if not self.detection_engine.load_model():
                logger.error("Failed to load detection model")
                return False
            
            logger.info("✅ All components initialized successfully")
            self.components_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            return False
    
    def process_frame(self, frame: np.ndarray, frame_number: int, 
                     video_source: str = "") -> FrameAnalysis:
        """Process single frame through the complete pipeline"""
        start_time = time.time()
        
        # Initialize result
        analysis = FrameAnalysis(
            frame_number=frame_number,
            timestamp=time.time(),
            detections=[],
            tracked_balls=[],
            calibration_data=None,
            processing_time=0.0
        )
        
        try:
            # Ensure components are initialized
            if not self.components_initialized:
                if not self.initialize_components():
                    logger.error("Cannot process frame - components not initialized")
                    return analysis
            
            # Check for frame skip request
            frame_context = {"frame_number": frame_number, "video_source": video_source}
            if frame_context.get("skip_frame"):
                logger.debug(f"Skipping frame {frame_number} as requested")
                return analysis
            
            # Step 1: Ball Detection
            detections = self._perform_detection(frame)
            analysis.detections = detections
            
            # Step 2: Table Calibration (if needed)
            calibration_data = self._perform_calibration(frame, frame_number, video_source)
            analysis.calibration_data = calibration_data
            
            # Step 3: Update coordinate transformer
            if calibration_data and calibration_data.is_calibrated():
                self.coordinate_transformer.update_calibration_data(calibration_data)
                self.trajectory_analyzer.update_calibration_data(calibration_data)
            
            # Step 4: Ball Tracking
            tracked_balls = self._perform_tracking(detections, frame_number)
            analysis.tracked_balls = tracked_balls
            
            # Step 5: Trajectory Analysis (if enabled)
            if self.config.debug_mode:
                self._perform_trajectory_analysis(tracked_balls)
            
            # Update processing statistics
            processing_time = time.time() - start_time
            analysis.processing_time = processing_time
            self._update_processing_stats(processing_time, True)
            
            if self.debug_mode:
                logger.debug(f"Frame {frame_number} processed in {processing_time:.3f}s - "
                           f"Detections: {len(detections)}, Tracks: {len(tracked_balls)}")
            
        except Exception as e:
            processing_time = time.time() - start_time
            analysis.processing_time = processing_time
            self._update_processing_stats(processing_time, False)
            
            # Handle critical processing error
            context = {
                "frame_number": frame_number,
                "video_source": video_source,
                "frame_shape": frame.shape,
                "degradation_context": self.degradation_context
            }
            
            self.error_handler.handle_error(
                ErrorCategory.DATA_PROCESSING,
                ErrorSeverity.HIGH,
                f"Frame processing failed: {str(e)}",
                e,
                context
            )
            
            # Update degradation context
            self.degradation_context.update(context.get("degradation_context", {}))
        
        return analysis
    
    def _perform_detection(self, frame: np.ndarray) -> List[Detection]:
        """Perform ball detection on frame"""
        # Check for graceful degradation
        if self.degradation_context.get("detection_degraded"):
            if self.degradation_context.get("use_empty_detections"):
                return []
        
        try:
            detections = self.detection_engine.detect_balls(frame)
            
            if self.debug_mode and detections:
                logger.debug(f"Detected {len(detections)} balls")
            
            return detections
            
        except Exception as e:
            self.processing_stats['detection_failures'] += 1
            
            # Handle error with recovery
            context = {
                "frame_shape": frame.shape,
                "model_path": self.config.detection.model_path,
                "degradation_context": self.degradation_context
            }
            
            recovery_successful = self.error_handler.handle_error(
                ErrorCategory.DETECTION,
                ErrorSeverity.HIGH,
                f"Ball detection failed: {str(e)}",
                e,
                context
            )
            
            # Update degradation context
            self.degradation_context.update(context.get("degradation_context", {}))
            
            if recovery_successful or self.degradation_context.get("use_empty_detections"):
                return []
            else:
                # Re-raise if no recovery possible
                raise
    
    def _perform_calibration(self, frame: np.ndarray, frame_number: int, 
                           video_source: str = "") -> Optional[CalibrationData]:
        """Perform table calibration if needed"""
        # Check for graceful degradation
        if self.degradation_context.get("calibration_degraded"):
            if self.degradation_context.get("use_default_calibration"):
                return self._get_default_calibration()
        
        try:
            # Check if we need calibration
            current_calibration = self.calibration_engine.get_calibration_data()
            
            if (not current_calibration.is_calibrated() or 
                (self.config.calibration.auto_recalibrate and 
                 frame_number - self.processing_stats['last_successful_calibration'] > 
                 self.config.calibration.calibration_interval)):
                
                # Attempt calibration
                if self.calibration_engine.calibrate_frame(frame, frame_number, video_source):
                    self.processing_stats['last_successful_calibration'] = frame_number
                    if self.debug_mode:
                        logger.debug(f"Calibration successful at frame {frame_number}")
                else:
                    self.processing_stats['calibration_failures'] += 1
            
            return self.calibration_engine.get_calibration_data()
            
        except Exception as e:
            self.processing_stats['calibration_failures'] += 1
            
            # Handle error with recovery
            context = {
                "frame_number": frame_number,
                "video_source": video_source,
                "frame_shape": frame.shape,
                "degradation_context": self.degradation_context
            }
            
            recovery_successful = self.error_handler.handle_error(
                ErrorCategory.CALIBRATION,
                ErrorSeverity.MEDIUM,
                f"Table calibration failed: {str(e)}",
                e,
                context
            )
            
            # Update degradation context
            self.degradation_context.update(context.get("degradation_context", {}))
            
            if recovery_successful:
                return self.calibration_engine.get_calibration_data()
            elif self.degradation_context.get("use_default_calibration"):
                return self._get_default_calibration()
            else:
                return self.calibration_engine.get_calibration_data()
    
    def _perform_tracking(self, detections: List[Detection], frame_number: int) -> List[TrackedBall]:
        """Perform ball tracking"""
        # Check for graceful degradation
        if self.degradation_context.get("tracking_degraded"):
            if self.degradation_context.get("detection_only_mode"):
                return self._convert_detections_to_tracks(detections, frame_number)
        
        try:
            tracked_balls = self.tracker.update(detections, frame_number)
            
            if self.debug_mode:
                active_tracks = len([t for t in tracked_balls if t.is_active])
                logger.debug(f"Tracking: {active_tracks} active tracks")
            
            return tracked_balls
            
        except Exception as e:
            self.processing_stats['tracking_failures'] += 1
            
            # Handle error with recovery
            context = {
                "detections": detections,
                "frame_number": frame_number,
                "degradation_context": self.degradation_context
            }
            
            recovery_successful = self.error_handler.handle_error(
                ErrorCategory.TRACKING,
                ErrorSeverity.MEDIUM,
                f"Ball tracking failed: {str(e)}",
                e,
                context
            )
            
            # Update degradation context
            self.degradation_context.update(context.get("degradation_context", {}))
            
            if recovery_successful:
                # Try tracking again after recovery
                try:
                    return self.tracker.update(detections, frame_number)
                except:
                    pass
            
            # Fallback to detection-only mode
            if self.degradation_context.get("detection_only_mode"):
                return self._convert_detections_to_tracks(detections, frame_number)
            
            return []
    
    def _perform_trajectory_analysis(self, tracked_balls: List[TrackedBall]) -> None:
        """Perform trajectory analysis for events"""
        try:
            # Detect potting events
            potting_events = self.trajectory_analyzer.detect_potting_events(tracked_balls)
            if potting_events:
                logger.info(f"Detected {len(potting_events)} potting events")
            
            # Detect collision events
            collision_events = self.trajectory_analyzer.detect_collision_events(tracked_balls)
            if collision_events:
                logger.info(f"Detected {len(collision_events)} collision events")
                
        except Exception as e:
            logger.error(f"Trajectory analysis failed: {e}")
    
    def _update_processing_stats(self, processing_time: float, success: bool) -> None:
        """Update processing performance statistics"""
        self.processing_stats['frames_processed'] += 1
        
        if success:
            self.processing_stats['total_processing_time'] += processing_time
            
            # Calculate running average
            frames = self.processing_stats['frames_processed']
            total_time = self.processing_stats['total_processing_time']
            self.processing_stats['avg_processing_time'] = total_time / frames
    
    def set_debug_mode(self, enabled: bool) -> None:
        """Enable/disable debug mode"""
        self.debug_mode = enabled
        self.config.debug_mode = enabled
        
        if enabled:
            logger.setLevel(logging.DEBUG)
            logger.info("Debug mode enabled")
        else:
            logger.setLevel(logging.INFO)
            logger.info("Debug mode disabled")
    
    def get_processing_stats(self) -> Dict:
        """Get processing performance statistics"""
        stats = self.processing_stats.copy()
        
        # Add component-specific stats
        stats['detection_stats'] = self.detection_engine.get_detection_stats()
        stats['tracking_stats'] = self.tracker.get_tracking_stats()
        stats['validation_stats'] = self.detection_engine.get_validation_stats()
        
        # Calculate success rates
        total_frames = stats['frames_processed']
        if total_frames > 0:
            stats['detection_success_rate'] = 1.0 - (stats['detection_failures'] / total_frames)
            stats['calibration_success_rate'] = 1.0 - (stats['calibration_failures'] / total_frames)
            stats['tracking_success_rate'] = 1.0 - (stats['tracking_failures'] / total_frames)
        else:
            stats['detection_success_rate'] = 0.0
            stats['calibration_success_rate'] = 0.0
            stats['tracking_success_rate'] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset all processing statistics"""
        self.processing_stats = {
            'frames_processed': 0,
            'total_processing_time': 0.0,
            'avg_processing_time': 0.0,
            'detection_failures': 0,
            'calibration_failures': 0,
            'tracking_failures': 0,
            'last_successful_calibration': -1
        }
        
        # Reset component stats
        self.detection_engine.reset_stats()
        self.detection_engine.reset_validation_stats()
        self.tracker.reset_tracking()
        self.trajectory_analyzer.reset_analysis()
        
        logger.info("All processing statistics reset")
    
    def get_current_calibration(self) -> CalibrationData:
        """Get current calibration data"""
        return self.calibration_engine.get_calibration_data()
    
    def reset_calibration(self) -> None:
        """Reset calibration data"""
        self.calibration_engine.reset_calibration()
        self.coordinate_transformer = CoordinateTransformer()
        logger.info("Calibration reset")
    
    def update_detection_threshold(self, threshold: float) -> None:
        """Update detection confidence threshold"""
        self.detection_engine.set_confidence_threshold(threshold)
        logger.info(f"Detection threshold updated to {threshold}")
    
    def get_trajectory_summary(self) -> Dict:
        """Get trajectory analysis summary"""
        tracked_balls = self.tracker.get_active_tracks()
        return self.trajectory_analyzer.get_trajectory_summary(tracked_balls)
    
    def visualize_frame_analysis(self, frame: np.ndarray, analysis: FrameAnalysis) -> np.ndarray:
        """Create visualization of frame analysis results"""
        import cv2
        
        vis_frame = frame.copy()
        
        # Draw detections
        if analysis.detections:
            vis_frame = self.detection_engine.visualize_detections(vis_frame, analysis.detections)
        
        # Draw calibration
        if analysis.calibration_data and analysis.calibration_data.is_calibrated():
            vis_frame = self.calibration_engine.visualize_calibration(vis_frame)
        
        # Draw tracking
        if analysis.tracked_balls:
            vis_frame = self.tracker.visualize_tracks(vis_frame)
        
        # Draw processing info
        info_text = [
            f"Frame: {analysis.frame_number}",
            f"Processing: {analysis.processing_time:.3f}s",
            f"Detections: {len(analysis.detections)}",
            f"Tracks: {len([t for t in analysis.tracked_balls if t.is_active])}"
        ]
        
        for i, text in enumerate(info_text):
            y_pos = 30 + i * 25
            cv2.putText(vis_frame, text, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(vis_frame, text, (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        return vis_frame
    
    def is_ready_for_processing(self) -> bool:
        """Check if processor is ready for frame processing"""
        return (self.components_initialized and 
                self.detection_engine.is_model_loaded())
    
    def get_component_status(self) -> Dict[str, bool]:
        """Get status of all components"""
        return {
            'detection_engine': self.detection_engine.is_model_loaded(),
            'calibration_engine': True,  # Always available
            'tracker': True,  # Always available
            'coordinate_transformer': self.coordinate_transformer.is_transformation_available(),
            'trajectory_analyzer': True,  # Always available
            'overall_ready': self.is_ready_for_processing()
        }
    
    def _get_default_calibration(self) -> CalibrationData:
        """Get default calibration data for graceful degradation"""
        from ..core import CalibrationData, Point, BoundingBox
        import numpy as np
        
        # Create basic identity-like calibration
        default_corners = [
            Point(100, 100), Point(700, 100),
            Point(700, 400), Point(100, 400)
        ]
        
        identity_homography = np.eye(3, dtype=np.float32)
        
        default_pockets = [
            BoundingBox(90, 90, 110, 110),
            BoundingBox(690, 90, 710, 110),
            BoundingBox(90, 390, 110, 410),
            BoundingBox(690, 390, 710, 410)
        ]
        
        return CalibrationData(
            homography_matrix=identity_homography,
            table_corners=default_corners,
            table_dimensions=(3.569, 1.778),
            pocket_regions=default_pockets,
            calibration_timestamp=time.time(),
            is_valid=False  # Mark as invalid since it's a fallback
        )
    
    def _convert_detections_to_tracks(self, detections: List[Detection], frame_number: int) -> List[TrackedBall]:
        """Convert detections to simple tracks for detection-only mode"""
        from ..core import TrackedBall, BallType
        
        tracks = []
        for i, detection in enumerate(detections):
            track = TrackedBall(
                track_id=i,
                ball_type=BallType(detection.class_id),
                current_position=detection.get_centroid(),
                trajectory=[detection.get_centroid()],
                confidence_history=[detection.confidence],
                last_seen_frame=frame_number,
                is_active=True
            )
            tracks.append(track)
        
        return tracks
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        return self.error_handler.get_error_statistics()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        stats = self.error_handler.get_error_statistics()
        return {
            "system_health": stats["system_health"],
            "degraded_components": self.error_handler.get_degraded_components(),
            "degradation_context": self.degradation_context,
            "is_healthy": self.error_handler.is_system_healthy()
        }
    
    def reset_error_handling(self) -> None:
        """Reset error handling and recovery state"""
        self.error_handler.reset_error_statistics()
        self.degradation_context.clear()
        logger.info("Error handling state reset")