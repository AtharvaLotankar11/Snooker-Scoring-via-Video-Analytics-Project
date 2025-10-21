#!/usr/bin/env python3
"""
Core module for snooker ball detection and tracking system
"""

from .data_models import (
    Point, BoundingBox, Detection, TrackedBall, CalibrationData, FrameAnalysis,
    BallType, DetectionConfig, TrackingConfig, CalibrationConfig, SystemConfig,
    BALL_CLASSES, get_ball_color, get_ball_name
)

from .interfaces import (
    IDetectionEngine, ICalibrationEngine, ITracker, ICoordinateTransformer,
    IVideoInputHandler, IFrameProcessor, IDetectionAPI, IErrorHandler
)

from .error_handling import (
    ErrorHandler, ErrorEvent, ErrorSeverity, ErrorCategory, RecoveryStrategy,
    global_error_handler, handle_error
)

from .recovery_strategies import (
    ModelReloadStrategy, CalibrationRecoveryStrategy, TrackingResetStrategy,
    VideoInputRecoveryStrategy, GracefulDegradationStrategy, FrameSkipStrategy,
    ComponentRestartStrategy, MemoryCleanupStrategy
)

# Configuration management (import from config module)
try:
    from ..config import ConfigManager, ConfigValidator, ConfigLoader, ConfigSchema
    HAS_CONFIG_MANAGEMENT = True
except ImportError:
    HAS_CONFIG_MANAGEMENT = False

__all__ = [
    # Data models
    'Point', 'BoundingBox', 'Detection', 'TrackedBall', 'CalibrationData', 'FrameAnalysis',
    'BallType', 'DetectionConfig', 'TrackingConfig', 'CalibrationConfig', 'SystemConfig',
    'BALL_CLASSES', 'get_ball_color', 'get_ball_name',
    
    # Interfaces
    'IDetectionEngine', 'ICalibrationEngine', 'ITracker', 'ICoordinateTransformer',
    'IVideoInputHandler', 'IFrameProcessor', 'IDetectionAPI', 'IErrorHandler',
    
    # Error handling
    'ErrorHandler', 'ErrorEvent', 'ErrorSeverity', 'ErrorCategory', 'RecoveryStrategy',
    'global_error_handler', 'handle_error',
    
    # Recovery strategies
    'ModelReloadStrategy', 'CalibrationRecoveryStrategy', 'TrackingResetStrategy',
    'VideoInputRecoveryStrategy', 'GracefulDegradationStrategy', 'FrameSkipStrategy',
    'ComponentRestartStrategy', 'MemoryCleanupStrategy'
]

# Add config management to exports if available
if HAS_CONFIG_MANAGEMENT:
    __all__.extend(['ConfigManager', 'ConfigValidator', 'ConfigLoader', 'ConfigSchema'])