#!/usr/bin/env python3
"""
Configuration schema definitions and validation rules
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

class ConfigType(Enum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    PATH = "path"
    ENUM = "enum"

@dataclass
class ConfigField:
    """Configuration field definition"""
    name: str
    type: ConfigType
    default: Any
    description: str
    required: bool = True
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    validation_func: Optional[callable] = None
    
    def validate(self, value: Any) -> tuple[bool, str]:
        """Validate a value against this field definition"""
        # Check required
        if self.required and value is None:
            return False, f"Field '{self.name}' is required"
        
        if value is None:
            return True, ""
        
        # Type validation
        if self.type == ConfigType.STRING and not isinstance(value, str):
            return False, f"Field '{self.name}' must be a string"
        elif self.type == ConfigType.INTEGER and not isinstance(value, int):
            return False, f"Field '{self.name}' must be an integer"
        elif self.type == ConfigType.FLOAT and not isinstance(value, (int, float)):
            return False, f"Field '{self.name}' must be a number"
        elif self.type == ConfigType.BOOLEAN and not isinstance(value, bool):
            return False, f"Field '{self.name}' must be a boolean"
        elif self.type == ConfigType.LIST and not isinstance(value, list):
            return False, f"Field '{self.name}' must be a list"
        elif self.type == ConfigType.DICT and not isinstance(value, dict):
            return False, f"Field '{self.name}' must be a dictionary"
        elif self.type == ConfigType.PATH and not isinstance(value, str):
            return False, f"Field '{self.name}' must be a valid path string"
        
        # Range validation
        if self.type in [ConfigType.INTEGER, ConfigType.FLOAT]:
            if self.min_value is not None and value < self.min_value:
                return False, f"Field '{self.name}' must be >= {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"Field '{self.name}' must be <= {self.max_value}"
        
        # Allowed values validation
        if self.allowed_values and value not in self.allowed_values:
            return False, f"Field '{self.name}' must be one of {self.allowed_values}"
        
        # Custom validation
        if self.validation_func:
            try:
                is_valid, message = self.validation_func(value)
                if not is_valid:
                    return False, f"Field '{self.name}': {message}"
            except Exception as e:
                return False, f"Field '{self.name}' validation error: {e}"
        
        return True, ""

class ConfigSchema:
    """Configuration schema for the snooker detection system"""
    
    def __init__(self):
        self.fields = self._define_schema()
    
    def _define_schema(self) -> Dict[str, ConfigField]:
        """Define the complete configuration schema"""
        
        def validate_model_path(path: str) -> tuple[bool, str]:
            """Validate model path exists or is downloadable"""
            import os
            if os.path.exists(path):
                return True, ""
            # Check if it's a known model name that can be downloaded
            known_models = ["yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt"]
            if any(model in path for model in known_models):
                return True, ""
            return False, "Model path does not exist and is not a known downloadable model"
        
        def validate_directory_path(path: str) -> tuple[bool, str]:
            """Validate directory path can be created"""
            import os
            try:
                os.makedirs(path, exist_ok=True)
                return True, ""
            except Exception as e:
                return False, f"Cannot create directory: {e}"
        
        return {
            # Detection Configuration
            "detection.model_path": ConfigField(
                name="detection.model_path",
                type=ConfigType.PATH,
                default="models/best.pt",
                description="Path to the YOLO model file",
                validation_func=validate_model_path
            ),
            "detection.confidence_threshold": ConfigField(
                name="detection.confidence_threshold",
                type=ConfigType.FLOAT,
                default=0.2,
                description="Minimum confidence threshold for detections",
                min_value=0.0,
                max_value=1.0
            ),
            "detection.nms_threshold": ConfigField(
                name="detection.nms_threshold",
                type=ConfigType.FLOAT,
                default=0.5,
                description="Non-maximum suppression threshold",
                min_value=0.0,
                max_value=1.0
            ),
            "detection.input_size": ConfigField(
                name="detection.input_size",
                type=ConfigType.LIST,
                default=[640, 640],
                description="Input size for the model [width, height]"
            ),
            "detection.device": ConfigField(
                name="detection.device",
                type=ConfigType.ENUM,
                default="cpu",
                description="Device to run inference on",
                allowed_values=["cpu", "cuda", "mps"]
            ),
            
            # Tracking Configuration
            "tracking.max_disappeared_frames": ConfigField(
                name="tracking.max_disappeared_frames",
                type=ConfigType.INTEGER,
                default=10,
                description="Maximum frames a track can be lost before deletion",
                min_value=1,
                max_value=100
            ),
            "tracking.max_tracking_distance": ConfigField(
                name="tracking.max_tracking_distance",
                type=ConfigType.FLOAT,
                default=50.0,
                description="Maximum distance for track association",
                min_value=1.0,
                max_value=500.0
            ),
            "tracking.kalman_process_noise": ConfigField(
                name="tracking.kalman_process_noise",
                type=ConfigType.FLOAT,
                default=0.1,
                description="Kalman filter process noise",
                min_value=0.001,
                max_value=1.0
            ),
            "tracking.kalman_measurement_noise": ConfigField(
                name="tracking.kalman_measurement_noise",
                type=ConfigType.FLOAT,
                default=0.1,
                description="Kalman filter measurement noise",
                min_value=0.001,
                max_value=1.0
            ),
            "tracking.trajectory_smoothing": ConfigField(
                name="tracking.trajectory_smoothing",
                type=ConfigType.BOOLEAN,
                default=True,
                description="Enable trajectory smoothing"
            ),
            
            # Calibration Configuration
            "calibration.table_length": ConfigField(
                name="calibration.table_length",
                type=ConfigType.FLOAT,
                default=3.569,
                description="Snooker table length in meters",
                min_value=3.0,
                max_value=4.0
            ),
            "calibration.table_width": ConfigField(
                name="calibration.table_width",
                type=ConfigType.FLOAT,
                default=1.778,
                description="Snooker table width in meters",
                min_value=1.5,
                max_value=2.0
            ),
            "calibration.auto_recalibrate": ConfigField(
                name="calibration.auto_recalibrate",
                type=ConfigType.BOOLEAN,
                default=True,
                description="Enable automatic recalibration"
            ),
            "calibration.calibration_interval": ConfigField(
                name="calibration.calibration_interval",
                type=ConfigType.INTEGER,
                default=100,
                description="Frames between calibration attempts",
                min_value=10,
                max_value=1000
            ),
            "calibration.corner_detection_threshold": ConfigField(
                name="calibration.corner_detection_threshold",
                type=ConfigType.FLOAT,
                default=0.1,
                description="Threshold for corner detection",
                min_value=0.01,
                max_value=1.0
            ),
            
            # System Configuration
            "system.debug_mode": ConfigField(
                name="system.debug_mode",
                type=ConfigType.BOOLEAN,
                default=False,
                description="Enable debug mode with verbose logging"
            ),
            "system.save_debug_frames": ConfigField(
                name="system.save_debug_frames",
                type=ConfigType.BOOLEAN,
                default=False,
                description="Save debug frames to disk"
            ),
            "system.output_directory": ConfigField(
                name="system.output_directory",
                type=ConfigType.PATH,
                default="output",
                description="Directory for output files",
                validation_func=validate_directory_path
            ),
            "system.log_level": ConfigField(
                name="system.log_level",
                type=ConfigType.ENUM,
                default="INFO",
                description="Logging level",
                allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            ),
            "system.max_threads": ConfigField(
                name="system.max_threads",
                type=ConfigType.INTEGER,
                default=4,
                description="Maximum number of processing threads",
                min_value=1,
                max_value=16
            ),
            
            # Performance Configuration
            "performance.target_fps": ConfigField(
                name="performance.target_fps",
                type=ConfigType.FLOAT,
                default=30.0,
                description="Target processing FPS",
                min_value=1.0,
                max_value=120.0
            ),
            "performance.frame_skip_threshold": ConfigField(
                name="performance.frame_skip_threshold",
                type=ConfigType.FLOAT,
                default=0.1,
                description="Processing time threshold for frame skipping",
                min_value=0.01,
                max_value=1.0
            ),
            "performance.memory_limit_mb": ConfigField(
                name="performance.memory_limit_mb",
                type=ConfigType.INTEGER,
                default=2048,
                description="Memory limit in MB",
                min_value=512,
                max_value=16384
            ),
            
            # Visualization Configuration
            "visualization.enable_overlay": ConfigField(
                name="visualization.enable_overlay",
                type=ConfigType.BOOLEAN,
                default=True,
                description="Enable visualization overlays"
            ),
            "visualization.show_detections": ConfigField(
                name="visualization.show_detections",
                type=ConfigType.BOOLEAN,
                default=True,
                description="Show detection bounding boxes"
            ),
            "visualization.show_tracking": ConfigField(
                name="visualization.show_tracking",
                type=ConfigType.BOOLEAN,
                default=True,
                description="Show tracking information"
            ),
            "visualization.show_calibration": ConfigField(
                name="visualization.show_calibration",
                type=ConfigType.BOOLEAN,
                default=True,
                description="Show calibration visualization"
            ),
            "visualization.trajectory_length": ConfigField(
                name="visualization.trajectory_length",
                type=ConfigType.INTEGER,
                default=20,
                description="Number of trajectory points to display",
                min_value=5,
                max_value=100
            )
        }
    
    def get_field(self, field_name: str) -> Optional[ConfigField]:
        """Get field definition by name"""
        return self.fields.get(field_name)
    
    def get_all_fields(self) -> Dict[str, ConfigField]:
        """Get all field definitions"""
        return self.fields.copy()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        config = {}
        for field_name, field_def in self.fields.items():
            self._set_nested_value(config, field_name, field_def.default)
        return config
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested dictionary value using dot notation"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value