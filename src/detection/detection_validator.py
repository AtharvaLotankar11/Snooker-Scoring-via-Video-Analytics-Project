#!/usr/bin/env python3
"""
Detection validation and filtering utilities
"""

import logging
from typing import List, Dict, Set
import numpy as np

from ..core import Detection, BallType, BALL_CLASSES

logger = logging.getLogger(__name__)

class DetectionValidator:
    """Validates and filters ball detections"""
    
    def __init__(self, min_confidence: float = 0.2, max_balls_per_type: Dict[BallType, int] = None):
        self.min_confidence = min_confidence
        self.max_balls_per_type = max_balls_per_type or {
            BallType.CUE_BALL: 1,
            BallType.YELLOW: 1,
            BallType.GREEN: 1,
            BallType.BROWN: 1,
            BallType.BLUE: 1,
            BallType.PINK: 1,
            BallType.BLACK: 1,
            BallType.RED: 15  # Maximum 15 red balls
        }
        
        # Detection quality metrics
        self.quality_stats = {
            'total_processed': 0,
            'filtered_low_confidence': 0,
            'filtered_duplicates': 0,
            'filtered_invalid_positions': 0
        }
    
    def validate_detections(self, detections: List[Detection], frame_shape: tuple = None) -> List[Detection]:
        """Validate and filter detections based on various criteria"""
        if not detections:
            return []
        
        self.quality_stats['total_processed'] += len(detections)
        
        # Step 1: Filter by confidence
        confident_detections = self._filter_by_confidence(detections)
        
        # Step 2: Filter by position validity
        if frame_shape:
            valid_position_detections = self._filter_by_position(confident_detections, frame_shape)
        else:
            valid_position_detections = confident_detections
        
        # Step 3: Remove duplicates and limit by ball type
        final_detections = self._filter_duplicates_and_limits(valid_position_detections)
        
        # Step 4: Validate ball type consistency
        validated_detections = self._validate_ball_types(final_detections)
        
        return validated_detections
    
    def _filter_by_confidence(self, detections: List[Detection]) -> List[Detection]:
        """Filter detections by confidence threshold"""
        filtered = [d for d in detections if d.confidence >= self.min_confidence]
        
        filtered_count = len(detections) - len(filtered)
        self.quality_stats['filtered_low_confidence'] += filtered_count
        
        if filtered_count > 0:
            logger.debug(f"Filtered {filtered_count} low-confidence detections")
        
        return filtered
    
    def _filter_by_position(self, detections: List[Detection], frame_shape: tuple) -> List[Detection]:
        """Filter detections with invalid positions"""
        height, width = frame_shape[:2]
        valid_detections = []
        
        for detection in detections:
            bbox = detection.bbox
            
            # Check if bounding box is within frame boundaries
            if (bbox.x1 >= 0 and bbox.y1 >= 0 and 
                bbox.x2 <= width and bbox.y2 <= height and
                bbox.x1 < bbox.x2 and bbox.y1 < bbox.y2):
                
                # Check minimum size (avoid tiny detections)
                if bbox.get_area() > 100:  # Minimum 10x10 pixels
                    valid_detections.append(detection)
                else:
                    self.quality_stats['filtered_invalid_positions'] += 1
            else:
                self.quality_stats['filtered_invalid_positions'] += 1
        
        return valid_detections
    
    def _filter_duplicates_and_limits(self, detections: List[Detection]) -> List[Detection]:
        """Remove duplicate detections and enforce ball count limits"""
        if not detections:
            return []
        
        # Group detections by ball type
        detections_by_type = {}
        for detection in detections:
            ball_type = detection.get_ball_type()
            if ball_type not in detections_by_type:
                detections_by_type[ball_type] = []
            detections_by_type[ball_type].append(detection)
        
        final_detections = []
        
        for ball_type, type_detections in detections_by_type.items():
            # Sort by confidence (highest first)
            type_detections.sort(key=lambda x: x.confidence, reverse=True)
            
            # Remove spatial duplicates (balls too close to each other)
            non_duplicate_detections = self._remove_spatial_duplicates(type_detections)
            
            # Enforce count limits
            max_count = self.max_balls_per_type.get(ball_type, 1)
            limited_detections = non_duplicate_detections[:max_count]
            
            # Track filtered duplicates
            filtered_count = len(type_detections) - len(limited_detections)
            self.quality_stats['filtered_duplicates'] += filtered_count
            
            final_detections.extend(limited_detections)
        
        return final_detections
    
    def _remove_spatial_duplicates(self, detections: List[Detection], min_distance: float = 30.0) -> List[Detection]:
        """Remove detections that are too close to each other"""
        if len(detections) <= 1:
            return detections
        
        # Sort by confidence (keep highest confidence detections)
        detections.sort(key=lambda x: x.confidence, reverse=True)
        
        filtered_detections = []
        
        for detection in detections:
            current_center = detection.get_centroid()
            is_duplicate = False
            
            # Check distance to all already accepted detections
            for accepted_detection in filtered_detections:
                accepted_center = accepted_detection.get_centroid()
                distance = current_center.distance_to(accepted_center)
                
                if distance < min_distance:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_detections.append(detection)
        
        return filtered_detections
    
    def _validate_ball_types(self, detections: List[Detection]) -> List[Detection]:
        """Validate ball type classifications"""
        # For now, just return as-is
        # Future: Add color-based validation, size consistency checks, etc.
        return detections
    
    def get_quality_stats(self) -> Dict:
        """Get detection quality statistics"""
        stats = self.quality_stats.copy()
        
        if stats['total_processed'] > 0:
            stats['confidence_filter_rate'] = stats['filtered_low_confidence'] / stats['total_processed']
            stats['duplicate_filter_rate'] = stats['filtered_duplicates'] / stats['total_processed']
            stats['position_filter_rate'] = stats['filtered_invalid_positions'] / stats['total_processed']
        else:
            stats['confidence_filter_rate'] = 0.0
            stats['duplicate_filter_rate'] = 0.0
            stats['position_filter_rate'] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset quality statistics"""
        self.quality_stats = {
            'total_processed': 0,
            'filtered_low_confidence': 0,
            'filtered_duplicates': 0,
            'filtered_invalid_positions': 0
        }
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """Update confidence threshold"""
        if 0.0 <= threshold <= 1.0:
            self.min_confidence = threshold
            logger.info(f"Detection confidence threshold updated to {threshold}")
        else:
            logger.warning(f"Invalid confidence threshold: {threshold}")

class DetectionFormatter:
    """Formats detection results for API consumption"""
    
    @staticmethod
    def format_for_api(detections: List[Detection]) -> List[Dict]:
        """Format detections for API response"""
        formatted_detections = []
        
        for detection in detections:
            ball_type = detection.get_ball_type()
            ball_name, color = BALL_CLASSES[ball_type.value]
            centroid = detection.get_centroid()
            
            formatted_detection = {
                'id': id(detection),  # Temporary ID
                'ball_type': ball_name,
                'ball_class_id': detection.class_id,
                'confidence': round(detection.confidence, 3),
                'bounding_box': {
                    'x1': detection.bbox.x1,
                    'y1': detection.bbox.y1,
                    'x2': detection.bbox.x2,
                    'y2': detection.bbox.y2,
                    'width': detection.bbox.x2 - detection.bbox.x1,
                    'height': detection.bbox.y2 - detection.bbox.y1,
                    'area': detection.bbox.get_area()
                },
                'centroid': {
                    'x': round(centroid.x, 2),
                    'y': round(centroid.y, 2)
                },
                'color_bgr': color,
                'timestamp': detection.timestamp
            }
            
            formatted_detections.append(formatted_detection)
        
        return formatted_detections
    
    @staticmethod
    def format_summary(detections: List[Detection]) -> Dict:
        """Create detection summary"""
        ball_counts = {}
        total_confidence = 0.0
        
        for detection in detections:
            ball_type = detection.get_ball_type()
            ball_name = BALL_CLASSES[ball_type.value][0]
            
            ball_counts[ball_name] = ball_counts.get(ball_name, 0) + 1
            total_confidence += detection.confidence
        
        avg_confidence = total_confidence / len(detections) if detections else 0.0
        
        return {
            'total_balls_detected': len(detections),
            'ball_counts': ball_counts,
            'average_confidence': round(avg_confidence, 3),
            'detection_timestamp': detections[0].timestamp if detections else None
        }