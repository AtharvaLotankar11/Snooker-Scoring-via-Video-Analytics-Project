#!/usr/bin/env python3
"""
Debug visualization for snooker detection system
"""

import logging
import time
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import cv2

from ..core import (
    Detection, TrackedBall, CalibrationData, FrameAnalysis, 
    BallType, get_ball_color, get_ball_name, ErrorEvent
)

logger = logging.getLogger(__name__)

class DebugVisualizer:
    """Comprehensive debug visualization for the detection system"""
    
    def __init__(self, enable_overlay: bool = True, save_frames: bool = False, 
                 output_directory: str = "debug_output"):
        self.enable_overlay = enable_overlay
        self.save_frames = save_frames
        self.output_directory = output_directory
        
        # Visualization settings
        self.colors = {
            'detection_box': (0, 255, 0),      # Green
            'tracking_box': (255, 0, 0),       # Blue  
            'trajectory': (0, 255, 255),       # Yellow
            'calibration': (255, 255, 0),      # Cyan
            'pocket': (255, 0, 255),           # Magenta
            'text': (255, 255, 255),           # White
            'background': (0, 0, 0),           # Black
            'error': (0, 0, 255),              # Red
            'warning': (0, 165, 255)           # Orange
        }
        
        # Font settings
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 1
        
        # Frame counter for saving
        self.frame_counter = 0
        
        # Create output directory if saving frames
        if self.save_frames:
            import os
            os.makedirs(self.output_directory, exist_ok=True)
    
    def visualize_frame_analysis(self, frame: np.ndarray, 
                               analysis: FrameAnalysis,
                               show_detections: bool = True,
                               show_tracking: bool = True,
                               show_calibration: bool = True,
                               show_info: bool = True) -> np.ndarray:
        """Create comprehensive visualization of frame analysis"""
        if not self.enable_overlay:
            return frame
        
        vis_frame = frame.copy()
        
        # Draw calibration visualization
        if show_calibration and analysis.calibration_data:
            vis_frame = self._draw_calibration(vis_frame, analysis.calibration_data)
        
        # Draw detections
        if show_detections and analysis.detections:
            vis_frame = self._draw_detections(vis_frame, analysis.detections)
        
        # Draw tracking
        if show_tracking and analysis.tracked_balls:
            vis_frame = self._draw_tracking(vis_frame, analysis.tracked_balls)
        
        # Draw frame information
        if show_info:
            vis_frame = self._draw_frame_info(vis_frame, analysis)
        
        # Save frame if enabled
        if self.save_frames:
            self._save_debug_frame(vis_frame, analysis.frame_number)
        
        return vis_frame
    
    def _draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Draw detection bounding boxes and labels"""
        for detection in detections:
            bbox = detection.bbox
            ball_type = BallType(detection.class_id)
            ball_color = get_ball_color(ball_type)
            ball_name = get_ball_name(ball_type)
            
            # Draw bounding box
            cv2.rectangle(frame, (bbox.x1, bbox.y1), (bbox.x2, bbox.y2), 
                         ball_color, 2)
            
            # Draw confidence and label
            label = f"{ball_name}: {detection.confidence:.2f}"
            label_size = cv2.getTextSize(label, self.font, self.font_scale, self.font_thickness)[0]
            
            # Background for text
            cv2.rectangle(frame, 
                         (bbox.x1, bbox.y1 - label_size[1] - 10),
                         (bbox.x1 + label_size[0], bbox.y1),
                         ball_color, -1)
            
            # Text
            cv2.putText(frame, label, (bbox.x1, bbox.y1 - 5),
                       self.font, self.font_scale, self.colors['text'], self.font_thickness)
            
            # Draw center point
            center = detection.get_centroid()
            cv2.circle(frame, (int(center.x), int(center.y)), 3, ball_color, -1)
        
        return frame
    
    def _draw_tracking(self, frame: np.ndarray, tracked_balls: List[TrackedBall]) -> np.ndarray:
        """Draw tracking information and trajectories"""
        for ball in tracked_balls:
            if not ball.is_active:
                continue
            
            ball_color = get_ball_color(ball.ball_type)
            
            # Draw current position
            pos = ball.current_position
            cv2.circle(frame, (int(pos.x), int(pos.y)), 8, ball_color, 2)
            
            # Draw track ID
            track_label = f"ID:{ball.track_id}"
            cv2.putText(frame, track_label, 
                       (int(pos.x) + 10, int(pos.y) - 10),
                       self.font, self.font_scale, ball_color, self.font_thickness)
            
            # Draw trajectory
            if len(ball.trajectory) > 1:
                trajectory_points = [(int(p.x), int(p.y)) for p in ball.trajectory[-20:]]  # Last 20 points
                
                for i in range(1, len(trajectory_points)):
                    # Fade trajectory (older points are more transparent)
                    alpha = i / len(trajectory_points)
                    color = tuple(int(c * alpha) for c in ball_color)
                    
                    cv2.line(frame, trajectory_points[i-1], trajectory_points[i], 
                            color, 2)
            
            # Draw velocity vector if available
            if ball.velocity:
                vel_end = (int(pos.x + ball.velocity.x * 10), 
                          int(pos.y + ball.velocity.y * 10))
                cv2.arrowedLine(frame, (int(pos.x), int(pos.y)), vel_end,
                               self.colors['trajectory'], 2)
        
        return frame
    
    def _draw_calibration(self, frame: np.ndarray, calibration_data: CalibrationData) -> np.ndarray:
        """Draw calibration visualization"""
        if not calibration_data.is_calibrated():
            # Draw "Not Calibrated" message
            cv2.putText(frame, "TABLE NOT CALIBRATED", (50, 50),
                       self.font, 1.0, self.colors['error'], 2)
            return frame
        
        # Draw table corners
        corners = calibration_data.table_corners
        if corners and len(corners) >= 4:
            # Draw corner points
            for i, corner in enumerate(corners):
                cv2.circle(frame, (int(corner.x), int(corner.y)), 8, 
                          self.colors['calibration'], -1)
                cv2.putText(frame, f"C{i+1}", 
                           (int(corner.x) + 10, int(corner.y) - 10),
                           self.font, self.font_scale, self.colors['calibration'], 
                           self.font_thickness)
            
            # Draw table boundary
            corner_points = np.array([[int(c.x), int(c.y)] for c in corners], np.int32)
            cv2.polylines(frame, [corner_points], True, self.colors['calibration'], 2)
        
        # Draw pocket regions
        for i, pocket in enumerate(calibration_data.pocket_regions):
            cv2.rectangle(frame, (pocket.x1, pocket.y1), (pocket.x2, pocket.y2), 
                         self.colors['pocket'], 2)
            cv2.putText(frame, f"P{i+1}", (pocket.x1, pocket.y1 - 5),
                       self.font, 0.4, self.colors['pocket'], 1)
        
        # Draw calibration status
        cv2.putText(frame, "TABLE CALIBRATED", (50, 50),
                   self.font, 1.0, self.colors['calibration'], 2)
        
        return frame    

    def _draw_frame_info(self, frame: np.ndarray, analysis: FrameAnalysis) -> np.ndarray:
        """Draw frame information overlay"""
        info_lines = [
            f"Frame: {analysis.frame_number}",
            f"Processing: {analysis.processing_time:.3f}s",
            f"Detections: {len(analysis.detections)}",
            f"Active Tracks: {len([t for t in analysis.tracked_balls if t.is_active])}"
        ]
        
        # Add calibration status
        if analysis.calibration_data:
            status = "OK" if analysis.calibration_data.is_calibrated() else "FAILED"
            info_lines.append(f"Calibration: {status}")
        
        # Draw info panel background
        panel_height = len(info_lines) * 25 + 20
        cv2.rectangle(frame, (10, 10), (300, panel_height), 
                     self.colors['background'], -1)
        cv2.rectangle(frame, (10, 10), (300, panel_height), 
                     self.colors['text'], 1)
        
        # Draw info text
        for i, line in enumerate(info_lines):
            y_pos = 30 + i * 25
            cv2.putText(frame, line, (20, y_pos), 
                       self.font, self.font_scale, self.colors['text'], 
                       self.font_thickness)
        
        return frame
    
    def _save_debug_frame(self, frame: np.ndarray, frame_number: int) -> None:
        """Save debug frame to disk"""
        try:
            filename = f"debug_frame_{frame_number:06d}.jpg"
            filepath = f"{self.output_directory}/{filename}"
            cv2.imwrite(filepath, frame)
            
            if frame_number % 100 == 0:  # Log every 100th frame
                logger.debug(f"Saved debug frame: {filepath}")
                
        except Exception as e:
            logger.error(f"Failed to save debug frame: {e}")
    
    def visualize_error_overlay(self, frame: np.ndarray, 
                              error_events: List[ErrorEvent]) -> np.ndarray:
        """Draw error information overlay"""
        if not error_events:
            return frame
        
        vis_frame = frame.copy()
        
        # Draw error panel
        panel_width = 400
        panel_height = min(len(error_events) * 30 + 40, frame.shape[0] - 20)
        
        # Background
        cv2.rectangle(vis_frame, 
                     (frame.shape[1] - panel_width - 10, 10),
                     (frame.shape[1] - 10, panel_height),
                     self.colors['background'], -1)
        
        # Border
        cv2.rectangle(vis_frame, 
                     (frame.shape[1] - panel_width - 10, 10),
                     (frame.shape[1] - 10, panel_height),
                     self.colors['error'], 2)
        
        # Title
        cv2.putText(vis_frame, "RECENT ERRORS", 
                   (frame.shape[1] - panel_width, 35),
                   self.font, 0.7, self.colors['error'], 2)
        
        # Error list
        for i, error in enumerate(error_events[:10]):  # Show max 10 errors
            y_pos = 60 + i * 25
            
            # Error severity color
            if error.severity.value == "critical":
                color = self.colors['error']
            elif error.severity.value == "high":
                color = self.colors['warning']
            else:
                color = self.colors['text']
            
            # Error text
            error_text = f"{error.category.value}: {error.message[:30]}..."
            cv2.putText(vis_frame, error_text,
                       (frame.shape[1] - panel_width + 10, y_pos),
                       self.font, 0.4, color, 1)
        
        return vis_frame
    
    def create_detection_heatmap(self, detections_history: List[List[Detection]], 
                               frame_shape: Tuple[int, int]) -> np.ndarray:
        """Create heatmap of detection locations"""
        heatmap = np.zeros(frame_shape[:2], dtype=np.float32)
        
        for detections in detections_history:
            for detection in detections:
                center = detection.get_centroid()
                x, y = int(center.x), int(center.y)
                
                if 0 <= x < frame_shape[1] and 0 <= y < frame_shape[0]:
                    # Add gaussian blob around detection
                    cv2.circle(heatmap, (x, y), 20, 1.0, -1)
        
        # Normalize and convert to color
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        heatmap_colored = cv2.applyColorMap(
            (heatmap * 255).astype(np.uint8), cv2.COLORMAP_JET
        )
        
        return heatmap_colored
    
    def create_trajectory_plot(self, tracked_balls: List[TrackedBall], 
                             frame_shape: Tuple[int, int]) -> np.ndarray:
        """Create trajectory visualization plot"""
        plot = np.zeros((*frame_shape[:2], 3), dtype=np.uint8)
        
        for ball in tracked_balls:
            if len(ball.trajectory) < 2:
                continue
            
            ball_color = get_ball_color(ball.ball_type)
            
            # Draw trajectory
            points = [(int(p.x), int(p.y)) for p in ball.trajectory]
            
            for i in range(1, len(points)):
                cv2.line(plot, points[i-1], points[i], ball_color, 2)
            
            # Draw start and end points
            if points:
                cv2.circle(plot, points[0], 5, (0, 255, 0), -1)  # Start (green)
                cv2.circle(plot, points[-1], 5, (0, 0, 255), -1)  # End (red)
        
        return plot
    
    def set_visualization_options(self, enable_overlay: bool = None,
                                save_frames: bool = None) -> None:
        """Update visualization options"""
        if enable_overlay is not None:
            self.enable_overlay = enable_overlay
        if save_frames is not None:
            self.save_frames = save_frames
            
            # Create output directory if needed
            if self.save_frames:
                import os
                os.makedirs(self.output_directory, exist_ok=True)
    
    def get_visualization_stats(self) -> Dict[str, Any]:
        """Get visualization statistics"""
        return {
            "frames_processed": self.frame_counter,
            "overlay_enabled": self.enable_overlay,
            "saving_frames": self.save_frames,
            "output_directory": self.output_directory
        }