#!/usr/bin/env python3
"""
Specific recovery strategies for different system components
"""

import logging
import time
from typing import Dict, Any, Optional
import numpy as np

from .error_handling import RecoveryStrategy, ErrorEvent
from .data_models import CalibrationData, Point, BoundingBox

logger = logging.getLogger(__name__)

class ModelReloadStrategy(RecoveryStrategy):
    """Recovery strategy for model loading failures"""
    
    def __init__(self, detection_engine=None):
        super().__init__("model_reload", max_attempts=3)
        self.detection_engine = detection_engine
        self.fallback_model_path = "yolov8s.pt"  # Pre-trained fallback
    
    def _execute_recovery(self, error_event: ErrorEvent, context: Dict[str, Any]) -> bool:
        """Attempt to reload the model or use fallback"""
        if not self.detection_engine:
            return False
        
        try:
            # First, try reloading the original model
            original_model = context.get("model_path")
            if original_model and self.attempt_count == 1:
                logger.info(f"Attempting to reload original model: {original_model}")
                if self.detection_engine.load_model(original_model):
                    return True
            
            # If original fails, try fallback model
            logger.info(f"Attempting to load fallback model: {self.fallback_model_path}")
            if self.detection_engine.load_model(self.fallback_model_path):
                logger.warning("Using fallback model - detection accuracy may be reduced")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Model reload recovery failed: {e}")
            return False

class CalibrationRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for calibration failures"""
    
    def __init__(self, calibration_engine=None):
        super().__init__("calibration_recovery", max_attempts=5)
        self.calibration_engine = calibration_engine
    
    def _execute_recovery(self, error_event: ErrorEvent, context: Dict[str, Any]) -> bool:
        """Attempt calibration recovery"""
        if not self.calibration_engine:
            return False
        
        try:
            # Strategy 1: Try loading cached calibration
            if self.attempt_count <= 2:
                logger.info("Attempting to recover calibration from cache")
                if hasattr(self.calibration_engine, '_load_cached_calibration'):
                    if self.calibration_engine._load_cached_calibration():
                        return True
            
            # Strategy 2: Try recovery manager if available
            if self.attempt_count <= 3:
                logger.info("Attempting calibration recovery using recovery manager")
                if hasattr(self.calibration_engine, '_attempt_calibration_recovery'):
                    video_source = context.get("video_source", "")
                    if self.calibration_engine._attempt_calibration_recovery(video_source):
                        return True
            
            # Strategy 3: Force recalibration
            if self.attempt_count <= 4:
                logger.info("Forcing calibration reset for fresh attempt")
                if hasattr(self.calibration_engine, 'reset_calibration'):
                    self.calibration_engine.reset_calibration()
                    return True  # Reset successful, next frame will attempt calibration
            
            return False
            
        except Exception as e:
            logger.error(f"Calibration recovery failed: {e}")
            return False

class TrackingResetStrategy(RecoveryStrategy):
    """Recovery strategy for tracking failures"""
    
    def __init__(self, tracker=None):
        super().__init__("tracking_reset", max_attempts=2)
        self.tracker = tracker
    
    def _execute_recovery(self, error_event: ErrorEvent, context: Dict[str, Any]) -> bool:
        """Reset tracking system"""
        if not self.tracker:
            return False
        
        try:
            logger.info("Resetting tracking system")
            
            # Reset all tracks
            if hasattr(self.tracker, 'reset_tracking'):
                self.tracker.reset_tracking()
            
            # Reinitialize with current detections if available
            current_detections = context.get("detections", [])
            if current_detections and hasattr(self.tracker, 'update'):
                frame_number = context.get("frame_number", 0)
                self.tracker.update(current_detections, frame_number)
            
            return True
            
        except Exception as e:
            logger.error(f"Tracking reset recovery failed: {e}")
            return False

class VideoInputRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for video input failures"""
    
    def __init__(self, video_handler=None):
        super().__init__("video_input_recovery", max_attempts=3)
        self.video_handler = video_handler
    
    def _execute_recovery(self, error_event: ErrorEvent, context: Dict[str, Any]) -> bool:
        """Attempt to recover video input"""
        if not self.video_handler:
            return False
        
        try:
            video_source = context.get("video_source")
            if not video_source:
                return False
            
            logger.info(f"Attempting to recover video input: {video_source}")
            
            # Release current connection
            if hasattr(self.video_handler, 'release'):
                self.video_handler.release()
            
            # Wait a moment before reconnecting
            time.sleep(1.0)
            
            # Attempt to reopen
            if hasattr(self.video_handler, 'open_source'):
                return self.video_handler.open_source(video_source)
            
            return False
            
        except Exception as e:
            logger.error(f"Video input recovery failed: {e}")
            return False

