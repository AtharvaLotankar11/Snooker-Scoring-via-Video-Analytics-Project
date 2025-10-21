#!/usr/bin/env python3
"""
Snooker Ball Detection and Calibration System

A comprehensive computer vision system for detecting, tracking, and analyzing
snooker balls in video streams with automatic table calibration.
"""

from .core import (
    Point, BoundingBox, Detection, TrackedBall, CalibrationData, FrameAnalysis,
    BallType, DetectionConfig, TrackingConfig, CalibrationConfig, SystemConfig,
    BALL_CLASSES, get_ball_color, get_ball_name
)

from .detection import BallDetectionEngine, DetectionValidator, DetectionFormatter
from .calibration import TableCalibrationEngine, CoordinateTransformer, TableGeometry
from .tracking import BallTracker, TrajectoryAnalyzer, BallState
from .processing import FrameProcessor, VideoInputHandler, VideoWriter
from .api import DetectionAPI

__version__ = "1.0.0"
__author__ = "Snooker Analytics Team"

__all__ = [
    # Core data models
    'Point', 'BoundingBox', 'Detection', 'TrackedBall', 'CalibrationData', 'FrameAnalysis',
    'BallType', 'DetectionConfig', 'TrackingConfig', 'CalibrationConfig', 'SystemConfig',
    'BALL_CLASSES', 'get_ball_color', 'get_ball_name',
    
    # Detection components
    'BallDetectionEngine', 'DetectionValidator', 'DetectionFormatter',
    
    # Calibration components
    'TableCalibrationEngine', 'CoordinateTransformer', 'TableGeometry',
    
    # Tracking components
    'BallTracker', 'TrajectoryAnalyzer', 'BallState',
    
    # Processing components
    'FrameProcessor', 'VideoInputHandler', 'VideoWriter',
    
    # API
    'DetectionAPI'
]

def create_default_config() -> SystemConfig:
    """Create default system configuration"""
    return SystemConfig(
        detection=DetectionConfig(
            model_path="models/best.pt",
            confidence_threshold=0.2,
            device="cpu"
        ),
        tracking=TrackingConfig(
            max_disappeared_frames=10,
            max_tracking_distance=50.0
        ),
        calibration=CalibrationConfig(
            auto_recalibrate=True,
            calibration_interval=100
        ),
        debug_mode=False
    )

def create_detection_system(config: SystemConfig = None) -> DetectionAPI:
    """Create and initialize a complete detection system"""
    if config is None:
        config = create_default_config()
    
    return DetectionAPI(config)