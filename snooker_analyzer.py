#!/usr/bin/env python3
"""
Snooker Video Analytics - Main Analysis Script
Fixed version with proper path handling and error checking
"""

import cv2
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO
import mediapipe as mp
import time

# Import configuration
from config import (
    BASE_DIR, DATASET_DIR, MODEL_PATH, VIDEO_PATH, 
    BALL_CLASSES, POCKETS, CONFIDENCE_THRESHOLD
)

def is_in_pocket(x, y):
    """Check if coordinates are within any pocket"""
    for idx, ((x1, y1), (x2, y2)) in enumerate(POCKETS):
        if x1 <= x <= x2 and y1 <= y <= y2:
            return idx
    return -1

class SnookerAnalyzer:
    def __init__(self):
        self.model = None
        self.face_detection = None
        self.movement_data = {cls_id: [] for cls_id in BALL_CLASSES}
        self.detections_per_class = {cls_id: 0 for cls_id in BALL_CLASSES}
        self.potted_balls = {}
        
    def load_model(self):
        """Load YOLO model with error handling"""
        try:
            if os.path.exists(MODEL_PATH):
                self.model = YOLO(MODEL_PATH)
                print(f"✅ Loaded trained model from {MODEL_PATH}")
            else:
                print(f"⚠️ Trained model not found at {MODEL_PATH}")
                print("🔄 Using pre-trained YOLOv8s model")
                self.model = YOLO("yolov8s.pt")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
        return True
    
    def setup_face_detection(self):
        """Initialize MediaPipe face detection"""
        mp_face_detection = mp.solutions.face_detection
        self.face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)
        
    def analyze_video(self, video_path=None):
        """Analyze snooker video for ball tracking and potting detection"""
        if video_path is None:
            video_path = VIDEO_PATH
            
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return False
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_path}")
            return False
            
        print(f"🎥 Analyzing video: {video_path}")
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # Run YOLO detection
            results = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
            boxes = results[0].boxes
            
            detected_in_frame = {cls_id: False for cls_id in BALL_CLASSES}
            
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    cls_id = int(box.cls.item())
                    if cls_id in BALL_CLASSES:
                        name, color = BALL_CLASSES[cls_id]
                        conf = float(box.conf.item())
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        centroid_x = (x1 + x2) // 2
                        centroid_y = (y1 + y2) // 2
                        
                        # Store movement data
                        if not detected_in_frame[cls_id]:
                            detected_in_frame[cls_id] = True
                            self.movement_data[cls_id].append((frame_count, centroid_x, centroid_y))
                            self.detections_per_class[cls_id] += 1
                            
                        # Draw detection
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Display frame (optional - comment out for batch processing)
            cv2.imshow("Snooker Analysis", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"✅ Analysis complete. Processed {frame_count} frames")
        return True
    
    def detect_potting_events(self):
        """Analyze movement data to detect potting events"""
        for cls_id, coords in self.movement_data.items():
            if len(coords) < 2:
                continue
                
            ball_name = BALL_CLASSES[cls_id][0]
            potted_events = []
            
            for i in range(1, len(coords)):
                frame_num, x, y = coords[i]
                prev_frame, prev_x, prev_y = coords[i-1]
                
                # Calculate movement distance
                distance = np.sqrt((x - prev_x)**2 + (y - prev_y)**2)
                
                # Check if ball moved significantly into a pocket
                if distance > 60:  # Significant movement threshold
                    pocket_idx = is_in_pocket(x, y)
                    if pocket_idx != -1:
                        potted_events.append((frame_num, (x, y), pocket_idx))
            
            if potted_events:
                self.potted_balls[ball_name] = potted_events
    
    def generate_reports(self):
        """Generate analysis reports and visualizations"""
        # Print detection statistics
        print("\n📊 Detection Statistics:")
        for cls_id, count in self.detections_per_class.items():
            ball_name = BALL_CLASSES[cls_id][0]
            print(f"  {ball_name}: {count} detections")
        
        # Print potting events
        print("\n🏆 Potting Events:")
        if self.potted_balls:
            for ball, events in self.potted_balls.items():
                print(f"  {ball}: {len(events)} pots")
                for frame, pos, pocket in events:
                    print(f"    Frame {frame}: Position {pos}, Pocket {pocket}")
        else:
            print("  No potting events detected")
        
        # Save movement data
        self.save_movement_data()
        
        # Generate trajectory plot
        self.plot_trajectories()
    
    def save_movement_data(self):
        """Save movement data to file"""
        output_file = os.path.join(DATASET_DIR, "movement_analysis.txt")
        with open(output_file, "w") as f:
            f.write("Snooker Ball Movement Analysis\n")
            f.write("=" * 40 + "\n\n")
            
            for cls_id, coords in self.movement_data.items():
                ball_name = BALL_CLASSES[cls_id][0]
                f.write(f"{ball_name}: {len(coords)} positions\n")
                if coords:
                    f.write(f"  First position: Frame {coords[0][0]} at ({coords[0][1]}, {coords[0][2]})\n")
                    f.write(f"  Last position: Frame {coords[-1][0]} at ({coords[-1][1]}, {coords[-1][2]})\n")
                f.write("\n")
        
        print(f"💾 Movement data saved to {output_file}")
    
    def plot_trajectories(self):
        """Generate trajectory visualization"""
        if not any(self.movement_data.values()):
            print("⚠️ No movement data to plot")
            return
            
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        for cls_id, coords in self.movement_data.items():
            if not coords:
                continue
                
            ball_name, color = BALL_CLASSES[cls_id]
            # Convert color from BGR to RGB and normalize
            color_rgb = [c/255 for c in reversed(color)]
            
            frames = [c[0] for c in coords]
            x_coords = [c[1] for c in coords]
            y_coords = [c[2] for c in coords]
            
            ax1.plot(frames, x_coords, label=f"{ball_name} (X)", 
                    marker='o', color=color_rgb, markersize=3)
            ax2.plot(frames, y_coords, label=f"{ball_name} (Y)", 
                    marker='o', color=color_rgb, markersize=3)
        
        ax1.set_ylabel("X Coordinate (pixels)")
        ax1.set_title("Ball Trajectories - X Coordinates")
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True)
        
        ax2.set_ylabel("Y Coordinate (pixels)")
        ax2.set_xlabel("Frame Number")
        ax2.set_title("Ball Trajectories - Y Coordinates")
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True)
        
        plt.tight_layout()
        
        # Save plot
        output_file = os.path.join(DATASET_DIR, "ball_trajectories.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"📈 Trajectory plot saved to {output_file}")

def main():
    """Main analysis function"""
    print("🎱 Snooker Video Analytics")
    print("=" * 30)
    
    # Initialize analyzer
    analyzer = SnookerAnalyzer()
    
    # Load model
    if not analyzer.load_model():
        return
    
    # Setup face detection
    analyzer.setup_face_detection()
    
    # Analyze video
    if analyzer.analyze_video():
        # Detect potting events
        analyzer.detect_potting_events()
        
        # Generate reports
        analyzer.generate_reports()
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()