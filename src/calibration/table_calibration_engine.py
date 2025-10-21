#!/usr/bin/env python3
"""
Table Calibration Engine for snooker table geometry detection
"""

import logging
import time
from typing import List, Optional, Tuple
import numpy as np
import cv2

from ..core import ICalibrationEngine, CalibrationData, Point, BoundingBox, CalibrationConfig
from .calibration_persistence import CalibrationPersistenceManager, CalibrationRecoveryManager

logger = logging.getLogger(__name__)

class TableCalibrationEngine(ICalibrationEngine):
    """Detects snooker table geometry and calculates calibration data"""
    
    def __init__(self, config: CalibrationConfig, cache_directory: str = "cache/calibration"):
        self.config = config
        self.calibration_data = CalibrationData()
        self.last_calibration_frame = -1
        self.calibration_attempts = 0
        
        # Initialize persistence and recovery managers
        self.persistence_manager = CalibrationPersistenceManager(cache_directory)
        self.recovery_manager = CalibrationRecoveryManager(self.persistence_manager)
        
        # Try to load existing calibration data
        self._load_cached_calibration()
        
        # Standard snooker table pocket positions (normalized coordinates)
        self.standard_pocket_positions = [
            (0.0, 0.0),    # Top-left
            (0.5, 0.0),    # Top-middle  
            (1.0, 0.0),    # Top-right
            (0.0, 1.0),    # Bottom-left
            (0.5, 1.0),    # Bottom-middle
            (1.0, 1.0)     # Bottom-right
        ]
        
        # Camera angle change detection
        self.previous_corners = None
        self.corner_change_threshold = 50.0  # pixels
    
    def detect_table_corners(self, frame: np.ndarray) -> List[Point]:
        """Detect table corner points using edge and line detection"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Edge detection
            edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
            
            # Morphological operations to clean up edges
            kernel = np.ones((3, 3), np.uint8)
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is None or len(lines) < 4:
                logger.warning("Insufficient lines detected for table corner detection")
                return []
            
            # Filter and group lines
            horizontal_lines, vertical_lines = self._filter_lines(lines)
            
            if len(horizontal_lines) < 2 or len(vertical_lines) < 2:
                logger.warning("Insufficient horizontal or vertical lines detected")
                return []
            
            # Find intersections to get corner points
            corners = self._find_line_intersections(horizontal_lines, vertical_lines)
            
            # Validate and order corners
            if len(corners) >= 4:
                ordered_corners = self._order_corners(corners)
                return ordered_corners[:4]  # Return top 4 corners
            
            return []
            
        except Exception as e:
            logger.error(f"Corner detection failed: {e}")
            return []
    
    def _filter_lines(self, lines: np.ndarray) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
        """Filter and categorize lines into horizontal and vertical"""
        horizontal_lines = []
        vertical_lines = []
        
        for line in lines:
            rho, theta = line[0]
            
            # Convert to degrees
            angle_deg = np.degrees(theta)
            
            # Classify as horizontal or vertical based on angle
            if abs(angle_deg) < 20 or abs(angle_deg - 180) < 20:
                horizontal_lines.append((rho, theta))
            elif abs(angle_deg - 90) < 20:
                vertical_lines.append((rho, theta))
        
        # Remove duplicate lines (similar rho values)
        horizontal_lines = self._remove_duplicate_lines(horizontal_lines)
        vertical_lines = self._remove_duplicate_lines(vertical_lines)
        
        return horizontal_lines, vertical_lines
    
    def _remove_duplicate_lines(self, lines: List[Tuple[float, float]], threshold: float = 30) -> List[Tuple[float, float]]:
        """Remove lines that are too close to each other"""
        if not lines:
            return []
        
        # Sort by rho value
        lines.sort(key=lambda x: abs(x[0]))
        
        filtered_lines = [lines[0]]
        
        for rho, theta in lines[1:]:
            # Check if this line is too close to any existing line
            is_duplicate = False
            for existing_rho, existing_theta in filtered_lines:
                if abs(rho - existing_rho) < threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_lines.append((rho, theta))
        
        return filtered_lines
    
    def _find_line_intersections(self, horizontal_lines: List[Tuple[float, float]], 
                                vertical_lines: List[Tuple[float, float]]) -> List[Point]:
        """Find intersection points between horizontal and vertical lines"""
        intersections = []
        
        for h_rho, h_theta in horizontal_lines:
            for v_rho, v_theta in vertical_lines:
                intersection = self._line_intersection(h_rho, h_theta, v_rho, v_theta)
                if intersection:
                    intersections.append(intersection)
        
        return intersections
    
    def _line_intersection(self, rho1: float, theta1: float, rho2: float, theta2: float) -> Optional[Point]:
        """Calculate intersection point of two lines in polar form"""
        try:
            # Convert polar to cartesian form
            cos_theta1, sin_theta1 = np.cos(theta1), np.sin(theta1)
            cos_theta2, sin_theta2 = np.cos(theta2), np.sin(theta2)
            
            # Solve system of equations
            det = cos_theta1 * sin_theta2 - sin_theta1 * cos_theta2
            
            if abs(det) < 1e-6:  # Lines are parallel
                return None
            
            x = (sin_theta2 * rho1 - sin_theta1 * rho2) / det
            y = (cos_theta1 * rho2 - cos_theta2 * rho1) / det
            
            return Point(x, y)
            
        except Exception:
            return None
    
    def _order_corners(self, corners: List[Point]) -> List[Point]:
        """Order corners in clockwise order starting from top-left"""
        if len(corners) < 4:
            return corners
        
        # Convert to numpy array for easier manipulation
        points = np.array([(p.x, p.y) for p in corners])
        
        # Find centroid
        centroid = np.mean(points, axis=0)
        
        # Calculate angles from centroid
        angles = np.arctan2(points[:, 1] - centroid[1], points[:, 0] - centroid[0])
        
        # Sort by angle
        sorted_indices = np.argsort(angles)
        
        # Order: top-left, top-right, bottom-right, bottom-left
        ordered_points = points[sorted_indices]
        
        return [Point(x, y) for x, y in ordered_points]
    
    def calculate_homography(self, corners: List[Point]) -> Optional[np.ndarray]:
        """Calculate homography transformation matrix from detected corners"""
        if len(corners) != 4:
            logger.warning(f"Need exactly 4 corners for homography, got {len(corners)}")
            return None
        
        try:
            # Source points (detected corners)
            src_points = np.array([[p.x, p.y] for p in corners], dtype=np.float32)
            
            # Destination points (standard rectangle)
            # Assuming table dimensions in meters, scale to reasonable pixel size
            table_width_px = 800
            table_height_px = int(table_width_px * self.config.table_width / self.config.table_length)
            
            dst_points = np.array([
                [0, 0],
                [table_width_px, 0],
                [table_width_px, table_height_px],
                [0, table_height_px]
            ], dtype=np.float32)
            
            # Calculate homography
            homography_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            
            # Validate homography
            if self._validate_homography(homography_matrix, src_points, dst_points):
                return homography_matrix
            else:
                logger.warning("Homography validation failed")
                return None
                
        except Exception as e:
            logger.error(f"Homography calculation failed: {e}")
            return None
    
    def _validate_homography(self, homography: np.ndarray, src_points: np.ndarray, 
                           dst_points: np.ndarray, max_error: float = 10.0) -> bool:
        """Validate homography by checking reprojection error"""
        try:
            # Transform source points using homography
            transformed_points = cv2.perspectiveTransform(
                src_points.reshape(-1, 1, 2), homography
            ).reshape(-1, 2)
            
            # Calculate reprojection error
            errors = np.linalg.norm(transformed_points - dst_points, axis=1)
            mean_error = np.mean(errors)
            
            logger.debug(f"Homography reprojection error: {mean_error:.2f}")
            
            return mean_error < max_error
            
        except Exception as e:
            logger.error(f"Homography validation failed: {e}")
            return False
    
    def is_calibrated(self) -> bool:
        """Check if calibration is valid"""
        return self.calibration_data.is_calibrated()
    
    def get_calibration_data(self) -> CalibrationData:
        """Get current calibration data"""
        return self.calibration_data
    
    def reset_calibration(self) -> None:
        """Reset calibration data"""
        self.calibration_data = CalibrationData()
        self.last_calibration_frame = -1
        self.calibration_attempts = 0
        logger.info("Calibration data reset")
    
    def calibrate_frame(self, frame: np.ndarray, frame_number: int = 0, 
                       video_source: str = "") -> bool:
        """Perform calibration on a single frame"""
        # Check if we need to recalibrate
        if (self.is_calibrated() and 
            not self.config.auto_recalibrate and
            frame_number - self.last_calibration_frame < self.config.calibration_interval):
            return True
        
        # Check for camera angle changes if we have previous calibration
        if self.is_calibrated() and self._detect_camera_angle_change(frame):
            logger.info("Camera angle change detected, forcing recalibration")
            self.reset_calibration()
        
        self.calibration_attempts += 1
        
        # Detect table corners
        corners = self.detect_table_corners(frame)
        
        if len(corners) < 4:
            logger.debug(f"Calibration attempt {self.calibration_attempts}: insufficient corners detected")
            # Try recovery if this is a critical failure
            if self.calibration_attempts > 5 and not self.is_calibrated():
                return self._attempt_calibration_recovery(video_source)
            return False
        
        # Calculate homography
        homography = self.calculate_homography(corners)
        
        if homography is None:
            logger.debug(f"Calibration attempt {self.calibration_attempts}: homography calculation failed")
            # Try recovery if this is a critical failure
            if self.calibration_attempts > 5 and not self.is_calibrated():
                return self._attempt_calibration_recovery(video_source)
            return False
        
        # Generate pocket regions
        pocket_regions = self._generate_pocket_regions(corners, frame.shape)
        
        # Update calibration data
        self.calibration_data = CalibrationData(
            homography_matrix=homography,
            table_corners=corners,
            table_dimensions=(self.config.table_length, self.config.table_width),
            pocket_regions=pocket_regions,
            calibration_timestamp=time.time(),
            is_valid=True
        )
        
        self.last_calibration_frame = frame_number
        self.previous_corners = corners.copy()
        
        # Save calibration data for future use
        self.persistence_manager.save_calibration_data(
            self.calibration_data, video_source, frame_number
        )
        
        logger.info(f"Table calibration successful on attempt {self.calibration_attempts}")
        return True
    
    def _generate_pocket_regions(self, corners: List[Point], frame_shape: tuple) -> List[BoundingBox]:
        """Generate pocket regions based on table corners"""
        if len(corners) != 4:
            return []
        
        pocket_regions = []
        
        # Calculate pocket positions based on table corners
        # This is a simplified approach - in practice, you might want more sophisticated pocket detection
        
        # Get table boundaries
        min_x = min(p.x for p in corners)
        max_x = max(p.x for p in corners)
        min_y = min(p.y for p in corners)
        max_y = max(p.y for p in corners)
        
        table_width = max_x - min_x
        table_height = max_y - min_y
        
        # Pocket size (as fraction of table dimensions)
        pocket_size_x = table_width * 0.05  # 5% of table width
        pocket_size_y = table_height * 0.08  # 8% of table height
        
        # Define pocket positions (6 pockets)
        pocket_positions = [
            (min_x, min_y),  # Top-left
            (min_x + table_width/2, min_y),  # Top-middle
            (max_x, min_y),  # Top-right
            (min_x, max_y),  # Bottom-left
            (min_x + table_width/2, max_y),  # Bottom-middle
            (max_x, max_y)   # Bottom-right
        ]
        
        for px, py in pocket_positions:
            x1 = max(0, int(px - pocket_size_x/2))
            y1 = max(0, int(py - pocket_size_y/2))
            x2 = min(frame_shape[1], int(px + pocket_size_x/2))
            y2 = min(frame_shape[0], int(py + pocket_size_y/2))
            
            pocket_regions.append(BoundingBox(x1, y1, x2, y2))
        
        return pocket_regions
    
    def visualize_calibration(self, frame: np.ndarray) -> np.ndarray:
        """Draw calibration visualization on frame"""
        vis_frame = frame.copy()
        
        if not self.is_calibrated():
            # Draw "Not Calibrated" message
            cv2.putText(vis_frame, "Table Not Calibrated", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return vis_frame
        
        # Draw table corners
        corners = self.calibration_data.table_corners
        if corners:
            for i, corner in enumerate(corners):
                cv2.circle(vis_frame, (int(corner.x), int(corner.y)), 8, (0, 255, 0), -1)
                cv2.putText(vis_frame, f"C{i+1}", (int(corner.x)+10, int(corner.y)-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Draw table boundary
            corner_points = np.array([[int(c.x), int(c.y)] for c in corners], np.int32)
            cv2.polylines(vis_frame, [corner_points], True, (0, 255, 0), 2)
        
        # Draw pocket regions
        for i, pocket in enumerate(self.calibration_data.pocket_regions):
            cv2.rectangle(vis_frame, (pocket.x1, pocket.y1), (pocket.x2, pocket.y2), (255, 0, 0), 2)
            cv2.putText(vis_frame, f"P{i+1}", (pocket.x1, pocket.y1-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
        
        # Draw calibration info
        cv2.putText(vis_frame, "Table Calibrated", (50, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return vis_frame
    
    def _load_cached_calibration(self) -> bool:
        """Load calibration data from cache if available"""
        try:
            cached_data = self.persistence_manager.load_calibration_data()
            if cached_data and cached_data.is_calibrated():
                self.calibration_data = cached_data
                logger.info("Loaded cached calibration data")
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to load cached calibration: {e}")
            return False
    
    def _detect_camera_angle_change(self, frame: np.ndarray) -> bool:
        """Detect if camera angle has changed significantly"""
        if not self.previous_corners or len(self.previous_corners) != 4:
            return False
        
        try:
            # Detect current corners
            current_corners = self.detect_table_corners(frame)
            if len(current_corners) != 4:
                return False
            
            # Calculate average displacement
            total_displacement = 0.0
            for prev_corner, curr_corner in zip(self.previous_corners, current_corners):
                displacement = prev_corner.distance_to(curr_corner)
                total_displacement += displacement
            
            avg_displacement = total_displacement / 4
            
            if avg_displacement > self.corner_change_threshold:
                logger.info(f"Camera angle change detected: avg displacement {avg_displacement:.1f}px")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error detecting camera angle change: {e}")
            return False
    
    def _attempt_calibration_recovery(self, video_source: str = "") -> bool:
        """Attempt to recover calibration using various strategies"""
        try:
            logger.info("Attempting calibration recovery...")
            
            recovered_data = self.recovery_manager.recover_calibration(video_source)
            if recovered_data:
                self.calibration_data = recovered_data
                logger.info("Calibration recovery successful")
                return True
            
            logger.warning("Calibration recovery failed")
            return False
            
        except Exception as e:
            logger.error(f"Calibration recovery error: {e}")
            return False
    
    def force_recalibration(self) -> None:
        """Force recalibration on next frame"""
        self.reset_calibration()
        self.last_calibration_frame = -1
        logger.info("Forced recalibration requested")
    
    def get_calibration_status(self) -> dict:
        """Get detailed calibration status information"""
        cache_metadata = self.persistence_manager.get_cache_metadata()
        
        return {
            "is_calibrated": self.is_calibrated(),
            "calibration_attempts": self.calibration_attempts,
            "last_calibration_frame": self.last_calibration_frame,
            "calibration_timestamp": self.calibration_data.calibration_timestamp if self.calibration_data else None,
            "table_corners_count": len(self.calibration_data.table_corners) if self.calibration_data else 0,
            "pocket_regions_count": len(self.calibration_data.pocket_regions) if self.calibration_data else 0,
            "cache_metadata": cache_metadata,
            "auto_recalibrate": self.config.auto_recalibrate,
            "calibration_interval": self.config.calibration_interval
        }
    
    def clear_calibration_cache(self) -> bool:
        """Clear all cached calibration data"""
        return self.persistence_manager.clear_cache()