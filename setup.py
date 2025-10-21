#!/usr/bin/env python3
"""
Setup script for Snooker Video Analytics
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'cv2', 'numpy', 'matplotlib', 'ultralytics', 'mediapipe'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies"""
    print("📦 Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "dataset/yolo_data/images/train",
        "dataset/yolo_data/labels/train",
        "scripts/detection/runs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def download_yolo_model():
    """Download YOLOv8 model if not present"""
    model_path = "scripts/detection/yolov8s.pt"
    if not os.path.exists(model_path):
        print("🔄 Downloading YOLOv8s model...")
        try:
            from ultralytics import YOLO
            model = YOLO("yolov8s.pt")
            # Move to scripts directory
            import shutil
            shutil.move("yolov8s.pt", model_path)
            print(f"✅ YOLOv8s model downloaded to {model_path}")
        except Exception as e:
            print(f"⚠️ Could not download model: {e}")
    else:
        print(f"✅ YOLOv8s model already exists at {model_path}")

def main():
    print("🎱 Snooker Video Analytics Setup")
    print("=" * 35)
    
    # Check dependencies
    missing = check_dependencies()
    
    if missing:
        print(f"\n📋 Missing packages: {', '.join(missing)}")
        install_deps = input("Install missing dependencies? (y/n): ").lower().strip()
        if install_deps == 'y':
            if not install_dependencies():
                print("❌ Setup failed due to dependency installation error")
                return
        else:
            print("⚠️ Setup incomplete - missing dependencies")
            return
    
    # Create directories
    print("\n📁 Creating project directories...")
    create_directories()
    
    # Download YOLO model
    print("\n🤖 Setting up YOLO model...")
    download_yolo_model()
    
    print("\n✅ Setup complete!")
    print("\n🚀 Next steps:")
    print("1. Place your snooker video in dataset/sample_snooker.mp4")
    print("2. Run: python snooker_analyzer.py")
    print("3. Or train custom model: cd scripts/detection && python train_yolo.py")

if __name__ == "__main__":
    main()