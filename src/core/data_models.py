#!/usr/bin/env python3
"""
Core data models for snooker ball detection and tracking system
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from enum import Enum
import time

class BallType(Enum):
    """Enumeration of snooker ball types"""
    CUE_BALL = 0
    YELLOW = 1
    RED = 2
    BROWN = 3  # Changed from ORANGE to BROWN to match snooker terminology
    GREEN = 4
    PINK = 5
    BLUE = 6
    BLACK = 7

@dataclass
class Point:
    """2D point representation"""
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point"""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple format"""
        return (self.x, self.y)

@dataclass
class BoundingBox:
    """Bounding box representation"""
    x1: int
    y1: int
    x2: int
    y2: int
    
    def get_center(self) -> Point:
        """Get center point of bounding box"""
        return Point((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    def get_area(self) -> int:
        """Calculate bounding box area"""
        return (self.x2 - self.x1) * (self.y2 - self.y1)
    
    def to_xyxy(self) -> Tuple[int, int, int, int]:
        """Convert to (x1, y1, x2, y2) format"""
        return (self.x1, self.y1, self.x2, self.y2)

@dataclass
class Detection:
    """Ball detection result"""
    bbox: BoundingBox
    class_id: int
    confidence: float
    timestamp: float = field(default_factory=time.time)
    
    def get_centroid(self) -> Point:
        """Get detection centroid"""
        return self.bbox.get_center()
    
    def get_ball_type(self) -> BallType:
        """Get ball type from class ID"""
        return BallType(self.class_id)

@dataclass
class TrackedBall:
    """Tracked ball with trajectory history"""
    track_id: int
    ball_type: BallType
    current_position: Point
    trajectory: List[Point] = field(default_factory=list)
    confidence_history: List[float] = field(default_factory=list)
    last_seen_frame: int = 0
    is_active: bool = True
    velocity: Optional[Point] = None
    
    def update_position(self, new_position: Point, confidence: float, frame_number: int):
        """Update ball position and trajectory"""
        if self.current_position:
            # Calculate velocity
            dx = new_position.x - self.current_position.x
            dy = new_position.y - self.current_position.y
            self.velocity = Point(dx, dy)
        
        self.current_position = new_position
        self.trajectory.append(new_position)
        self.confidence_history.append(confidence)
        self.last_seen_frame = frame_number
        
        # Keep trajectory history manageable
        if len(self.trajectory) > 100:
            self.trajectory = self.trajectory[-50:]
            self.confidence_history = self.confidence_history[-50:]
    
    def predict_next_position(self) -> Optional[Point]:
        """Predict next position based on velocity"""
        if self.velocity and self.current_position:
            return Point(
                self.current_position.x + self.velocity.x,
                self.current_position.y + self.velocity.y
            )
        return None
    
    def is_lost(self, current_frame: int, max_frames: int = 10) -> bool:
        """Check if ball tracking is lost"""
        return (current_frame - self.last_seen_frame) > max_frames

@dataclass
class CalibrationData:
    """Table calibration information"""
    homography_matrix: Optional[np.ndarray] = None
    table_corners: List[Point] = field(default_factory=list)
    table_dimensions: Tuple[float, float] = (3.569, 1.778)  # Standard snooker table
    pocket_regions: List[BoundingBox] = field(default_factory=list)
    calibration_timestamp: float = field(default_factory=time.time)
    is_valid: bool = False
    
    def is_calibrated(self) -> bool:
        """Check if calibration is valid"""
        return (self.is_valid and 
                self.homography_matrix is not None and 
                len(self.table_corners) == 4)

@dataclass
class FrameAnalysis:
    """Complete analysis result for a single frame"""
    frame_number: int
    timestamp: float
    detections: List[Detection] = field(default_factory=list)
    tracked_balls: List[TrackedBall] = field(default_factory=list)
    calibration_data: Optional[CalibrationData] = None
    processing_time: float = 0.0
    
    def get_ball_count(self) -> int:
        """Get total number of detected balls"""
        return len(self.detections)
    
    def get_active_tracks(self) -> List[TrackedBall]:
        """Get only active tracked balls"""
        return [ball for ball in self.tracked_balls if ball.is_active]

# Configuration Classes
@dataclass
class DetectionConfig:
    """Configuration for ball detection"""
    model_path: str = "models/best.pt"
    confidence_threshold: float = 0.2
    nms_threshold: float = 0.5
    input_size: Tuple[int, int] = (640, 640)
    device: str = "cpu"  # or "cuda"
    
@dataclass
class TrackingConfig:
    """Configuration for ball tracking"""
    max_disappeared_frames: int = 10
    max_tracking_distance: float = 50.0
    kalman_process_noise: float = 0.1
    kalman_measurement_noise: float = 0.1
    trajectory_smoothing: bool = True
    
@dataclass
class CalibrationConfig:
    """Configuration for table calibration"""
    table_length: float = 3.569  # meters
    table_width: float = 1.778   # meters
    auto_recalibrate: bool = True
    calibration_interval: int = 100  # frames
    corner_detection_threshold: float = 0.1
    
@dataclass
class SystemConfig:
    """Overall system configuration"""
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    calibration: CalibrationConfig = field(default_factory=CalibrationConfig)
    debug_mode: bool = False
    save_debug_frames: bool = False
    output_directory: str = "output"

# Ball class mappings (compatible with existing config.py)
BALL_CLASSES = {
    0: ("cue_ball", (255, 255, 255)),
    1: ("yellow_ball", (0, 255, 255)),
    2: ("red_ball", (255, 0, 0)),
    3: ("orange_ball", (165, 42, 42)),
    4: ("green_ball", (0, 128, 0)),
    5: ("pink_ball", (255, 20, 147)),
    6: ("blue_ball", (0, 0, 255)),
    7: ("black_ball", (0, 0, 0))
}

def get_ball_color(ball_type: BallType) -> Tuple[int, int, int]:
    """Get BGR color for ball type"""
    return BALL_CLASSES[ball_type.value][1]

def get_ball_name(ball_type: BallType) -> str:
    """Get name for ball type"""
    return BALL_CLASSES[ball_type.value][0]