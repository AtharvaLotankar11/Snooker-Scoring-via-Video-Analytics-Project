#!/usr/bin/env python3
"""
Video input handling for different video sources
"""

import logging
import os
from typing import Tuple, Optional, Union
import numpy as np
import cv2

from ..core import IVideoInputHandler

logger = logging.getLogger(__name__)

class VideoInputHandler(IVideoInputHandler):
    """Handles video input from files, cameras, and streams"""
    
    def __init__(self):
        self.cap = None
        self.source_type = None
        self.source_path = None
        self.frame_count = 0
        self.fps = 30.0
        self.current_frame = 0
        
        # Video properties
        self.width = 0
        self.height = 0
        self.total_frames = 0
        
    def open_source(self, source: Union[str, int]) -> bool:
        """Open video source (file path, camera index, or stream URL)"""
        try:
            # Release any existing capture
            if self.cap is not None:
                self.cap.release()
            
            # Determine source type
            if isinstance(source, int):
                # Camera index
                self.source_type = "camera"
                self.source_path = f"camera_{source}"
                logger.info(f"Opening camera {source}")
            elif isinstance(source, str):
                if source.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
                    # Network stream
                    self.source_type = "stream"
                    self.source_path = source
                    logger.info(f"Opening network stream: {source}")
                elif os.path.isfile(source):
                    # Video file
                    self.source_type = "file"
                    self.source_path = source
                    logger.info(f"Opening video file: {source}")
                else:
                    logger.error(f"Source not found: {source}")
                    return False
            else:
                logger.error(f"Invalid source type: {type(source)}")
                return False
            
            # Open video capture
            self.cap = cv2.VideoCapture(source)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open video source: {source}")
                return False
            
            # Get video properties
            self._update_video_properties()
            
            logger.info(f"✅ Video source opened successfully")
            logger.info(f"   Resolution: {self.width}x{self.height}")
            logger.info(f"   FPS: {self.fps}")
            if self.source_type == "file":
                logger.info(f"   Total frames: {self.total_frames}")
                logger.info(f"   Duration: {self.total_frames/self.fps:.1f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to open video source: {e}")
            return False
    
    def _update_video_properties(self) -> None:
        """Update video properties from capture object"""
        if self.cap is None:
            return
        
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # For video files, get total frame count
        if self.source_type == "file":
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        else:
            self.total_frames = -1  # Unknown for live sources
        
        # Ensure reasonable FPS value
        if self.fps <= 0 or self.fps > 1000:
            self.fps = 30.0
            logger.warning(f"Invalid FPS detected, using default: {self.fps}")
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read next frame from video source"""
        if self.cap is None or not self.cap.isOpened():
            return False, None
        
        try:
            ret, frame = self.cap.read()
            
            if ret:
                self.current_frame += 1
                
                # Validate frame
                if frame is None or frame.size == 0:
                    logger.warning("Received empty frame")
                    return False, None
                
                # Ensure frame is in correct format
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    # BGR format is expected
                    return True, frame
                elif len(frame.shape) == 2:
                    # Grayscale - convert to BGR
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    return True, frame_bgr
                else:
                    logger.warning(f"Unexpected frame format: {frame.shape}")
                    return False, None
            else:
                # End of video or read error
                if self.source_type == "file":
                    logger.info("Reached end of video file")
                else:
                    logger.warning("Failed to read frame from live source")
                return False, None
                
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return False, None
    
    def is_opened(self) -> bool:
        """Check if video source is opened"""
        return self.cap is not None and self.cap.isOpened()
    
    def release(self) -> None:
        """Release video source"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        logger.info(f"Video source released: {self.source_path}")
        
        # Reset properties
        self.source_type = None
        self.source_path = None
        self.current_frame = 0
    
    def get_frame_count(self) -> int:
        """Get total frame count (for video files)"""
        return self.total_frames if self.total_frames > 0 else -1
    
    def get_fps(self) -> float:
        """Get frames per second"""
        return self.fps
    
    def get_current_frame_number(self) -> int:
        """Get current frame number"""
        return self.current_frame
    
    def get_video_properties(self) -> dict:
        """Get comprehensive video properties"""
        return {
            'source_type': self.source_type,
            'source_path': self.source_path,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'total_frames': self.total_frames,
            'current_frame': self.current_frame,
            'is_opened': self.is_opened(),
            'duration_seconds': self.total_frames / self.fps if self.total_frames > 0 else -1,
            'progress_percent': (self.current_frame / self.total_frames * 100) if self.total_frames > 0 else -1
        }
    
    def seek_to_frame(self, frame_number: int) -> bool:
        """Seek to specific frame (video files only)"""
        if self.source_type != "file" or self.cap is None:
            logger.warning("Seeking only supported for video files")
            return False
        
        if frame_number < 0 or (self.total_frames > 0 and frame_number >= self.total_frames):
            logger.warning(f"Invalid frame number: {frame_number}")
            return False
        
        try:
            success = self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            if success:
                self.current_frame = frame_number
                logger.debug(f"Seeked to frame {frame_number}")
            return success
        except Exception as e:
            logger.error(f"Failed to seek to frame {frame_number}: {e}")
            return False
    
    def seek_to_time(self, time_seconds: float) -> bool:
        """Seek to specific time (video files only)"""
        if self.source_type != "file":
            logger.warning("Seeking only supported for video files")
            return False
        
        frame_number = int(time_seconds * self.fps)
        return self.seek_to_frame(frame_number)
    
    def set_fps_limit(self, max_fps: float) -> None:
        """Set maximum FPS for processing (useful for real-time processing)"""
        if max_fps > 0:
            self.fps = min(self.fps, max_fps)
            logger.info(f"FPS limited to {max_fps}")
    
    def get_frame_at_position(self, frame_number: int) -> Tuple[bool, Optional[np.ndarray]]:
        """Get frame at specific position without changing current position"""
        if self.source_type != "file":
            logger.warning("Random access only supported for video files")
            return False, None
        
        # Save current position
        current_pos = self.current_frame
        
        # Seek to desired frame
        if self.seek_to_frame(frame_number):
            ret, frame = self.read_frame()
            
            # Restore original position
            self.seek_to_frame(current_pos)
            
            return ret, frame
        
        return False, None
    
    def validate_source(self, source: Union[str, int]) -> bool:
        """Validate video source without opening it"""
        try:
            if isinstance(source, int):
                # Camera index - assume valid if >= 0
                return source >= 0
            elif isinstance(source, str):
                if source.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
                    # Network stream - assume valid (actual validation requires connection)
                    return True
                else:
                    # File path
                    return os.path.isfile(source)
            return False
        except Exception:
            return False
    
    def get_supported_formats(self) -> list:
        """Get list of supported video formats"""
        return [
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', 
            '.webm', '.m4v', '.3gp', '.mpg', '.mpeg'
        ]
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()

