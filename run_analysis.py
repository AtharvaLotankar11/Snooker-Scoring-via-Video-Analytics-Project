#!/usr/bin/env python3
"""
Simple launcher script for Snooker Video Analytics
Handles dependency checking and provides user-friendly interface
"""

import os
import sys
import subprocess

def check_dependencies():
    """Quick dependency check"""
    try:
        import cv2, numpy, matplotlib, ultralytics, mediapipe
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def install_dependencies():
    """Install dependencies if missing"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def main():
    """Main launcher function"""
    print("🎱 Snooker Video Analytics - Launcher")
    print("=" * 40)
    
    # Check if video file exists
    video_path = "dataset/sample_snooker.mp4"
    if not os.path.exists(video_path):
        print(f"⚠️ Video file not found: {video_path}")
        print("Please place your snooker video in the dataset folder")
        return
    
    # Check dependencies
    if not check_dependencies():
        install_choice = input("Install missing dependencies? (y/n): ").lower().strip()
        if install_choice == 'y':
            if not install_dependencies():
                return
        else:
            print("❌ Cannot run without dependencies")
            return
    
    print("🚀 Starting Snooker Analysis...")
    print("Press 'q' in the video window to stop analysis")
    print("-" * 40)
    
    # Run the main analyzer
    try:
        from snooker_analyzer import main as run_analyzer
        run_analyzer()
    except KeyboardInterrupt:
        print("\n⏹️ Analysis stopped by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print("Check that your video file is valid and try again")

if __name__ == "__main__":
    main()