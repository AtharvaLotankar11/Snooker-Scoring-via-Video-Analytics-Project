#!/usr/bin/env python3
"""
Coordinate transformation utilities for snooker table calibration
"""

import logging
from typing import List, Optional, Tuple
import numpy as np
import cv2

from ..core import ICoordinateTransformer, Point, CalibrationData

logger = logging.getLogger(__name__)

class CoordinateTransformer(ICoordinateTransformer):
    """Transforms coordinates between pixel and table coordinate systems"""
    
    def __init__(self, calibration_data: Optional[CalibrationData] = None):
        self.calibration_data = calibration_data
        self.homography_matrix = None
        self.inverse_homography = None
        
        if calibration_data and calibration_data.homography_matrix is not None:
            self.set_homography(calibration_data.homography_matrix)
    
    def set_homography(self, homography_matrix: np.ndarray) -> None:
        """Set homography transformation matrix"""
        try:
            self.homography_matrix = homography_matrix.copy()
            self.inverse_homography = np.linalg.inv(homography_matrix)
            logger.debug("Homography matrix updated successfully")
        except Exception as e:
            logger.error(f"Failed to set homography matrix: {e}")
            self.homography_matrix = None
            self.inverse_homography = None
    
    def pixel_to_table(self, pixel_point: Point) -> Optional[Point]:
        """Convert pixel coordinates to table coordinates (in meters)"""
        if self.homography_matrix is None:
            logger.warning("No homography matrix available for transformation")
            return None
        
        try:
            # Convert point to homogeneous coordinates
            pixel_coords = np.array([[pixel_point.x, pixel_point.y]], dtype=np.float32)
            pixel_coords = pixel_coords.reshape(-1, 1, 2)
            
            # Apply homography transformation
            table_coords = cv2.perspectiveTransform(pixel_coords, self.homography_matrix)
            
            # Extract transformed coordinates
            x, y = table_coords[0, 0]
            
            # Convert from pixels to meters (assuming the homography maps to a standard table)
            if self.calibration_data:
                table_length = self.calibration_data.table_dimensions[0]
                table_width = self.calibration_data.table_dimensions[1]
                
                # Normalize to table dimensions
                # Assuming the homography maps to a rectangle of size (800, 400) pixels
                x_meters = (x / 800.0) * table_length
                y_meters = (y / 400.0) * table_width
                
                return Point(x_meters, y_meters)
            else:
                # Return in transformed pixel coordinates
                return Point(x, y)
                
        except Exception as e:
            logger.error(f"Pixel to table transformation failed: {e}")
            return None
    
    def table_to_pixel(self, table_point: Point) -> Optional[Point]:
        """Convert table coordinates (in meters) to pixel coordinates"""
        if self.inverse_homography is None:
            logger.warning("No inverse homography matrix available for transformation")
            return None
        
        try:
            # Convert from meters to normalized coordinates
            if self.calibration_data:
                table_length = self.calibration_data.table_dimensions[0]
                table_width = self.calibration_data.table_dimensions[1]
                
                # Convert to pixel coordinates in the standard rectangle
                x_px = (table_point.x / table_length) * 800.0
                y_px = (table_point.y / table_width) * 400.0
            else:
                x_px, y_px = table_point.x, table_point.y
            
            # Convert point to homogeneous coordinates
            table_coords = np.array([[x_px, y_px]], dtype=np.float32)
            table_coords = table_coords.reshape(-1, 1, 2)
            
            # Apply inverse homography transformation
            pixel_coords = cv2.perspectiveTransform(table_coords, self.inverse_homography)
            
            # Extract transformed coordinates
            x, y = pixel_coords[0, 0]
            
            return Point(x, y)
            
        except Exception as e:
            logger.error(f"Table to pixel transformation failed: {e}")
            return None
    
    def transform_trajectory(self, pixel_trajectory: List[Point]) -> List[Point]:
        """Transform entire trajectory to table coordinates"""
        if not pixel_trajectory:
            return []
        
        table_trajectory = []
        
        for pixel_point in pixel_trajectory:
            table_point = self.pixel_to_table(pixel_point)
            if table_point:
                table_trajectory.append(table_point)
        
        return table_trajectory
    
    def transform_bounding_box_to_table(self, pixel_bbox: Tuple[int, int, int, int]) -> Optional[Tuple[float, float, float, float]]:
        """Transform bounding box from pixel to table coordinates"""
        x1, y1, x2, y2 = pixel_bbox
        
        # Transform corner points
        top_left = self.pixel_to_table(Point(x1, y1))
        bottom_right = self.pixel_to_table(Point(x2, y2))
        
        if top_left and bottom_right:
            return (top_left.x, top_left.y, bottom_right.x, bottom_right.y)
        
        return None
    
    def get_table_dimensions_in_pixels(self) -> Optional[Tuple[int, int]]:
        """Get table dimensions in the current pixel coordinate system"""
        if not self.calibration_data or not self.calibration_data.table_corners:
            return None
        
        corners = self.calibration_data.table_corners
        
        if len(corners) < 4:
            return None
        
        # Calculate width and height from corners
        # Assuming corners are ordered: top-left, top-right, bottom-right, bottom-left
        width = max(
            corners[1].distance_to(corners[0]),  # top edge
            corners[2].distance_to(corners[3])   # bottom edge
        )
        
        height = max(
            corners[3].distance_to(corners[0]),  # left edge
            corners[2].distance_to(corners[1])   # right edge
        )
        
        return (int(width), int(height))
    
    def is_point_on_table(self, pixel_point: Point, margin: float = 0.1) -> bool:
        """Check if a pixel point is within the table boundaries"""
        if not self.calibration_data or not self.calibration_data.table_corners:
            return True  # Assume on table if no calibration
        
        corners = self.calibration_data.table_corners
        if len(corners) < 4:
            return True
        
        # Create a polygon from the table corners
        corner_points = np.array([[c.x, c.y] for c in corners], dtype=np.int32)
        
        # Check if point is inside the polygon
        result = cv2.pointPolygonTest(corner_points, (pixel_point.x, pixel_point.y), False)
        
        return result >= 0  # Inside or on the boundary
    
    def get_distance_to_table_edge(self, pixel_point: Point) -> float:
        """Get distance from point to nearest table edge"""
        if not self.calibration_data or not self.calibration_data.table_corners:
            return float('inf')
        
        corners = self.calibration_data.table_corners
        if len(corners) < 4:
            return float('inf')
        
        # Create a polygon from the table corners
        corner_points = np.array([[c.x, c.y] for c in corners], dtype=np.int32)
        
        # Get distance to polygon (negative if inside, positive if outside)
        distance = cv2.pointPolygonTest(corner_points, (pixel_point.x, pixel_point.y), True)
        
        return abs(distance)
    
    def get_pocket_regions_in_table_coords(self) -> List[Tuple[float, float, float, float]]:
        """Get pocket regions in table coordinate system"""
        if not self.calibration_data or not self.calibration_data.pocket_regions:
            return []
        
        table_pocket_regions = []
        
        for pocket_bbox in self.calibration_data.pocket_regions:
            table_bbox = self.transform_bounding_box_to_table(
                (pocket_bbox.x1, pocket_bbox.y1, pocket_bbox.x2, pocket_bbox.y2)
            )
            if table_bbox:
                table_pocket_regions.append(table_bbox)
        
        return table_pocket_regions
    
    def update_calibration_data(self, calibration_data: CalibrationData) -> None:
        """Update calibration data and homography matrix"""
        self.calibration_data = calibration_data
        
        if calibration_data.homography_matrix is not None:
            self.set_homography(calibration_data.homography_matrix)
        else:
            self.homography_matrix = None
            self.inverse_homography = None
    
    def is_transformation_available(self) -> bool:
        """Check if coordinate transformation is available"""
        return self.homography_matrix is not None and self.inverse_homography is not None

