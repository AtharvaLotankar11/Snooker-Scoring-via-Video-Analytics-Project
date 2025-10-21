#!/usr/bin/env python3
"""
Abstract interfaces for the snooker detection system
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import numpy as np

from .data_models import (
    Detection, TrackedBall, CalibrationData, FrameAnalysis,
    Point, BoundingBox
)

class IDetectionEngine(ABC):
    """Interface for ball detection engines"""
    
    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        """Load detection model"""
        pass
    
    @abstractmethod
    def detect_balls(self, frame: np.ndarray) -> List[Detection]:
        """Detect balls in frame"""
        pass
    
    @abstractmethod
    def set_confidence_threshold(self, threshold: float) -> None:
        """Set detection confidence threshold"""
        pass
    
    @abstractmethod
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        pass

class ICalibrationEngine(ABC):
    """Interface for table calibration engines"""
    
    @abstractmethod
    def detect_table_corners(self, frame: np.ndarray) -> List[Point]:
        """Detect table corner points"""
        pass
    
    @abstractmethod
    def calculate_homography(self, corners: List[Point]) -> Optional[np.ndarray]:
        """Calculate homography transformation matrix"""
        pass
    
    @abstractmethod
    def is_calibrated(self) -> bool:
        """Check if calibration is valid"""
        pass
    
    @abstractmethod
    def get_calibration_data(self) -> CalibrationData:
        """Get current calibration data"""
        pass
    
    @abstractmethod
    def reset_calibration(self) -> None:
        """Reset calibration data"""
        pass

class ITracker(ABC):
    """Interface for ball tracking systems"""
    
    @abstractmethod
    def update(self, detections: List[Detection], frame_number: int) -> List[TrackedBall]:
        """Update tracking with new detections"""
        pass
    
    @abstractmethod
    def get_active_tracks(self) -> List[TrackedBall]:
        """Get currently active tracks"""
        pass
    
    @abstractmethod
    def reset_tracking(self) -> None:
        """Reset all tracking data"""
        pass
    
    @abstractmethod
    def get_track_by_id(self, track_id: int) -> Optional[TrackedBall]:
        """Get specific track by ID"""
        pass

class ICoordinateTransformer(ABC):
    """Interface for coordinate transformation"""
    
    @abstractmethod
    def pixel_to_table(self, pixel_point: Point) -> Optional[Point]:
        """Convert pixel coordinates to table coordinates"""
        pass
    
    @abstractmethod
    def table_to_pixel(self, table_point: Point) -> Optional[Point]:
        """Convert table coordinates to pixel coordinates"""
        pass
    
    @abstractmethod
    def transform_trajectory(self, pixel_trajectory: List[Point]) -> List[Point]:
        """Transform entire trajectory to table coordinates"""
        pass
    
    @abstractmethod
    def set_homography(self, homography_matrix: np.ndarray) -> None:
        """Set homography transformation matrix"""
        pass

class IVideoInputHandler(ABC):
    """Interface for video input handling"""
    
    @abstractmethod
    def open_source(self, source: str) -> bool:
        """Open video source (file path or stream URL)"""
        pass
    
    @abstractmethod
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read next frame"""
        pass
    
    @abstractmethod
    def is_opened(self) -> bool:
        """Check if source is opened"""
        pass
    
    @abstractmethod
    def release(self) -> None:
        """Release video source"""
        pass
    
    @abstractmethod
    def get_frame_count(self) -> int:
        """Get total frame count (for video files)"""
        pass
    
    @abstractmethod
    def get_fps(self) -> float:
        """Get frames per second"""
        pass

class IFrameProcessor(ABC):
    """Interface for frame processing pipeline"""
    
    @abstractmethod
    def process_frame(self, frame: np.ndarray, frame_number: int, 
                     video_source: str = "") -> FrameAnalysis:
        """Process single frame"""
        pass
    
    @abstractmethod
    def set_debug_mode(self, enabled: bool) -> None:
        """Enable/disable debug mode"""
        pass
    
    @abstractmethod
    def get_processing_stats(self) -> dict:
        """Get processing performance statistics"""
        pass

class IDetectionAPI(ABC):
    """Interface for detection API"""
    
    @abstractmethod
    def start_analysis(self, video_source: str) -> bool:
        """Start video analysis"""
        pass
    
    @abstractmethod
    def stop_analysis(self) -> None:
        """Stop video analysis"""
        pass
    
    @abstractmethod
    def get_latest_results(self) -> Optional[FrameAnalysis]:
        """Get latest analysis results"""
        pass
    
    @abstractmethod
    def get_analysis_history(self, num_frames: int = 10) -> List[FrameAnalysis]:
        """Get recent analysis history"""
        pass
    
    @abstractmethod
    def is_analyzing(self) -> bool:
        """Check if analysis is running"""
        pass

class IErrorHandler(ABC):
    """Interface for error handling"""
    
    @abstractmethod
    def handle_detection_error(self, error: Exception, frame: np.ndarray) -> List[Detection]:
        """Handle detection errors"""
        pass
    
    @abstractmethod
    def handle_calibration_error(self, error: Exception) -> CalibrationData:
        """Handle calibration errors"""
        pass
    
    @abstractmethod
    def handle_tracking_error(self, error: Exception, detections: List[Detection]) -> List[TrackedBall]:
        """Handle tracking errors"""
        pass
    
    @abstractmethod
    def log_error(self, error: Exception, context: str) -> None:
        """Log error with context"""
        pass