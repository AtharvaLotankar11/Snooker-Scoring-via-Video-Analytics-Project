#!/usr/bin/env python3
"""
Real-time display for live snooker detection system
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict, Any
import cv2
import numpy as np

from ..core import FrameAnalysis
from .debug_visualizer import DebugVisualizer

logger = logging.getLogger(__name__)

class RealTimeDisplay:
    """Real-time display window for live detection visualization"""
    
    def __init__(self, window_name: str = "Snooker Detection", 
                 window_size: Optional[tuple] = None,
                 enable_controls: bool = True):
        self.window_name = window_name
        self.window_size = window_size
        self.enable_controls = enable_controls
        
        # Display state
        self.is_running = False
        self.display_thread = None
        self.current_frame = None
        self.current_analysis = None
        self.frame_lock = threading.Lock()
        
        # Visualization components
        self.visualizer = DebugVisualizer()
        
        # Display options
        self.show_detections = True
        self.show_tracking = True
        self.show_calibration = True
        self.show_info = True
        self.show_trajectories = True
        
        # Performance monitoring
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.display_fps = 0.0
        
        # Callbacks
        self.key_callbacks: Dict[int, Callable] = {}
        
        # Setup default key bindings
        self._setup_default_keybindings()
    
    def _setup_default_keybindings(self) -> None:
        """Setup default keyboard shortcuts"""
        if not self.enable_controls:
            return
        
        # Toggle options
        self.key_callbacks[ord('d')] = lambda: self._toggle_option('show_detections')
        self.key_callbacks[ord('t')] = lambda: self._toggle_option('show_tracking')
        self.key_callbacks[ord('c')] = lambda: self._toggle_option('show_calibration')
        self.key_callbacks[ord('i')] = lambda: self._toggle_option('show_info')
        self.key_callbacks[ord('r')] = lambda: self._toggle_option('show_trajectories')
        
        # Save screenshot
        self.key_callbacks[ord('s')] = self._save_screenshot
        
        # Reset display
        self.key_callbacks[ord(' ')] = self._reset_display
        
        # Quit
        self.key_callbacks[27] = self.stop  # ESC key
        self.key_callbacks[ord('q')] = self.stop
    
    def start(self) -> bool:
        """Start the real-time display"""
        if self.is_running:
            logger.warning("Display already running")
            return False
        
        try:
            # Create window
            cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
            
            if self.window_size:
                cv2.resizeWindow(self.window_name, *self.window_size)
            
            # Start display thread
            self.is_running = True
            self.display_thread = threading.Thread(
                target=self._display_loop,
                name="RealTimeDisplay",
                daemon=True
            )
            self.display_thread.start()
            
            logger.info(f"Real-time display started: {self.window_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start display: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> None:
        """Stop the real-time display"""
        if not self.is_running:
            return
        
        logger.info("Stopping real-time display...")
        self.is_running = False
        
        # Wait for display thread to finish
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=2.0)
        
        # Destroy window
        try:
            cv2.destroyWindow(self.window_name)
        except:
            pass
        
        logger.info("Real-time display stopped")
    
    def update_frame(self, frame: np.ndarray, analysis: Optional[FrameAnalysis] = None) -> None:
        """Update the display with new frame and analysis"""
        with self.frame_lock:
            self.current_frame = frame.copy()
            self.current_analysis = analysis
    
    def _display_loop(self) -> None:
        """Main display loop running in separate thread"""
        while self.is_running:
            try:
                # Get current frame and analysis
                with self.frame_lock:
                    frame = self.current_frame
                    analysis = self.current_analysis
                
                if frame is not None:
                    # Create visualization
                    vis_frame = self._create_visualization(frame, analysis)
                    
                    # Display frame
                    cv2.imshow(self.window_name, vis_frame)
                    
                    # Update FPS counter
                    self._update_fps_counter()
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key != 255:  # Key pressed
                    self._handle_keypress(key)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Display loop error: {e}")
                break
    
    def _create_visualization(self, frame: np.ndarray, 
                            analysis: Optional[FrameAnalysis]) -> np.ndarray:
        """Create visualization frame"""
        if analysis is None:
            # Just show the frame with basic info
            vis_frame = frame.copy()
            cv2.putText(vis_frame, "No Analysis Data", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return vis_frame
        
        # Use debug visualizer to create comprehensive visualization
        vis_frame = self.visualizer.visualize_frame_analysis(
            frame, analysis,
            show_detections=self.show_detections,
            show_tracking=self.show_tracking,
            show_calibration=self.show_calibration,
            show_info=self.show_info
        )
        
        # Add display-specific overlays
        vis_frame = self._add_display_overlays(vis_frame)
        
        return vis_frame
    
    def _add_display_overlays(self, frame: np.ndarray) -> np.ndarray:
        """Add display-specific overlays"""
        # Add FPS counter
        fps_text = f"Display FPS: {self.display_fps:.1f}"
        cv2.putText(frame, fps_text, (frame.shape[1] - 200, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add control hints if enabled
        if self.enable_controls:
            hints = [
                "Controls:",
                "D - Toggle Detections",
                "T - Toggle Tracking", 
                "C - Toggle Calibration",
                "I - Toggle Info",
                "S - Save Screenshot",
                "Q/ESC - Quit"
            ]
            
            for i, hint in enumerate(hints):
                y_pos = frame.shape[0] - (len(hints) - i) * 20
                cv2.putText(frame, hint, (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame
    
    def _update_fps_counter(self) -> None:
        """Update FPS counter"""
        self.fps_counter += 1
        
        if self.fps_counter >= 30:  # Update every 30 frames
            current_time = time.time()
            elapsed = current_time - self.fps_start_time
            
            if elapsed > 0:
                self.display_fps = self.fps_counter / elapsed
            
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def _handle_keypress(self, key: int) -> None:
        """Handle keyboard input"""
        if key in self.key_callbacks:
            try:
                self.key_callbacks[key]()
            except Exception as e:
                logger.error(f"Key callback error: {e}")
    
    def _toggle_option(self, option_name: str) -> None:
        """Toggle display option"""
        if hasattr(self, option_name):
            current_value = getattr(self, option_name)
            setattr(self, option_name, not current_value)
            logger.info(f"Toggled {option_name}: {not current_value}")
    
    def _save_screenshot(self) -> None:
        """Save current frame as screenshot"""
        with self.frame_lock:
            if self.current_frame is not None:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.jpg"
                
                # Create visualization for screenshot
                if self.current_analysis:
                    screenshot = self._create_visualization(self.current_frame, self.current_analysis)
                else:
                    screenshot = self.current_frame.copy()
                
                cv2.imwrite(filename, screenshot)
                logger.info(f"Screenshot saved: {filename}")
    
    def _reset_display(self) -> None:
        """Reset display options to defaults"""
        self.show_detections = True
        self.show_tracking = True
        self.show_calibration = True
        self.show_info = True
        self.show_trajectories = True
        logger.info("Display options reset to defaults")
    
    def add_key_callback(self, key: int, callback: Callable) -> None:
        """Add custom key callback"""
        self.key_callbacks[key] = callback
        logger.info(f"Added key callback for key: {key}")
    
    def set_visualization_options(self, **options) -> None:
        """Set multiple visualization options"""
        for option, value in options.items():
            if hasattr(self, option):
                setattr(self, option, value)
                logger.debug(f"Set {option} = {value}")
    
    def get_display_stats(self) -> Dict[str, Any]:
        """Get display statistics"""
        return {
            "is_running": self.is_running,
            "display_fps": self.display_fps,
            "window_name": self.window_name,
            "visualization_options": {
                "show_detections": self.show_detections,
                "show_tracking": self.show_tracking,
                "show_calibration": self.show_calibration,
                "show_info": self.show_info,
                "show_trajectories": self.show_trajectories
            }
        }