#!/usr/bin/env python3
"""
Configuration loading and saving utilities
"""

import json
import logging
import os
from typing import Dict, Any, Optional, Union
from pathlib import Path

# Optional YAML import
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Configuration file loader supporting multiple formats"""
    
    def __init__(self):
        self.supported_formats = {'.json'}
        if HAS_YAML:
            self.supported_formats.update({'.yaml', '.yml'})
    
    def load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from file"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        if config_path.suffix not in self.supported_formats:
            raise ValueError(f"Unsupported config format: {config_path.suffix}. "
                           f"Supported formats: {self.supported_formats}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix == '.json':
                    config = json.load(f)
                elif config_path.suffix in {'.yaml', '.yml'}:
                    if not HAS_YAML:
                        raise ValueError("YAML support not available - install PyYAML")
                    config = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported format: {config_path.suffix}")
            
            logger.info(f"Configuration loaded from: {config_path}")
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config file: {e}")
    
    def save_config(self, config: Dict[str, Any], 
                   config_path: Union[str, Path],
                   format: Optional[str] = None) -> None:
        """Save configuration to file"""
        config_path = Path(config_path)
        
        # Determine format from extension or parameter
        if format:
            if not format.startswith('.'):
                format = f'.{format}'
        else:
            format = config_path.suffix
        
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported config format: {format}")
        
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if format == '.json':
                    json.dump(config, f, indent=2, default=str)
                elif format in {'.yaml', '.yml'}:
                    if not HAS_YAML:
                        raise ValueError("YAML support not available - install PyYAML")
                    yaml.dump(config, f, default_flow_style=False, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Configuration saved to: {config_path}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to save config file: {e}")
    
    def load_multiple_configs(self, config_paths: list[Union[str, Path]]) -> Dict[str, Any]:
        """Load and merge multiple configuration files"""
        merged_config = {}
        
        for config_path in config_paths:
            try:
                config = self.load_config(config_path)
                merged_config = self._deep_merge(merged_config, config)
                logger.debug(f"Merged config from: {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config {config_path}: {e}")
        
        return merged_config
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def create_config_template(self, output_path: Union[str, Path],
                             schema_defaults: Dict[str, Any],
                             format: str = 'yaml') -> None:
        """Create configuration template file with comments"""
        config_path = Path(output_path)
        
        if format == 'yaml':
            self._create_yaml_template(config_path, schema_defaults)
        elif format == 'json':
            self._create_json_template(config_path, schema_defaults)
        else:
            raise ValueError(f"Template creation not supported for format: {format}")
    
    def _create_yaml_template(self, config_path: Path, 
                            schema_defaults: Dict[str, Any]) -> None:
        """Create YAML configuration template with comments"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("# Snooker Detection System Configuration\n")
            f.write("# Generated configuration template\n\n")
            
            # Write sections
            sections = {
                'detection': 'Ball Detection Configuration',
                'tracking': 'Ball Tracking Configuration', 
                'calibration': 'Table Calibration Configuration',
                'system': 'System Configuration',
                'performance': 'Performance Configuration',
                'visualization': 'Visualization Configuration'
            }
            
            for section_name, section_desc in sections.items():
                if section_name in schema_defaults:
                    f.write(f"# {section_desc}\n")
                    f.write(f"{section_name}:\n")
                    
                    section_data = schema_defaults[section_name]
                    for key, value in section_data.items():
                        f.write(f"  {key}: {self._format_yaml_value(value)}\n")
                    
                    f.write("\n")
        
        logger.info(f"Configuration template created: {config_path}")
    
    def _create_json_template(self, config_path: Path,
                            schema_defaults: Dict[str, Any]) -> None:
        """Create JSON configuration template"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(schema_defaults, f, indent=2, default=str)
        
        logger.info(f"Configuration template created: {config_path}")
    
    def _format_yaml_value(self, value: Any) -> str:
        """Format value for YAML output"""
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, list):
            return str(value)
        else:
            return str(value)
    
    def backup_config(self, config_path: Union[str, Path],
                     backup_dir: Optional[Union[str, Path]] = None) -> Path:
        """Create backup of configuration file"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        # Determine backup location
        if backup_dir:
            backup_dir = Path(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"{config_path.stem}_backup{config_path.suffix}"
        else:
            backup_path = config_path.with_name(f"{config_path.stem}_backup{config_path.suffix}")
        
        # Copy file
        import shutil
        shutil.copy2(config_path, backup_path)
        
        logger.info(f"Configuration backed up to: {backup_path}")
        return backup_path
    
    def validate_file_format(self, config_path: Union[str, Path]) -> bool:
        """Validate configuration file format without loading"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            return False
        
        if config_path.suffix not in self.supported_formats:
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix == '.json':
                    json.load(f)
                elif config_path.suffix in {'.yaml', '.yml'}:
                    yaml.safe_load(f)
            return True
        except:
            return False