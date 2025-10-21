#!/usr/bin/env python3
"""
Processing module for frame processing pipeline
"""

from .frame_processor import FrameProcessor
from .video_input_handler import VideoInputHandler, VideoWriter

__all__ = ['FrameProcessor', 'VideoInputHandler', 'VideoWriter']