class TableGeometry:
    """Utility class for table geometry calculations"""
    
    def __init__(self, calibration_data: CalibrationData):
        self.calibration_data = calibration_data
        self.transformer = CoordinateTransformer(calibration_data)
    
    def get_table_center(self) -> Optional[Point]:
        """Get table center in pixel coordinates"""
        if not self.calibration_data.table_corners or len(self.calibration_data.table_corners) < 4:
            return None
        
        corners = self.calibration_data.table_corners
        center_x = sum(c.x for c in corners) / len(corners)
        center_y = sum(c.y for c in corners) / len(corners)
        
        return Point(center_x, center_y)
    
    def get_table_area(self) -> float:
        """Get table area in square pixels"""
        if not self.calibration_data.table_corners or len(self.calibration_data.table_corners) < 4:
            return 0.0
        
        corners = self.calibration_data.table_corners
        corner_points = np.array([[c.x, c.y] for c in corners], dtype=np.float32)
        
        return cv2.contourArea(corner_points)
    
    def get_table_perimeter(self) -> float:
        """Get table perimeter in pixels"""
        if not self.calibration_data.table_corners or len(self.calibration_data.table_corners) < 4:
            return 0.0
        
        corners = self.calibration_data.table_corners
        perimeter = 0.0
        
        for i in range(len(corners)):
            next_i = (i + 1) % len(corners)
            perimeter += corners[i].distance_to(corners[next_i])
        
        return perimeter
    
    def is_point_near_pocket(self, point: Point, threshold: float = 50.0) -> Tuple[bool, int]:
        """Check if point is near any pocket"""
        if not self.calibration_data.pocket_regions:
            return False, -1
        
        for i, pocket in enumerate(self.calibration_data.pocket_regions):
            pocket_center = Point(
                (pocket.x1 + pocket.x2) / 2,
                (pocket.y1 + pocket.y2) / 2
            )
            
            distance = point.distance_to(pocket_center)
            if distance <= threshold:
                return True, i
        
        return False, -1