class GracefulDegradationStrategy(RecoveryStrategy):
    """Strategy for graceful degradation when recovery fails"""
    
    def __init__(self, component_name: str):
        super().__init__(f"graceful_degradation_{component_name}", max_attempts=1)
        self.component_name = component_name
    
    def _execute_recovery(self, error_event: ErrorEvent, context: Dict[str, Any]) -> bool:
        """Enable graceful degradation mode"""
        try:
            logger.warning(f"Enabling graceful degradation for {self.component_name}")
            
            # Set degradation flags in context
            degradation_context = context.get("degradation_context", {})
            degradation_context[f"{self.component_name}_degraded"] = True
            degradation_context[f"{self.component_name}_degradation_time"] = time.time()
            
            # Adjust system behavior based on component
            if self.component_name == "detection":
                # Continue with empty detections
                degradation_context["use_empty_detections"] = True
                
            elif self.component_name == "calibration":
                # Use default/identity transformation
                degradation_context["use_default_calibration"] = True
                
            elif self.component_name == "tracking":
                # Use detection-only mode
                degradation_context["detection_only_mode"] = True
            
            context["degradation_context"] = degradation_context
            
            logger.info(f"Graceful degradation enabled for {self.component_name}")
            return True
            
        except Exception as e:
            logger.error(f"Graceful degradation setup failed: {e}")
            return False

class FrameSkipStrategy(RecoveryStrategy):
    """Strategy to skip problematic frames"""
    
    def __init__(self, max_skip_frames: int = 5):
        super().__init__("frame_skip", max_attempts=1)
        self.max_skip_frames = max_skip_frames
        self.skipped_frames = 0
    
    def _execute_recovery(self, error_event: ErrorEvent, context: Dict[str, Any]) -> bool:
        """Skip current frame and continue processing"""
        try:
            if self.skipped_frames >= self.max_skip_frames:
                logger.warning(f"Maximum frame skip limit reached ({self.max_skip_frames})")
                return False
            
            self.skipped_frames += 1
            frame_number = context.get("frame_number", 0)
            
            logger.info(f"Skipping problematic frame {frame_number} (skip count: {self.skipped_frames})")
            
            # Signal to skip this frame
            context["skip_frame"] = True
            
            return True
            
        except Exception as e:
            logger.error(f"Frame skip strategy failed: {e}")
            return False
    
    def reset(self) -> None:
        """Reset strategy state"""
        super().reset()
        self.skipped_frames = 0

class ComponentRestartStrategy(RecoveryStrategy):
    """Strategy to restart individual components"""
    
    def __init__(self, component_name: str, restart_function=None):
        super().__init__(f"restart_{component_name}", max_attempts=2)
        self.component_name = component_name
        self.restart_function = restart_function
    
    def _execute_recovery(self, error_event: ErrorEvent, context: Dict[str, Any]) -> bool:
        """Restart the component"""
        try:
            logger.info(f"Attempting to restart component: {self.component_name}")
            
            if self.restart_function:
                return self.restart_function(context)
            
            # Generic restart logic
            component = context.get(self.component_name)
            if component:
                # Try to reinitialize if method exists
                if hasattr(component, 'initialize') or hasattr(component, 'reset'):
                    init_method = getattr(component, 'initialize', None) or getattr(component, 'reset')
                    init_method()
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Component restart failed for {self.component_name}: {e}")
            return False

class MemoryCleanupStrategy(RecoveryStrategy):
    """Strategy to clean up memory and resources"""
    
    def __init__(self):
        super().__init__("memory_cleanup", max_attempts=1)
    
    def _execute_recovery(self, error_event: ErrorEvent, context: Dict[str, Any]) -> bool:
        """Perform memory cleanup"""
        try:
            logger.info("Performing memory cleanup")
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear any large data structures in context
            cleanup_keys = ["frame_buffer", "trajectory_history", "detection_cache"]
            for key in cleanup_keys:
                if key in context:
                    del context[key]
                    logger.debug(f"Cleared {key} from context")
            
            # Clear numpy cache if available
            try:
                np.clear_cache = getattr(np, 'clear_cache', None)
                if np.clear_cache:
                    np.clear_cache()
            except:
                pass
            
            logger.info("Memory cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            return False