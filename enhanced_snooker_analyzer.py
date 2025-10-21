#!/usr/bin/env python3
"""
Enhanced Snooker Video Analytics - Integration with new detection system
Maintains backward compatibility while using the new modular architecture
"""

import cv2
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import time
import logging

# Import the new detection system
from src import (
    DetectionAPI, SystemConfig, DetectionConfig, TrackingConfig, CalibrationConfig,
    create_default_config, BallType, get_ball_name, get_ball_color
)

# Import original configuration for compatibility
from config import (
    BASE_DIR, DATASET_DIR, MODEL_PATH, VIDEO_PATH, 
    BALL_CLASSES, POCKETS, CONFIDENCE_THRESHOLD
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedSnookerAnalyzer:
    """Enhanced analyzer using the new detection system with backward compatibility"""
    
    def __init__(self, debug_mode: bool = False):
        # Create configuration using existing settings
        self.config = self._create_config_from_legacy()
        self.config.debug_mode = debug_mode
        
        # Initialize the new detection system
        self.detection_api = DetectionAPI(self.config)
        
        # Legacy compatibility - store analysis results
        self.movement_data = {cls_id: [] for cls_id in BALL_CLASSES}
        self.detections_per_class = {cls_id: 0 for cls_id in BALL_CLASSES}
        self.potted_balls = {}
        self.analysis_results = []
        
        # Performance tracking
        self.start_time = None
        self.total_frames = 0
        
    def _create_config_from_legacy(self) -> SystemConfig:
        """Create new system config from legacy configuration"""
        return SystemConfig(
            detection=DetectionConfig(
                model_path=MODEL_PATH,
                confidence_threshold=CONFIDENCE_THRESHOLD,
                device="cpu"
            ),
            tracking=TrackingConfig(
                max_disappeared_frames=10,
                max_tracking_distance=50.0,
                kalman_process_noise=0.1,
                kalman_measurement_noise=0.1
            ),
            calibration=CalibrationConfig(
                auto_recalibrate=True,
                calibration_interval=100
            ),
            debug_mode=False,
            output_directory=DATASET_DIR
        )
    
    def initialize(self) -> bool:
        """Initialize the detection system"""
        logger.info("🎱 Enhanced Snooker Video Analytics")
        logger.info("=" * 50)
        
        if not self.detection_api.initialize():
            logger.error("Failed to initialize detection system")
            return False
        
        # Set up callbacks for real-time analysis
        self.detection_api.add_frame_callback(self._on_frame_analyzed)
        self.detection_api.add_event_callback(self._on_event_detected)
        
        logger.info("✅ Enhanced analyzer initialized successfully")
        return True
    
    def analyze_video(self, video_path: str = None) -> bool:
        """Analyze snooker video using the new detection system"""
        if video_path is None:
            video_path = VIDEO_PATH
            
        if not os.path.exists(video_path):
            logger.error(f"❌ Video file not found: {video_path}")
            return False
        
        logger.info(f"🎥 Starting analysis: {video_path}")
        self.start_time = time.time()
        
        # Start analysis
        if not self.detection_api.start_analysis(video_path):
            logger.error("Failed to start video analysis")
            return False
        
        try:
            # Wait for analysis to complete (for video files)
            while self.detection_api.is_analyzing():
                time.sleep(0.1)
                
                # Print progress for video files
                status = self.detection_api.get_system_status()
                video_props = status['video_source']
                
                if video_props['source_type'] == 'file' and video_props['total_frames'] > 0:
                    progress = video_props['progress_percent']
                    if progress >= 0:
                        print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            
            print()  # New line after progress
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ Analysis interrupted by user")
            self.detection_api.stop_analysis()
            return False
        
        # Analysis completed
        analysis_time = time.time() - self.start_time
        logger.info(f"✅ Analysis completed in {analysis_time:.2f} seconds")
        
        return True
    
    def _on_frame_analyzed(self, analysis) -> None:
        """Callback for each analyzed frame"""
        self.total_frames += 1
        self.analysis_results.append(analysis)
        
        # Convert to legacy format for compatibility
        self._update_legacy_data(analysis)
    
    def _on_event_detected(self, event) -> None:
        """Callback for detected events"""
        logger.info(f"🎯 Event detected: {event}")
    
    def _update_legacy_data(self, analysis) -> None:
        """Update legacy data structures for backward compatibility"""
        frame_number = analysis.frame_number
        
        # Update detection counts
        for detection in analysis.detections:
            ball_type = detection.get_ball_type()
            class_id = ball_type.value
            
            if class_id in self.detections_per_class:
                self.detections_per_class[class_id] += 1
        
        # Update movement data from tracked balls
        for tracked_ball in analysis.tracked_balls:
            if tracked_ball.is_active:
                class_id = tracked_ball.ball_type.value
                pos = tracked_ball.current_position
                
                if class_id in self.movement_data:
                    self.movement_data[class_id].append((frame_number, pos.x, pos.y))
    
    def detect_potting_events(self) -> None:
        """Analyze results to detect potting events (legacy compatibility)"""
        logger.info("🔍 Analyzing potting events...")
        
        # Get trajectory summary from the new system
        if hasattr(self.detection_api.frame_processor, 'trajectory_analyzer'):
            analyzer = self.detection_api.frame_processor.trajectory_analyzer
            
            # Get all tracked balls from analysis history
            all_tracked_balls = []
            for analysis in self.analysis_results:
                all_tracked_balls.extend(analysis.tracked_balls)
            
            # Detect potting events
            potting_events = analyzer.detect_potting_events(all_tracked_balls)
            
            # Convert to legacy format
            for event in potting_events:
                ball_name = event['ball_type']
                if ball_name not in self.potted_balls:
                    self.potted_balls[ball_name] = []
                
                self.potted_balls[ball_name].append({
                    'frame': event['frame'],
                    'position': (event['position'].x, event['position'].y),
                    'pocket': event.get('pocket_id', -1)
                })
    
    def generate_reports(self) -> None:
        """Generate analysis reports (enhanced version)"""
        logger.info("\n📊 Generating Enhanced Analysis Reports")
        logger.info("=" * 50)
        
        # Get system status and statistics
        status = self.detection_api.get_system_status()
        processing_stats = status['processing_stats']
        
        # Print detection statistics
        print("\n📊 Detection Statistics:")
        for cls_id, count in self.detections_per_class.items():
            if cls_id in BALL_CLASSES:
                ball_name = BALL_CLASSES[cls_id][0]
                print(f"  {ball_name}: {count} detections")
        
        # Print performance statistics
        print(f"\n⚡ Performance Statistics:")
        print(f"  Total frames processed: {processing_stats['frames_processed']}")
        print(f"  Average processing time: {processing_stats['avg_processing_time']:.3f}s per frame")
        print(f"  Detection success rate: {processing_stats['detection_success_rate']:.1%}")
        print(f"  Tracking success rate: {processing_stats['tracking_success_rate']:.1%}")
        
        if status['calibration_status']['is_calibrated']:
            print(f"  ✅ Table calibration: Successful")
        else:
            print(f"  ⚠️ Table calibration: Failed")
        
        # Print potting events
        print("\n🏆 Potting Events:")
        if self.potted_balls:
            for ball, events in self.potted_balls.items():
                print(f"  {ball}: {len(events)} pots")
                for event in events[:5]:  # Show first 5 events
                    print(f"    Frame {event['frame']}: Position {event['position']}")
        else:
            print("  No potting events detected")
        
        # Save enhanced analysis data
        self._save_enhanced_data()
        
        # Generate visualizations
        self._generate_enhanced_plots()
    
    def _save_enhanced_data(self) -> None:
        """Save enhanced analysis data"""
        output_file = os.path.join(DATASET_DIR, "enhanced_analysis.txt")
        
        try:
            with open(output_file, "w") as f:
                f.write("Enhanced Snooker Ball Analysis Report\n")
                f.write("=" * 50 + "\n\n")
                
                # System information
                status = self.detection_api.get_system_status()
                f.write("System Configuration:\n")
                f.write(f"  Detection Model: {self.config.detection.model_path}\n")
                f.write(f"  Confidence Threshold: {self.config.detection.confidence_threshold}\n")
                f.write(f"  Tracking Distance: {self.config.tracking.max_tracking_distance}\n")
                f.write("\n")
                
                # Analysis results
                f.write("Analysis Results:\n")
                processing_stats = status['processing_stats']
                f.write(f"  Frames Processed: {processing_stats['frames_processed']}\n")
                f.write(f"  Average Processing Time: {processing_stats['avg_processing_time']:.3f}s\n")
                f.write(f"  Detection Success Rate: {processing_stats['detection_success_rate']:.1%}\n")
                f.write("\n")
                
                # Ball detection summary
                f.write("Ball Detection Summary:\n")
                for cls_id, count in self.detections_per_class.items():
                    if cls_id in BALL_CLASSES and count > 0:
                        ball_name = BALL_CLASSES[cls_id][0]
                        f.write(f"  {ball_name}: {count} detections\n")
                f.write("\n")
            
            logger.info(f"💾 Enhanced analysis saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save enhanced analysis: {e}")
    
    def _generate_enhanced_plots(self) -> None:
        """Generate enhanced visualization plots"""
        if not self.analysis_results:
            logger.warning("⚠️ No analysis data to plot")
            return
        
        try:
            # Create comprehensive visualization
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # Plot 1: Detection confidence over time
            frames = []
            avg_confidences = []
            
            for analysis in self.analysis_results:
                if analysis.detections:
                    frames.append(analysis.frame_number)
                    confidences = [d.confidence for d in analysis.detections]
                    avg_confidences.append(np.mean(confidences))
            
            if frames:
                ax1.plot(frames, avg_confidences, 'b-', alpha=0.7)
                ax1.set_title('Average Detection Confidence Over Time')
                ax1.set_xlabel('Frame Number')
                ax1.set_ylabel('Average Confidence')
                ax1.grid(True)
            
            # Plot 2: Ball count over time
            ball_counts = []
            for analysis in self.analysis_results:
                active_balls = len([b for b in analysis.tracked_balls if b.is_active])
                ball_counts.append(active_balls)
            
            if ball_counts:
                ax2.plot(range(len(ball_counts)), ball_counts, 'g-', alpha=0.7)
                ax2.set_title('Active Ball Count Over Time')
                ax2.set_xlabel('Frame Number')
                ax2.set_ylabel('Number of Active Balls')
                ax2.grid(True)
            
            # Plot 3: Processing time distribution
            processing_times = [a.processing_time for a in self.analysis_results]
            if processing_times:
                ax3.hist(processing_times, bins=30, alpha=0.7, color='orange')
                ax3.set_title('Processing Time Distribution')
                ax3.set_xlabel('Processing Time (seconds)')
                ax3.set_ylabel('Frequency')
                ax3.grid(True)
            
            # Plot 4: Ball trajectories (sample)
            colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'black']
            color_idx = 0
            
            for analysis in self.analysis_results[-100:]:  # Last 100 frames
                for ball in analysis.tracked_balls:
                    if ball.is_active and len(ball.trajectory) > 1:
                        x_coords = [p.x for p in ball.trajectory[-20:]]  # Last 20 points
                        y_coords = [p.y for p in ball.trajectory[-20:]]
                        
                        if len(x_coords) > 1:
                            color = colors[color_idx % len(colors)]
                            ax4.plot(x_coords, y_coords, color=color, alpha=0.6, linewidth=1)
                            color_idx += 1
            
            ax4.set_title('Ball Trajectories (Recent)')
            ax4.set_xlabel('X Coordinate')
            ax4.set_ylabel('Y Coordinate')
            ax4.grid(True)
            ax4.invert_yaxis()  # Invert Y axis to match image coordinates
            
            plt.tight_layout()
            
            # Save plot
            output_file = os.path.join(DATASET_DIR, "enhanced_analysis_plots.png")
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.show()
            
            logger.info(f"📈 Enhanced plots saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced plots: {e}")
    
    def export_analysis_data(self, format: str = 'json') -> bool:
        """Export complete analysis data"""
        output_path = os.path.join(DATASET_DIR, f"complete_analysis.{format}")
        return self.detection_api.export_analysis_data(output_path, format)
    
    def get_system_status(self) -> dict:
        """Get comprehensive system status"""
        return self.detection_api.get_system_status()
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self.detection_api.is_analyzing():
            self.detection_api.stop_analysis()

def main():
    """Main analysis function with enhanced capabilities"""
    try:
        # Initialize enhanced analyzer
        analyzer = EnhancedSnookerAnalyzer(debug_mode=True)
        
        if not analyzer.initialize():
            logger.error("Failed to initialize analyzer")
            return
        
        # Analyze video
        if analyzer.analyze_video():
            # Detect potting events
            analyzer.detect_potting_events()
            
            # Generate comprehensive reports
            analyzer.generate_reports()
            
            # Export data
            analyzer.export_analysis_data('json')
            
            logger.info("\n✅ Enhanced analysis complete!")
        else:
            logger.error("Analysis failed")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Analysis interrupted by user")
    except Exception as e:
        logger.error(f"Analysis error: {e}")
    finally:
        if 'analyzer' in locals():
            analyzer.cleanup()

if __name__ == "__main__":
    main()