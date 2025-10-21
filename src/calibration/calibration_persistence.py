#!/usr/bin/env python3
"""
Calibration Persistence Manager for saving and loading calibration data
"""

import json
import logging
import os
import pickle
import time
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

from ..core import CalibrationData, Point, BoundingBox

logger = logging.getLogger(__name__)

class CalibrationPersistenceManager:
    """Manages saving and loading of calibration data"""
    
    def __init__(self, cache_directory: str = "cache/calibration"):
        self.cache_directory = Path(cache_directory)
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.calibration_file = self.cache_directory / "calibration_data.pkl"
        self.metadata_file = self.cache_directory / "calibration_metadata.json"
        self.backup_directory = self.cache_directory / "backups"
        self.backup_directory.mkdir(exist_ok=True)
        
        # Cache settings
        self.max_cache_age_hours = 24  # Maximum age before cache is considered stale
        self.max_backups = 5  # Maximum number of backup files to keep
        
        logger.info(f"Calibration persistence initialized: {self.cache_directory}")
    
    def save_calibration_data(self, calibration_data: CalibrationData, 
                            video_source: str = "", frame_number: int = 0) -> bool:
        """Save calibration data to cache"""
        try:
            # Create backup of existing data
            if self.calibration_file.exists():
                self._create_backup()
            
            # Prepare data for serialization
            serializable_data = self._prepare_for_serialization(calibration_data)
            
            # Save binary data (numpy arrays)
            with open(self.calibration_file, 'wb') as f:
                pickle.dump(serializable_data, f)
            
            # Save metadata
            metadata = {
                "timestamp": time.time(),
                "video_source": video_source,
                "frame_number": frame_number,
                "table_dimensions": calibration_data.table_dimensions,
                "corners_count": len(calibration_data.table_corners),
                "pockets_count": len(calibration_data.pocket_regions),
                "is_valid": calibration_data.is_valid,
                "calibration_timestamp": calibration_data.calibration_timestamp
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Calibration data saved successfully for {video_source}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save calibration data: {e}")
            return False
    
    def load_calibration_data(self, max_age_hours: Optional[float] = None) -> Optional[CalibrationData]:
        """Load calibration data from cache"""
        try:
            if not self.calibration_file.exists() or not self.metadata_file.exists():
                logger.debug("No cached calibration data found")
                return None
            
            # Check metadata first
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if cache is too old
            cache_age_hours = (time.time() - metadata["timestamp"]) / 3600
            max_age = max_age_hours if max_age_hours is not None else self.max_cache_age_hours
            
            if cache_age_hours > max_age:
                logger.info(f"Cached calibration data is too old ({cache_age_hours:.1f}h > {max_age}h)")
                return None
            
            # Load binary data
            with open(self.calibration_file, 'rb') as f:
                serializable_data = pickle.load(f)
            
            # Reconstruct CalibrationData object
            calibration_data = self._reconstruct_from_serialization(serializable_data)
            
            logger.info(f"Loaded cached calibration data (age: {cache_age_hours:.1f}h)")
            return calibration_data
            
        except Exception as e:
            logger.error(f"Failed to load calibration data: {e}")
            return None
    
    def is_cache_valid(self, max_age_hours: Optional[float] = None) -> bool:
        """Check if cached calibration data is valid and not too old"""
        try:
            if not self.metadata_file.exists():
                return False
            
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check age
            cache_age_hours = (time.time() - metadata["timestamp"]) / 3600
            max_age = max_age_hours if max_age_hours is not None else self.max_cache_age_hours
            
            if cache_age_hours > max_age:
                return False
            
            # Check validity
            return metadata.get("is_valid", False)
            
        except Exception as e:
            logger.error(f"Error checking cache validity: {e}")
            return False
    
    def get_cache_metadata(self) -> Optional[Dict[str, Any]]:
        """Get metadata about cached calibration data"""
        try:
            if not self.metadata_file.exists():
                return None
            
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Add computed fields
            cache_age_hours = (time.time() - metadata["timestamp"]) / 3600
            metadata["cache_age_hours"] = cache_age_hours
            metadata["is_cache_valid"] = cache_age_hours <= self.max_cache_age_hours
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error reading cache metadata: {e}")
            return None
    
    def clear_cache(self) -> bool:
        """Clear all cached calibration data"""
        try:
            files_removed = 0
            
            if self.calibration_file.exists():
                self.calibration_file.unlink()
                files_removed += 1
            
            if self.metadata_file.exists():
                self.metadata_file.unlink()
                files_removed += 1
            
            # Clear backups
            for backup_file in self.backup_directory.glob("*.pkl"):
                backup_file.unlink()
                files_removed += 1
            
            for backup_file in self.backup_directory.glob("*.json"):
                backup_file.unlink()
                files_removed += 1
            
            logger.info(f"Cleared calibration cache ({files_removed} files removed)")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def _prepare_for_serialization(self, calibration_data: CalibrationData) -> Dict[str, Any]:
        """Prepare CalibrationData for serialization"""
        return {
            "homography_matrix": calibration_data.homography_matrix,
            "table_corners": [(p.x, p.y) for p in calibration_data.table_corners],
            "table_dimensions": calibration_data.table_dimensions,
            "pocket_regions": [(bb.x1, bb.y1, bb.x2, bb.y2) for bb in calibration_data.pocket_regions],
            "calibration_timestamp": calibration_data.calibration_timestamp,
            "is_valid": calibration_data.is_valid
        }
    
    def _reconstruct_from_serialization(self, data: Dict[str, Any]) -> CalibrationData:
        """Reconstruct CalibrationData from serialized data"""
        return CalibrationData(
            homography_matrix=data["homography_matrix"],
            table_corners=[Point(x, y) for x, y in data["table_corners"]],
            table_dimensions=data["table_dimensions"],
            pocket_regions=[BoundingBox(x1, y1, x2, y2) for x1, y1, x2, y2 in data["pocket_regions"]],
            calibration_timestamp=data["calibration_timestamp"],
            is_valid=data["is_valid"]
        )
    
    def _create_backup(self) -> None:
        """Create backup of existing calibration data"""
        try:
            timestamp = int(time.time())
            backup_cal_file = self.backup_directory / f"calibration_data_{timestamp}.pkl"
            backup_meta_file = self.backup_directory / f"calibration_metadata_{timestamp}.json"
            
            # Copy files
            if self.calibration_file.exists():
                import shutil
                shutil.copy2(self.calibration_file, backup_cal_file)
            
            if self.metadata_file.exists():
                import shutil
                shutil.copy2(self.metadata_file, backup_meta_file)
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            logger.debug(f"Created calibration backup: {timestamp}")
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self) -> None:
        """Remove old backup files, keeping only the most recent ones"""
        try:
            # Get all backup files
            backup_files = list(self.backup_directory.glob("calibration_data_*.pkl"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            for old_backup in backup_files[self.max_backups:]:
                old_backup.unlink()
                # Also remove corresponding metadata file
                timestamp = old_backup.stem.split('_')[-1]
                meta_file = self.backup_directory / f"calibration_metadata_{timestamp}.json"
                if meta_file.exists():
                    meta_file.unlink()
            
        except Exception as e:
            logger.warning(f"Error cleaning up old backups: {e}")


class CalibrationRecoveryManager:
    """Manages calibration recovery strategies"""
    
    def __init__(self, persistence_manager: CalibrationPersistenceManager):
        self.persistence_manager = persistence_manager
        self.recovery_strategies = [
            self._recover_from_cache,
            self._recover_from_backup,
            self._recover_with_default_parameters
        ]
        
    def recover_calibration(self, video_source: str = "", 
                          max_cache_age_hours: float = 24) -> Optional[CalibrationData]:
        """Attempt to recover calibration data using various strategies"""
        logger.info("Attempting calibration recovery...")
        
        for i, strategy in enumerate(self.recovery_strategies):
            try:
                calibration_data = strategy(video_source, max_cache_age_hours)
                if calibration_data and calibration_data.is_calibrated():
                    logger.info(f"Calibration recovered using strategy {i+1}")
                    return calibration_data
            except Exception as e:
                logger.warning(f"Recovery strategy {i+1} failed: {e}")
        
        logger.warning("All calibration recovery strategies failed")
        return None
    
    def _recover_from_cache(self, video_source: str, max_cache_age_hours: float) -> Optional[CalibrationData]:
        """Strategy 1: Recover from recent cache"""
        return self.persistence_manager.load_calibration_data(max_cache_age_hours)
    
    def _recover_from_backup(self, video_source: str, max_cache_age_hours: float) -> Optional[CalibrationData]:
        """Strategy 2: Recover from backup files"""
        try:
            backup_files = list(self.persistence_manager.backup_directory.glob("calibration_data_*.pkl"))
            if not backup_files:
                return None
            
            # Try most recent backup first
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for backup_file in backup_files:
                try:
                    with open(backup_file, 'rb') as f:
                        serializable_data = pickle.load(f)
                    
                    calibration_data = self.persistence_manager._reconstruct_from_serialization(serializable_data)
                    
                    if calibration_data.is_calibrated():
                        logger.info(f"Recovered calibration from backup: {backup_file.name}")
                        return calibration_data
                        
                except Exception as e:
                    logger.warning(f"Failed to load backup {backup_file.name}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Backup recovery failed: {e}")
            return None
    
    def _recover_with_default_parameters(self, video_source: str, max_cache_age_hours: float) -> Optional[CalibrationData]:
        """Strategy 3: Create default calibration parameters"""
        try:
            # This creates a basic calibration that can be used as a fallback
            # In practice, this might use standard table dimensions and camera positions
            logger.info("Creating default calibration parameters")
            
            # Standard snooker table corners (normalized coordinates that need to be scaled)
            # This is a fallback - real implementation would need actual frame dimensions
            default_corners = [
                Point(100, 100),    # Top-left
                Point(700, 100),    # Top-right  
                Point(700, 400),    # Bottom-right
                Point(100, 400)     # Bottom-left
            ]
            
            # Create basic homography (identity-like transformation)
            homography = np.array([
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]
            ], dtype=np.float32)
            
            # Basic pocket regions
            pocket_regions = [
                BoundingBox(90, 90, 110, 110),      # Top-left
                BoundingBox(390, 90, 410, 110),     # Top-middle
                BoundingBox(690, 90, 710, 110),     # Top-right
                BoundingBox(90, 390, 110, 410),     # Bottom-left
                BoundingBox(390, 390, 410, 410),    # Bottom-middle
                BoundingBox(690, 390, 710, 410)     # Bottom-right
            ]
            
            calibration_data = CalibrationData(
                homography_matrix=homography,
                table_corners=default_corners,
                table_dimensions=(3.569, 1.778),  # Standard snooker table
                pocket_regions=pocket_regions,
                calibration_timestamp=time.time(),
                is_valid=False  # Mark as invalid since it's just a fallback
            )
            
            logger.warning("Using default calibration parameters - accuracy may be reduced")
            return calibration_data
            
        except Exception as e:
            logger.error(f"Default parameter recovery failed: {e}")
            return None