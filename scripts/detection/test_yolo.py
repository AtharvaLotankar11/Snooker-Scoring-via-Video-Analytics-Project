from ultralytics import YOLO
import cv2
import os
import matplotlib.pyplot as plt
import numpy as np

# Load trained YOLO model
model = YOLO("C:/Users/Manoj/Downloads/Snooker/scripts/detection/runs/detect/cue_ball_model_augmented/weights/best.pt")

# Input and output paths
image_dir = "C:/Users/Manoj/Downloads/Snooker/dataset/yolo_data/images/train"
output_dir = "C:/Users/Manoj/Downloads/Snooker/dataset"
os.makedirs(output_dir, exist_ok=True)

frame_files = [f"frame_{i}.jpg" for i in range(80)]

# Class definitions and colors (BGR)
target_classes = {
    0: ("cue_ball", (0, 255, 0)),        # Green
    1: ("yellow_ball", (0, 255, 255)),   # Yellow
    2: ("red_ball", (0, 0, 255)),        # Red
    3: ("orange_ball", (0, 165, 255)),   # Orange
    4: ("green_ball", (0, 128, 0)),      # Dark Green
    5: ("pink_ball", (203, 192, 255)),   # Pink
    6: ("blue_ball", (255, 0, 0)),       # Blue
    7: ("black_ball", (0, 0, 0))         # Black
}

conf_threshold = 0.20

# Data structures
movement_data = {cls_id: [] for cls_id in target_classes}
detections_per_class = {cls_id: 0 for cls_id in target_classes}
red_ball_data = []
total = 0
fallbacks = 0

# Frame loop
for idx, frame_file in enumerate(frame_files):
    total += 1
    frame_path = os.path.join(image_dir, frame_file)
    output_path = os.path.join(output_dir, f"test_yolo_{frame_file}")
    frame = cv2.imread(frame_path)

    if frame is None:
        print(f"⚠️ Could not load {frame_file}")
        continue

    print(f"📷 Processing {frame_file} | Frame {idx} | Shape: {frame.shape}")
    results = model(frame, conf=conf_threshold, verbose=False)
    boxes = results[0].boxes

    detected_in_frame = {cls_id: False for cls_id in target_classes}
    frame_data = {}

    if boxes is not None and len(boxes) > 0:
        for box in boxes:
            cls_id = int(box.cls.item())
            if cls_id in target_classes:
                name, color = target_classes[cls_id]
                conf = float(box.conf.item())
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                # Draw bounding box and label
                label = f"{name} {conf:.2f}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                if cls_id == 2:  # red_ball
                    red_ball_data.append((idx, cx, cy))
                elif not detected_in_frame[cls_id]:
                    detected_in_frame[cls_id] = True
                    frame_data[name] = [(cx, cy)]

                detections_per_class[cls_id] += 1
                print(f"✅ {name} detected in {frame_file}: Conf={conf:.3f}, Centroid=({cx}, {cy})")

        # Store centroids with frame index
        for name, centroids in frame_data.items():
            for cls_id, (cls_name, _) in target_classes.items():
                if cls_name == name and cls_id != 2:
                    for (cx, cy) in centroids:
                        movement_data[cls_id].append((idx, cx, cy))
    else:
        # Fallback
        fallbacks += 1
        x1, y1, w, h = 190, 140, 20, 20
        x2, y2 = x1 + w, y1 + h
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(frame, "Fallback", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        print(f"🟡 Fallback for {frame_file}: [{x1}, {y1}, {w}, {h}]")

    cv2.imwrite(output_path, frame)
    print(f"💾 Saved: {output_path}")

# Summary Stats
print("\n✅ Detection complete.")
print(f"🧮 Total frames: {total}")
for cls_id, count in detections_per_class.items():
    print(f"🎯 {target_classes[cls_id][0]} detected in: {count} instances")
print(f"🟡 Fallbacks used: {fallbacks}")
print(f"📉 Fallback rate: {(fallbacks / total) * 100:.2f}%")

# Prepare data for plotting
plot_data = {}
for cls_id, coords in movement_data.items():
    if coords:
        frames = [pt[0] for pt in coords]
        x_vals = [pt[1] for pt in coords]
        y_vals = [pt[2] for pt in coords]
        plot_data[target_classes[cls_id][0]] = {"frames": frames, "x": x_vals, "y": y_vals}

# Add red_ball
if red_ball_data:
    frames = [pt[0] for pt in red_ball_data]
    x_vals = [pt[1] for pt in red_ball_data]
    y_vals = [pt[2] for pt in red_ball_data]
    plot_data["red_ball"] = {"frames": frames, "x": x_vals, "y": y_vals}

# Print movement data
print("\n📍 Movement Data:")
for cls_id, coords in movement_data.items():
    print(f"{target_classes[cls_id][0]}: {len(coords)} positions - {coords}")
print("\nRed Ball Data:")
print(f"red_ball: {len(red_ball_data)} positions - {red_ball_data}")

# Plot movement trajectories (X and Y)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# Build correct color mapping
colors = {}
for cls_id, (name, bgr) in target_classes.items():
    rgb = tuple(c / 255.0 for c in reversed(bgr))  # Convert BGR to RGB
    colors[name] = rgb

# Use matching colors from target_classes
for ball, data in plot_data.items():
    color = colors.get(ball, [0, 0, 0])  # default black
    ax1.plot(data["frames"], data["x"], label=f"{ball} (X)", marker='o', color=color)
    ax2.plot(data["frames"], data["y"], label=f"{ball} (Y)", marker='o', color=color)

ax1.set_ylabel("X Coordinate (pixels)")
ax2.set_ylabel("Y Coordinate (pixels)")
ax2.set_xlabel("Frame Number")
fig.suptitle("Ball Movement Trajectories")
ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.grid(True)
plt.show()

# Potting Detection
pockets = [
    ((0, 0), (150, 150)),
    ((650, 0), (800, 150)),
    ((0, 450), (150, 600)),
    ((650, 450), (800, 600)),
    ((350, 0), (450, 150)),
    ((350, 450), (450, 600))
]

potted_balls = {}
all_data = {**movement_data, "red_ball": red_ball_data}

for ball_name, coords in all_data.items():
    if coords:
        for frame_idx, x, y in coords:
            for pocket_idx, ((px1, py1), (px2, py2)) in enumerate(pockets):
                if px1 <= x <= px2 and py1 <= y <= py2:
                    if ball_name not in potted_balls:
                        potted_balls[ball_name] = []
                    potted_balls[ball_name].append((frame_idx, (x, y), pocket_idx))
                    print(f"🎱 {ball_name} potted at frame {frame_idx} in pocket {pocket_idx} at ({x}, {y})")

# Potting Summary
if potted_balls:
    print("\n🏆 Potted Balls Summary:")
    for ball, events in potted_balls.items():
        print(f"{ball}: Potted {len(events)} time(s) - {events}")
else:
    print("\n🏆 No balls were potted.")
