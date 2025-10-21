#!/usr/bin/env python3
"""
Kaggle Dataset Downloader for Snooker Analytics
"""

import os
import subprocess
import sys

# Recommended datasets for snooker analysis
DATASETS = {
    "snooker_balls": {
        "name": "kylelix7/snooker-ball-detection",
        "description": "Snooker ball detection with bounding boxes",
        "priority": "HIGH",
        "size": "~50MB"
    },
    "pool_balls": {
        "name": "gpiosenka/balls-image-classification", 
        "description": "Pool/billiard ball classification dataset",
        "priority": "MEDIUM",
        "size": "~100MB"
    },
    "sports_balls": {
        "name": "gpiosenka/sports-balls-multiclass-image-classification",
        "description": "Multi-class sports ball detection",
        "priority": "MEDIUM", 
        "size": "~200MB"
    },
    "sports_videos": {
        "name": "bharatnatrayn/sports-videos-for-analysis",
        "description": "Sports video analysis dataset",
        "priority": "LOW",
        "size": "~1GB"
    }
}

def check_kaggle_setup():
    """Check if Kaggle API is properly configured"""
    try:
        result = subprocess.run(['kaggle', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Kaggle API is installed")
            return True
        else:
            print("❌ Kaggle API not working properly")
            return False
    except FileNotFoundError:
        print("❌ Kaggle API not installed")
        return False

def install_kaggle():
    """Install Kaggle API"""
    print("📦 Installing Kaggle API...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "kaggle"])
        print("✅ Kaggle API installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Kaggle API")
        return False

def setup_kaggle_credentials():
    """Guide user through Kaggle API setup"""
    print("\n🔑 Kaggle API Setup Required:")
    print("1. Go to https://www.kaggle.com/account")
    print("2. Click 'Create New API Token'")
    print("3. Download kaggle.json file")
    print("4. Place it in ~/.kaggle/ (Linux/Mac) or C:\\Users\\{username}\\.kaggle\\ (Windows)")
    print("5. Run: chmod 600 ~/.kaggle/kaggle.json (Linux/Mac only)")
    
    input("\nPress Enter when you've completed the setup...")

def download_dataset(dataset_key, dataset_info):
    """Download a specific dataset"""
    dataset_name = dataset_info["name"]
    output_dir = f"datasets/{dataset_key}"
    
    print(f"\n📥 Downloading {dataset_name}...")
    print(f"   Description: {dataset_info['description']}")
    print(f"   Size: {dataset_info['size']}")
    
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Download dataset
        cmd = ["kaggle", "datasets", "download", "-d", dataset_name, "-p", output_dir, "--unzip"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Downloaded {dataset_name} to {output_dir}")
            return True
        else:
            print(f"❌ Failed to download {dataset_name}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading {dataset_name}: {e}")
        return False

def list_datasets():
    """List available datasets"""
    print("\n📋 Available Datasets:")
    print("=" * 50)
    
    for key, info in DATASETS.items():
        priority_emoji = {"HIGH": "🔥", "MEDIUM": "⭐", "LOW": "💡"}
        emoji = priority_emoji.get(info["priority"], "📦")
        
        print(f"{emoji} {key}")
        print(f"   Name: {info['name']}")
        print(f"   Description: {info['description']}")
        print(f"   Priority: {info['priority']}")
        print(f"   Size: {info['size']}")
        print()

def main():
    print("🎱 Snooker Analytics - Dataset Downloader")
    print("=" * 45)
    
    # Check Kaggle API
    if not check_kaggle_setup():
        install_choice = input("Install Kaggle API? (y/n): ").lower().strip()
        if install_choice == 'y':
            if not install_kaggle():
                return
            setup_kaggle_credentials()
        else:
            print("❌ Kaggle API required for dataset download")
            return
    
    # List available datasets
    list_datasets()
    
    # Get user choice
    print("📥 Download Options:")
    print("1. Download high priority datasets only")
    print("2. Download all datasets")
    print("3. Select specific datasets")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        # Download high priority only
        for key, info in DATASETS.items():
            if info["priority"] == "HIGH":
                download_dataset(key, info)
                
    elif choice == "2":
        # Download all datasets
        for key, info in DATASETS.items():
            download_dataset(key, info)
            
    elif choice == "3":
        # Select specific datasets
        print("\nAvailable datasets:")
        for i, key in enumerate(DATASETS.keys(), 1):
            print(f"{i}. {key}")
        
        selections = input("Enter dataset numbers (comma-separated): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selections.split(",")]
            keys = list(DATASETS.keys())
            for idx in indices:
                if 0 <= idx < len(keys):
                    key = keys[idx]
                    download_dataset(key, DATASETS[key])
        except ValueError:
            print("❌ Invalid selection")
            
    elif choice == "4":
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")
        return
    
    print("\n✅ Dataset download complete!")
    print("\n🚀 Next steps:")
    print("1. Check the datasets/ folder for downloaded data")
    print("2. Update your YOLO training data with new images")
    print("3. Retrain your model: cd scripts/detection && python train_yolo.py")

if __name__ == "__main__":
    main()