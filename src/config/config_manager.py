#!/usr/bin/env python3
"""
Main configuration manager for the snooker detection system
"""

import logging
import os
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import threading
import time

from .config_schema import ConfigSchema
from .config_validator import ConfigValidator, ValidationResult
from .config_loader import ConfigLoader
from ..core import SystemConfig, DetectionConfig, TrackingConfig, CalibrationConfig

logger = logging.getLogger(__name__)

class ConfigManager:
    """Centralized configuration management system"""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        self.config_file = Path(config_file) if config_file else None
        self.schema = ConfigSchema()
        self.validator = ConfigValidator(self.schema)
        self.loader = ConfigLoader()
        
        # Configuration state
        self._config: Dict[str, Any] = {}
        self._config_lock = threading.RLock()
        self._last_modified = 0
        self._auto_reload = False
        self._reload_thread = None
        
        # Change callbacks
        self._change_callbacks: List[callable] = []
        
        # Load initial configuration
        self._load_initial_config()
    
    def _load_initial_config(self) -> None:
        """Load initial configuration from file or defaults"""
        try:
            if self.config_file and self.config_file.exists():
                self.load_from_file(self.config_file)
            else:
                # Use default configuration
                self._config = self.schema.get_default_config()
                logger.info("Using default configuration")
        except Exception as e:
            logger.error(f"Failed to load initial config: {e}")
            self._config = self.schema.get_default_config()
    
    def load_from_file(self, config_path: Union[str, Path]) -> ValidationResult:
        """Load configuration from file with validation"""
        config_path = Path(config_path)
        
        try:
            # Load raw configuration
            raw_config = self.loader.load_config(config_path)
            
            # Validate configuration
            validation_result = self.validator.validate_config(raw_config, auto_fix=True)
            
            # Apply fixes if any
            if validation_result.fixed_values:
                fixed_config = self._apply_fixes(raw_config, validation_result.fixed_values)
            else:
                fixed_config = raw_config
            
            # Update configuration if valid or auto-fixed
            if validation_result.is_valid:
                with self._config_lock:
                    self._config = fixed_config
                    self.config_file = config_path
                    self._last_modified = config_path.stat().st_mtime
                
                # Notify callbacks
                self._notify_change_callbacks()
                
                logger.info(f"Configuration loaded successfully: {validation_result.get_summary()}")
            else:
                logger.error(f"Configuration validation failed: {validation_result.get_summary()}")
                for error in validation_result.errors:
                    logger.error(f"  - {error}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            result = ValidationResult()
            result.add_error(str(e))
            return result
    
    def save_to_file(self, config_path: Optional[Union[str, Path]] = None,
                    format: Optional[str] = None,
                    create_backup: bool = True) -> bool:
        """Save current configuration to file"""
        target_path = Path(config_path) if config_path else self.config_file
        
        if not target_path:
            logger.error("No config file path specified")
            return False
        
        try:
            # Create backup if requested
            if create_backup and target_path.exists():
                self.loader.backup_config(target_path)
            
            # Save configuration
            with self._config_lock:
                self.loader.save_config(self._config, target_path, format)
            
            # Update file reference
            self.config_file = target_path
            self._last_modified = target_path.stat().st_mtime
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration (thread-safe copy)"""
        with self._config_lock:
            return self._deep_copy(self._config)
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        with self._config_lock:
            return self._get_nested_value(self._config, key, default)
    
    def set_value(self, key: str, value: Any, validate: bool = True) -> bool:
        """Set configuration value using dot notation"""
        if validate:
            # Validate the new value
            validation_result = self.validator.validate_field_value(key, value)
            if not validation_result.is_valid:
                logger.error(f"Invalid value for '{key}': {validation_result.errors[0]}")
                return False
        
        with self._config_lock:
            old_value = self._get_nested_value(self._config, key)
            self._set_nested_value(self._config, key, value)
            
            # Notify callbacks if value changed
            if old_value != value:
                self._notify_change_callbacks()
            
            logger.debug(f"Configuration updated: {key} = {value}")
            return True
    
    def update_config(self, updates: Dict[str, Any], validate: bool = True) -> ValidationResult:
        """Update multiple configuration values"""
        if validate:
            # Validate all updates first
            validation_result = self.validator.validate_config(updates, auto_fix=False)
            if not validation_result.is_valid:
                return validation_result
        
        with self._config_lock:
            # Apply updates
            for key, value in updates.items():
                self._set_nested_value(self._config, key, value)
            
            # Notify callbacks
            self._notify_change_callbacks()
        
        logger.info(f"Configuration updated with {len(updates)} changes")
        
        result = ValidationResult()
        return result
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
        with self._config_lock:
            self._config = self.schema.get_default_config()
            self._notify_change_callbacks()
        
        logger.info("Configuration reset to defaults")
    
    def validate_current_config(self) -> ValidationResult:
        """Validate current configuration"""
        with self._config_lock:
            return self.validator.validate_config(self._config, auto_fix=False)
    
    def get_system_config(self) -> SystemConfig:
        """Convert to SystemConfig object"""
        with self._config_lock:
            config_dict = self._config
            
            return SystemConfig(
                detection=DetectionConfig(
                    model_path=config_dict.get('detection', {}).get('model_path', 'models/best.pt'),
                    confidence_threshold=config_dict.get('detection', {}).get('confidence_threshold', 0.2),
                    nms_threshold=config_dict.get('detection', {}).get('nms_threshold', 0.5),
                    input_size=tuple(config_dict.get('detection', {}).get('input_size', [640, 640])),
                    device=config_dict.get('detection', {}).get('device', 'cpu')
                ),
                tracking=TrackingConfig(
                    max_disappeared_frames=config_dict.get('tracking', {}).get('max_disappeared_frames', 10),
                    max_tracking_distance=config_dict.get('tracking', {}).get('max_tracking_distance', 50.0),
                    kalman_process_noise=config_dict.get('tracking', {}).get('kalman_process_noise', 0.1),
                    kalman_measurement_noise=config_dict.get('tracking', {}).get('kalman_measurement_noise', 0.1),
                    trajectory_smoothing=config_dict.get('tracking', {}).get('trajectory_smoothing', True)
                ),
                calibration=CalibrationConfig(
                    table_length=config_dict.get('calibration', {}).get('table_length', 3.569),
                    table_width=config_dict.get('calibration', {}).get('table_width', 1.778),
                    auto_recalibrate=config_dict.get('calibration', {}).get('auto_recalibrate', True),
                    calibration_interval=config_dict.get('calibration', {}).get('calibration_interval', 100),
                    corner_detection_threshold=config_dict.get('calibration', {}).get('corner_detection_threshold', 0.1)
                ),
                debug_mode=config_dict.get('system', {}).get('debug_mode', False),
                save_debug_frames=config_dict.get('system', {}).get('save_debug_frames', False),
                output_directory=config_dict.get('system', {}).get('output_directory', 'output')
            )
    
    def create_config_template(self, output_path: Union[str, Path],
                             format: str = 'yaml') -> None:
        """Create configuration template file"""
        defaults = self.schema.get_default_config()
        self.loader.create_config_template(output_path, defaults, format)
    
    def enable_auto_reload(self, check_interval: float = 1.0) -> None:
        """Enable automatic configuration reloading"""
        if self._auto_reload:
            return
        
        self._auto_reload = True
        self._reload_thread = threading.Thread(
            target=self._auto_reload_worker,
            args=(check_interval,),
            daemon=True
        )
        self._reload_thread.start()
        
        logger.info("Auto-reload enabled")
    
    def disable_auto_reload(self) -> None:
        """Disable automatic configuration reloading"""
        self._auto_reload = False
        if self._reload_thread:
            self._reload_thread.join(timeout=2.0)
        
        logger.info("Auto-reload disabled")
    
    def _auto_reload_worker(self, check_interval: float) -> None:
        """Auto-reload worker thread"""
        while self._auto_reload:
            try:
                if self.config_file and self.config_file.exists():
                    current_mtime = self.config_file.stat().st_mtime
                    if current_mtime > self._last_modified:
                        logger.info("Configuration file changed, reloading...")
                        self.load_from_file(self.config_file)
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Auto-reload error: {e}")
                time.sleep(check_interval)
    
    def add_change_callback(self, callback: callable) -> None:
        """Add callback for configuration changes"""
        self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: callable) -> None:
        """Remove configuration change callback"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def _notify_change_callbacks(self) -> None:
        """Notify all change callbacks"""
        for callback in self._change_callbacks:
            try:
                callback(self.get_config())
            except Exception as e:
                logger.error(f"Configuration change callback error: {e}")
    
    def get_field_documentation(self) -> Dict[str, Dict[str, Any]]:
        """Get documentation for all configuration fields"""
        return self.validator.get_all_field_info()
    
    def export_config_documentation(self, output_path: Union[str, Path],
                                  format: str = 'markdown') -> None:
        """Export configuration documentation"""
        field_info = self.get_field_documentation()
        
        if format == 'markdown':
            self._export_markdown_docs(output_path, field_info)
        elif format == 'json':
            self.loader.save_config(field_info, output_path, 'json')
        else:
            raise ValueError(f"Unsupported documentation format: {format}")
    
    def _export_markdown_docs(self, output_path: Union[str, Path],
                            field_info: Dict[str, Dict[str, Any]]) -> None:
        """Export documentation as markdown"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Snooker Detection System Configuration\n\n")
            
            # Group by section
            sections = {}
            for field_name, info in field_info.items():
                section = field_name.split('.')[0]
                if section not in sections:
                    sections[section] = []
                sections[section].append((field_name, info))
            
            for section_name, fields in sections.items():
                f.write(f"## {section_name.title()} Configuration\n\n")
                
                for field_name, info in fields:
                    f.write(f"### {field_name}\n\n")
                    f.write(f"**Description:** {info['description']}\n\n")
                    f.write(f"**Type:** {info['type']}\n\n")
                    f.write(f"**Default:** `{info['default']}`\n\n")
                    f.write(f"**Required:** {info['required']}\n\n")
                    
                    if 'min_value' in info:
                        f.write(f"**Minimum:** {info['min_value']}\n\n")
                    if 'max_value' in info:
                        f.write(f"**Maximum:** {info['max_value']}\n\n")
                    if 'allowed_values' in info:
                        f.write(f"**Allowed Values:** {info['allowed_values']}\n\n")
                    
                    f.write("---\n\n")
        
        logger.info(f"Configuration documentation exported to: {output_path}")
    
    # Utility methods
    
    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy object"""
        import copy
        return copy.deepcopy(obj)
    
    def _get_nested_value(self, config: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get nested dictionary value using dot notation"""
        keys = key.split('.')
        current = config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set nested dictionary value using dot notation"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _apply_fixes(self, config: Dict[str, Any], fixes: Dict[str, Any]) -> Dict[str, Any]:
        """Apply validation fixes to configuration"""
        fixed_config = self._deep_copy(config)
        
        for key, value in fixes.items():
            self._set_nested_value(fixed_config, key, value)
        
        return fixed_config