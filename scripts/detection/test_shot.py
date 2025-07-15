import cv2
from motion import ShotDetector
import os

detector = ShotDetector()
# Use absolute paths
base_path = r"C:\Users\Manoj\Downloads\Snooker\dataset"
frames = [
    os.path.join(base_path, "frame_8.jpg"),
    os.path.join(base_path, "frame_9.jpg"),
    os.path.join(base_path, "frame_10.jpg")
]
bbox = [180, 140, 30, 30]  # Optimized for 360x640
prev_frame = None

for frame_path in frames:
    if not os.path.exists(frame_path):
        print(f"Error: File not found at {frame_path}")
        continue
    frame = cv2.imread(frame_path)
    if frame is None:
        print(f"Error: Could not load {frame_path}")
        continue
    if prev_frame is not None:
        shot_start, shot_end = detector.detect_shot(frame, prev_frame, bbox)
        print(f"{frame_path}: Start={shot_start}, End={shot_end}")
    prev_frame = frame