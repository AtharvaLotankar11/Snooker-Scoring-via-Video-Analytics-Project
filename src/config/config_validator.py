#!/usr/bin/env python3
"""
Configuration validation utilities
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from .config_schema import ConfigSchema, ConfigField

logger = logging.getLogger(__name__)

class ValidationResult:
    """Result of configuration validation"""
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.fixed_values: Dict[str, Any] = {}
    
    def add_error(self, message: str) -> None:
        """Add validation error"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add validation warning"""
        self.warnings.append(message)
    
    def add_fix(self, field_name: str, old_value: Any, new_value: Any) -> None:
        """Add automatic fix"""
        self.fixed_values[field_name] = new_value
        self.add_warning(f"Fixed '{field_name}': {old_value} -> {new_value}")
    
    def get_summary(self) -> str:
        """Get validation summary"""
        summary = []
        
        if self.is_valid:
            summary.append("✅ Configuration is valid")
        else:
            summary.append(f"❌ Configuration has {len(self.errors)} error(s)")
        
        if self.warnings:
            summary.append(f"⚠️ {len(self.warnings)} warning(s)")
        
        if self.fixed_values:
            summary.append(f"🔧 {len(self.fixed_values)} value(s) auto-fixed")
        
        return " | ".join(summary)

class ConfigValidator:
    """Configuration validator using schema definitions"""
    
    def __init__(self, schema: Optional[ConfigSchema] = None):
        self.schema = schema or ConfigSchema()
    
    def validate_config(self, config: Dict[str, Any], 
                       auto_fix: bool = True) -> ValidationResult:
        """Validate complete configuration"""
        result = ValidationResult()
        
        # Flatten config for validation
        flat_config = self._flatten_dict(config)
        
        # Validate each field in schema
        for field_name, field_def in self.schema.get_all_fields().items():
            value = flat_config.get(field_name)
            
            # Validate field
            field_result = self._validate_field(field_def, value, auto_fix)
            
            # Merge results
            if not field_result.is_valid:
                result.add_error(f"Field '{field_name}': {field_result.errors[0]}")
            
            for warning in field_result.warnings:
                result.add_warning(f"Field '{field_name}': {warning}")
            
            if field_result.fixed_values:
                result.fixed_values[field_name] = field_result.fixed_values[field_name]
        
        # Check for unknown fields
        schema_fields = set(self.schema.get_all_fields().keys())
        config_fields = set(flat_config.keys())
        unknown_fields = config_fields - schema_fields
        
        for unknown_field in unknown_fields:
            result.add_warning(f"Unknown configuration field: '{unknown_field}'")
        
        # Check for missing required fields
        for field_name, field_def in self.schema.get_all_fields().items():
            if field_def.required and field_name not in flat_config:
                if auto_fix:
                    result.add_fix(field_name, None, field_def.default)
                else:
                    result.add_error(f"Required field missing: '{field_name}'")
        
        return result
    
    def _validate_field(self, field_def: ConfigField, value: Any, 
                       auto_fix: bool) -> ValidationResult:
        """Validate individual field"""
        result = ValidationResult()
        
        # Use default if value is None and field is required
        if value is None and field_def.required:
            if auto_fix:
                result.add_fix(field_def.name, None, field_def.default)
                value = field_def.default
            else:
                result.add_error("Field is required but not provided")
                return result
        
        # Skip validation if value is None and field is optional
        if value is None and not field_def.required:
            return result
        
        # Validate using field definition
        is_valid, error_message = field_def.validate(value)
        
        if not is_valid:
            if auto_fix and hasattr(self, f'_fix_{field_def.type.value}'):
                # Try to auto-fix the value
                fix_func = getattr(self, f'_fix_{field_def.type.value}')
                try:
                    fixed_value = fix_func(value, field_def)
                    if fixed_value != value:
                        result.add_fix(field_def.name, value, fixed_value)
                        # Re-validate fixed value
                        is_valid, _ = field_def.validate(fixed_value)
                        if not is_valid:
                            result.add_error(error_message)
                    else:
                        result.add_error(error_message)
                except Exception as e:
                    result.add_error(f"{error_message} (auto-fix failed: {e})")
            else:
                result.add_error(error_message)
        
        return result
    
    def _fix_float(self, value: Any, field_def: ConfigField) -> Any:
        """Auto-fix float values"""
        try:
            fixed_value = float(value)
            
            # Clamp to valid range
            if field_def.min_value is not None:
                fixed_value = max(fixed_value, field_def.min_value)
            if field_def.max_value is not None:
                fixed_value = min(fixed_value, field_def.max_value)
            
            return fixed_value
        except (ValueError, TypeError):
            return field_def.default
    
    def _fix_integer(self, value: Any, field_def: ConfigField) -> Any:
        """Auto-fix integer values"""
        try:
            fixed_value = int(float(value))  # Handle string numbers
            
            # Clamp to valid range
            if field_def.min_value is not None:
                fixed_value = max(fixed_value, int(field_def.min_value))
            if field_def.max_value is not None:
                fixed_value = min(fixed_value, int(field_def.max_value))
            
            return fixed_value
        except (ValueError, TypeError):
            return field_def.default
    
    def _fix_boolean(self, value: Any, field_def: ConfigField) -> Any:
        """Auto-fix boolean values"""
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        elif isinstance(value, (int, float)):
            return bool(value)
        else:
            return field_def.default
    
    def _fix_string(self, value: Any, field_def: ConfigField) -> Any:
        """Auto-fix string values"""
        try:
            return str(value)
        except:
            return field_def.default
    
    def _fix_list(self, value: Any, field_def: ConfigField) -> Any:
        """Auto-fix list values"""
        if isinstance(value, str):
            # Try to parse comma-separated values
            try:
                return [item.strip() for item in value.split(',')]
            except:
                return field_def.default
        elif not isinstance(value, list):
            return field_def.default
        return value
    
    def _fix_enum(self, value: Any, field_def: ConfigField) -> Any:
        """Auto-fix enum values"""
        if field_def.allowed_values and value not in field_def.allowed_values:
            # Try case-insensitive match
            value_lower = str(value).lower()
            for allowed in field_def.allowed_values:
                if str(allowed).lower() == value_lower:
                    return allowed
            
            # Return default if no match
            return field_def.default
        
        return value
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', 
                     sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary using dot notation"""
        items = []
        
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    def validate_field_value(self, field_name: str, value: Any) -> ValidationResult:
        """Validate single field value"""
        field_def = self.schema.get_field(field_name)
        
        if not field_def:
            result = ValidationResult()
            result.add_error(f"Unknown field: '{field_name}'")
            return result
        
        return self._validate_field(field_def, value, auto_fix=False)
    
    def get_field_info(self, field_name: str) -> Optional[Dict[str, Any]]:
        """Get field information for documentation"""
        field_def = self.schema.get_field(field_name)
        
        if not field_def:
            return None
        
        info = {
            'name': field_def.name,
            'type': field_def.type.value,
            'default': field_def.default,
            'description': field_def.description,
            'required': field_def.required
        }
        
        if field_def.min_value is not None:
            info['min_value'] = field_def.min_value
        if field_def.max_value is not None:
            info['max_value'] = field_def.max_value
        if field_def.allowed_values:
            info['allowed_values'] = field_def.allowed_values
        
        return info
    
    def get_all_field_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all fields"""
        return {
            name: self.get_field_info(name)
            for name in self.schema.get_all_fields().keys()
        }