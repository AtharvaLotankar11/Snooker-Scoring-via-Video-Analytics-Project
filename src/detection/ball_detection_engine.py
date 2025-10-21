#!/usr/bin/env python3
"""
Ball Detection Engine using YOLO for snooker ball detection
"""

import os
import time
import logging
from typing import List, Optional
import numpy as np
import cv2

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from ..core import (
    IDetectionEngine, Detection, BoundingBox, BallType, DetectionConfig,
    BALL_CLASSES
)
from .detection_validator import DetectionValidator, DetectionFormatter

logger = logging.getLogger(__name__)

class BallDetectionEngine(IDetectionEngine):
    """YOLO-based ball detection engine"""
    
    def __init__(self, config: DetectionConfig):
        self.config = config
        self.model = None
        self.is_loaded = False
        self.validator = DetectionValidator(min_confidence=config.confidence_threshold)
        self.formatter = DetectionFormatter()
        self.detection_stats = {
            'total_detections': 0,
            'avg_confidence': 0.0,
            'processing_times': []
        }
    
    def load_model(self, model_path: str = None) -> bool:
        """Load YOLO model with fallback options"""
        if YOLO is None:
            logger.error("Ultralytics YOLO not available. Install with: pip install ultralytics")
            return False
        
        model_path = model_path or self.config.model_path
        
        try:
            # Try to load custom trained model first
            if os.path.exists(model_path):
                logger.info(f"Loading custom model from {model_path}")
                self.model = YOLO(model_path)
                self.is_loaded = True
                logger.info("✅ Custom model loaded successfully")
                return True
            else:
                logger.warning(f"Custom model not found at {model_path}")
        except Exception as e:
            logger.error(f"Failed to load custom model: {e}")
        
        # Fallback to pre-trained YOLOv8 model
        try:
            logger.info("Loading pre-trained YOLOv8s model as fallback")
            self.model = YOLO("yolov8s.pt")
            self.is_loaded = True
            logger.info("✅ Pre-trained YOLOv8s model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load fallback model: {e}")
            return False
    
    def detect_balls(self, frame: np.ndarray) -> List[Detection]:
        """Detect balls in the given frame"""
        if not self.is_model_loaded():
            logger.error("Model not loaded. Call load_model() first.")
            return []
        
        start_time = time.time()
        detections = []
        
        try:
            # Run YOLO inference
            results = self.model(
                frame,
                conf=self.config.confidence_threshold,
                iou=self.config.nms_threshold,
                imgsz=self.config.input_size,
                device=self.config.device,
                verbose=False
            )
            
            # Process results
            if results and len(results) > 0:
                boxes = results[0].boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        class_id = int(box.cls.item())
                        confidence = float(box.conf.item())
                        
                        # Only process known ball classes
                        if class_id in BALL_CLASSES:
                            # Extract bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                            
                            # Create detection object
                            bbox = BoundingBox(x1, y1, x2, y2)
                            detection = Detection(
                                bbox=bbox,
                                class_id=class_id,
                                confidence=confidence,
                                timestamp=time.time()
                            )
                            detections.append(detection)
            
            # Validate and filter detections
            validated_detections = self.validator.validate_detections(detections, frame.shape)
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(validated_detections, processing_time)
            
            return validated_detections
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """Set detection confidence threshold"""
        if 0.0 <= threshold <= 1.0:
            self.config.confidence_threshold = threshold
            self.validator.set_confidence_threshold(threshold)
            logger.info(f"Confidence threshold set to {threshold}")
        else:
            logger.warning(f"Invalid confidence threshold: {threshold}. Must be between 0.0 and 1.0")
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded and ready"""
        return self.is_loaded and self.model is not None
    
    def get_detection_stats(self) -> dict:
        """Get detection performance statistics"""
        return self.detection_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset detection statistics"""
        self.detection_stats = {
            'total_detections': 0,
            'avg_confidence': 0.0,
            'processing_times': []
        }
    
    def _update_stats(self, detections: List[Detection], processing_time: float) -> None:
        """Update internal statistics"""
        self.detection_stats['total_detections'] += len(detections)
        self.detection_stats['processing_times'].append(processing_time)
        
        # Keep only last 100 processing times
        if len(self.detection_stats['processing_times']) > 100:
            self.detection_stats['processing_times'] = self.detection_stats['processing_times'][-50:]
        
        # Update average confidence
        if detections:
            confidences = [d.confidence for d in detections]
            current_avg = self.detection_stats['avg_confidence']
            total_detections = self.detection_stats['total_detections']
            
            # Running average calculation
            if total_detections > len(detections):
                weight = len(detections) / total_detections
                self.detection_stats['avg_confidence'] = (
                    current_avg * (1 - weight) + np.mean(confidences) * weight
                )
            else:
                self.detection_stats['avg_confidence'] = np.mean(confidences)
    
    def get_avg_processing_time(self) -> float:
        """Get average processing time per frame"""
        times = self.detection_stats['processing_times']
        return np.mean(times) if times else 0.0
    
    def visualize_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Draw detection bounding boxes on frame"""
        annotated_frame = frame.copy()
        
        for detection in detections:
            bbox = detection.bbox
            ball_type = detection.get_ball_type()
            ball_name, color = BALL_CLASSES[ball_type.value]
            
            # Draw bounding box
            cv2.rectangle(
                annotated_frame,
                (bbox.x1, bbox.y1),
                (bbox.x2, bbox.y2),
                color,
                2
            )
            
            # Draw label
            label = f"{ball_name} {detection.confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            
            # Background for text
            cv2.rectangle(
                annotated_frame,
                (bbox.x1, bbox.y1 - label_size[1] - 10),
                (bbox.x1 + label_size[0], bbox.y1),
                color,
                -1
            )
            
            # Text
            cv2.putText(
                annotated_frame,
                label,
                (bbox.x1, bbox.y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
            
            # Draw center point
            center = detection.get_centroid()
            cv2.circle(
                annotated_frame,
                (int(center.x), int(center.y)),
                3,
                color,
                -1
            )
        
        return annotated_frame    

    def get_formatted_detections(self, detections: List[Detection]) -> List[dict]:
        """Get detections formatted for API consumption"""
        return self.formatter.format_for_api(detections)
    
    def get_detection_summary(self, detections: List[Detection]) -> dict:
        """Get detection summary statistics"""
        return self.formatter.format_summary(detections)
    
    def get_validation_stats(self) -> dict:
        """Get detection validation statistics"""
        return self.validator.get_quality_stats()
    
    def reset_validation_stats(self) -> None:
        """Reset validation statistics"""
        self.validator.reset_stats()