class VideoWriter:
    """Utility class for writing processed video output"""
    
    def __init__(self, output_path: str, fps: float, frame_size: Tuple[int, int], 
                 codec: str = 'mp4v'):
        self.output_path = output_path
        self.fps = fps
        self.frame_size = frame_size
        self.codec = codec
        self.writer = None
        
    def initialize(self) -> bool:
        """Initialize video writer"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*self.codec)
            self.writer = cv2.VideoWriter(
                self.output_path, fourcc, self.fps, self.frame_size
            )
            
            if not self.writer.isOpened():
                logger.error(f"Failed to initialize video writer: {self.output_path}")
                return False
            
            logger.info(f"Video writer initialized: {self.output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize video writer: {e}")
            return False
    
    def write_frame(self, frame: np.ndarray) -> bool:
        """Write frame to output video"""
        if self.writer is None:
            return False
        
        try:
            # Ensure frame is correct size
            if frame.shape[:2][::-1] != self.frame_size:
                frame = cv2.resize(frame, self.frame_size)
            
            self.writer.write(frame)
            return True
            
        except Exception as e:
            logger.error(f"Failed to write frame: {e}")
            return False
    
    def release(self) -> None:
        """Release video writer"""
        if self.writer is not None:
            self.writer.release()
            self.writer = None
            logger.info(f"Video writer released: {self.output_path}")
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()