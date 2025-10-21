from ultralytics import YOLO
import cv2
import os
import matplotlib.pyplot as plt
import numpy as np
import mediapipe as mp
import time

# --- Smart Potting Detection (Movement + Pocket Check) ---
pockets = [
    ((550, 190), (560, 200)),  # For red_ball (exact match for 554, 195)
    ((610, 300), (630, 340)),  # For black_ball (near 621, 319)
    ((0, 380), (100, 480)),  # Bottom-left (optional)
    ((540, 380), (640, 480))  # Bottom-right (optional)
]


def is_in_pocket(x, y):
    for idx, ((x1, y1), (x2, y2)) in enumerate(pockets):
        if x1 <= x <= x2 and y1 <= y <= y2:
            return idx
    return -1


# --- Video Capture Initialization ---
cap = cv2.VideoCapture("C:/Users/Manoj/Downloads/Snooker/dataset/sample_snooker.mp4")
if not cap.isOpened():
    print("Error: Could not open video source.")
    exit()
frame_count = 0

# Load the trained YOLO model
try:
    model = YOLO("C:/Users/Manoj/Downloads/Snooker/scripts/detection/runs/detect/cue_ball_model_augmented/weights/best.pt")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    exit()

# Input and output paths
input_dir = "C:/Users/Manoj/Downloads/Snooker/dataset/yolo_data/images/train"
output_dir = "C:/Users/Manoj/Downloads/Snooker/dataset"
frame_files = [f"frame_{i}.jpg" for i in range(80)]

# Detection parameters
conf_threshold = 0.2

# Target classes
target_classes = {
    0: ("cue_ball", (255, 255, 255)),
    1: ("yellow_ball", (0, 255, 255)),
    2: ("red_ball", (255, 0, 0)),
    3: ("orange_ball", (165, 42, 42)),
    4: ("green_ball", (0, 128, 0)),
    5: ("pink_ball", (255, 20, 147)),
    6: ("blue_ball", (0, 0, 255)),
    7: ("black_ball", (0, 0, 0))
}

# Store movement data (reset before real-time loop)
movement_data = {cls_id: [] for cls_id in target_classes}
red_ball_data = []

# Stats
total = 0
fallbacks = 0
detections_per_class = {cls_id: 0 for cls_id in target_classes}

# Original frame processing loop
for idx, frame_file in enumerate(frame_files):
    total += 1
    input_path = os.path.join(input_dir, frame_file)
    output_path = os.path.join(output_dir, f"test_yolo_{frame_file}")
    frame = cv2.imread(input_path)

    if frame is None:
        print(f"⚠ Error loading {frame_file}")
        continue

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
                centroid_x = (x1 + x2) // 2
                centroid_y = (y1 + y2) // 2

                if cls_id == 7:  # red_ball
                    red_ball_data.append((idx, centroid_x, centroid_y))
                    detections_per_class[cls_id] += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                elif not detected_in_frame[cls_id]:
                    detected_in_frame[cls_id] = True
                    frame_data[name] = [(centroid_x, centroid_y)]
                    detections_per_class[cls_id] += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        for name, centroids in frame_data.items():
            for cls_id, (cls_name, _) in target_classes.items():
                if cls_name == name and cls_id != 7:
                    if cls_id not in movement_data:
                        movement_data[cls_id] = []
                    for centroid in centroids:
                        movement_data[cls_id].append((idx, centroid[0], centroid[1]))

    if not any(detected_in_frame.values()):
        fallbacks += 1
        x1, y1, w, h = 190, 140, 20, 20
        x2, y2 = x1 + w, y1 + h
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(frame, "Fallback", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    cv2.imwrite(output_path, frame)

# Reset data for real-time loop to avoid pre-loaded contamination
movement_data = {cls_id: [] for cls_id in target_classes}
red_ball_data = []
detections_per_class = {cls_id: 0 for cls_id in target_classes}

# --- Real-Time Frame Processing Loop ---
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
print(f"Starting real-time loop with frame_count reset to 0")
frame_count = 0

# Initialize Mediapipe Face Detection
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Skip initial frames to avoid false positives
for _ in range(5):  # Skip first 5 frames
    ret, _ = cap.read()
    if not ret:
        print("Error: Could not read initial frames. Ending real-time processing.")
        break
    time.sleep(0.1)  # Small delay

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame. Ending real-time processing.")
        break

    total += 1
    frame_count += 1

    # Convert frame to RGB for Mediapipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Player detection (face/presence)
    results = face_detection.process(frame_rgb)
    players_detected = False
    if results.detections:
        for detection in results.detections:
            mp_drawing.draw_detection(frame, detection)
            players_detected = True
            # Define table region (approximate coordinates)
            table_region = [(0, 0), (640, 480)]  # Adjust based on your table size
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = frame.shape
            x_min = int(bbox.xmin * w)
            y_min = int(bbox.ymin * h)
            x_max = x_min + int(bbox.width * w)
            y_max = y_min + int(bbox.height * h)
            if (table_region[0][0] <= x_min <= table_region[1][0] and
                    table_region[0][1] <= y_min <= table_region[1][1]):
                cv2.putText(frame, "Player Near Table", (x_min, y_min - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # YOLO detection
    results_yolo = model(frame, conf=conf_threshold, verbose=False)
    boxes = results_yolo[0].boxes

    detected_in_frame = {cls_id: False for cls_id in target_classes}
    frame_data = {}

    if boxes is not None and len(boxes) > 0:
        for box in boxes:
            cls_id = int(box.cls.item())
            if cls_id in target_classes:
                name, color = target_classes[cls_id]
                conf = float(box.conf.item())
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                centroid_x = (x1 + x2) // 2
                centroid_y = (y1 + y2) // 2

                if cls_id == 7:  # red_ball
                    red_ball_data.append((frame_count, centroid_x, centroid_y))
                    detections_per_class[cls_id] += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    print(
                        f"Frame {frame_count}: Detected red_ball at ({centroid_x}, {centroid_y}) with conf {conf:.2f}")  # Debug
                elif not detected_in_frame[cls_id]:
                    detected_in_frame[cls_id] = True
                    frame_data[name] = [(centroid_x, centroid_y)]
                    detections_per_class[cls_id] += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        for name, centroids in frame_data.items():
            for cls_id, (cls_name, _) in target_classes.items():
                if cls_name == name and cls_id != 7:
                    if cls_id not in movement_data:
                        movement_data[cls_id] = []
                    for centroid in centroids:
                        movement_data[cls_id].append((frame_count, centroid[0], centroid[1]))

    if not any(detected_in_frame.values()):
        fallbacks += 1
        x1, y1, w, h = 190, 140, 20, 20
        x2, y2 = x1 + w, y1 + h
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(frame, "Fallback", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    # Display frame with detections and player info
    cv2.imshow("Snooker Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
print(f"Frame count after real-time loop: {frame_count}")

# Final Stats
print("\n✅ Testing complete.")
print(f"🧮 Total frames: {total}")
for cls_id, count in detections_per_class.items():
    print(f"🎯 {target_classes[cls_id][0]} detected: {count} instances")
print(f"🟡 Fallbacks used: {fallbacks}")
print(f"📉 Fallback rate: {(fallbacks / total) * 100:.2f}%")

# Prepare data for plotting (using only real-time data)
plot_data = {}
for cls_id, coords in movement_data.items():
    if coords:
        frame_indices = [point[0] for point in coords]
        x_coords = [point[1] for point in coords]
        y_coords = [point[2] for point in coords]
        plot_data[target_classes[cls_id][0]] = {"frames": frame_indices, "x": x_coords, "y": y_coords}

if red_ball_data:
    frame_indices = [point[0] for point in red_ball_data]
    x_coords = [point[1] for point in red_ball_data]
    y_coords = [point[2] for point in red_ball_data]
    plot_data["red_ball"] = {"frames": frame_indices, "x": x_coords, "y": y_coords}

# Print movement data
print("\nMovement Data:")
for ball, coords in movement_data.items():
    print(f"{target_classes[ball][0]}: {len(coords)} positions - {coords}")
print(f"red_ball: {len(red_ball_data)} positions - {red_ball_data}")

# --- Ball Trajectory Plotting ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
colors = {name: [c / 255 for c in color] for _, (name, color) in target_classes.items()}
colors["cue_ball"] = [1.0, 0.0, 1.0]  # Highlight cue_ball

for ball, data in plot_data.items():
    color = colors.get(ball, [0, 0, 0])
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

# --- Save Trajectory Plot ---
fig.savefig(os.path.join(output_dir, "trajectory_plot.png"))  # Save after showing
print("Trajectory plot saved as 'trajectory_plot.png'")

# --- Smart Potting Detection (Movement + Pocket Check) ---
potted_balls = {}
potted_ball_tracker = {}  # Track balls already potted by centroid proximity

# Focus only on red_ball and black_ball
target_balls = {"red_ball", "black_ball"}
for ball_name, data in plot_data.items():
    if ball_name not in target_balls:
        continue
    frames = data["frames"]
    xs = data["x"]
    ys = data["y"]
    is_potted = False  # Track if ball is currently potted
    last_potted_frame = -10  # Initialize to allow initial pots
    last_x, last_y = xs[0], ys[0]  # Initialize last position

    for i in range(1, len(frames)):
        current_x, current_y = xs[i], ys[i]
        # Check if ball has left the pocket
        last_pocket_idx = is_in_pocket(last_x, last_y)
        current_pocket_idx = is_in_pocket(current_x, current_y)
        if last_pocket_idx != -1 and current_pocket_idx == -1:
            is_potted = False  # Ball has left the pocket

        # Check for significant movement into pocket
        dx = current_x - last_x
        dy = current_y - last_y
        distance = np.sqrt(dx ** 2 + dy ** 2)
        if distance > 60 and not is_potted:
            pocket_idx = is_in_pocket(current_x, current_y)
            if pocket_idx != -1:
                current_frame = frames[i]
                # Debounce: Check if this ball was already potted (within 20 pixels)
                is_new_pot = True
                for prev_x, prev_y in potted_ball_tracker.get(ball_name, []):
                    if np.sqrt((current_x - prev_x) * 2 + (current_y - prev_y) * 2) < 20:
                        is_new_pot = False
                        break
                if is_new_pot and current_frame - last_potted_frame > 20:  # Reset after 20 frames
                    if ball_name not in potted_balls:
                        potted_balls[ball_name] = []
                    potted_balls[ball_name].append((current_frame, (current_x, current_y), pocket_idx))
                    if ball_name not in potted_ball_tracker:
                        potted_ball_tracker[ball_name] = []
                    potted_ball_tracker[ball_name].append((current_x, current_y))
                    is_potted = True
                    last_potted_frame = current_frame

        last_x, last_y = current_x, current_y

# --- Print Potted Balls ---
if potted_balls:
    print("\n🏆 Potted Balls:")
    for ball, events in potted_balls.items():
        print(f"{ball}: {len(events)} pots - {events}")
else:
    print("\n🏆 No balls potted.")

# --- Visualize Potting Statistics ---
if potted_balls:
    # Prepare data for bar chart
    frames_red = {event[0]: 1 for event in potted_balls.get("red_ball", [])}
    frames_black = {event[0]: 1 for event in potted_balls.get("black_ball", [])}

    # Bar Chart
    plt.figure(figsize=(12, 6))
    bar_width = 0.35
    frame_indices = range(frame_count)  # Use frame_count
    red_counts = [frames_red.get(i, 0) for i in frame_indices]
    black_counts = [frames_black.get(i, 0) for i in frame_indices]
    plt.bar([i - bar_width / 2 for i in frame_indices], red_counts, bar_width, label="Red Ball Pots", color="#FF6384")
    plt.bar([i + bar_width / 2 for i in frame_indices], black_counts, bar_width, label="Black Ball Pots",
            color="#36A2EB")
    plt.xlabel("Frame Number")
    plt.ylabel("Number of Pots")
    plt.title("Potting Events per Frame")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Cumulative Line Chart
    plt.figure(figsize=(12, 6))
    frame_indices = range(frame_count)
    frames_red = {event[0]: 1 for event in potted_balls.get("red_ball", [])}
    frames_black = {event[0]: 1 for event in potted_balls.get("black_ball", [])}
    cumulative_red = [sum(frames_red.get(i, 0) for i in range(j + 1)) for j in frame_indices]
    cumulative_black = [sum(frames_black.get(i, 0) for i in range(j + 1)) for j in frame_indices]
    # Ensure cumulative_black is initialized with the correct length
    if not cumulative_black and frames_black:
        cumulative_black = [0] * frame_count
        for j in range(frame_count):
            if j >= min(frames_black.keys(), default=frame_count):
                cumulative_black[j] = 1
    elif not any(cumulative_black) and frames_black:
        cumulative_black = [0] * frame_count
        cumulative_black[min(frames_black.keys(), default=0)] = 1
    plt.plot(frame_indices, cumulative_red, label="Cumulative Red Ball Pots", marker='o', color="#FF6384")
    plt.plot(frame_indices, cumulative_black, label="Cumulative Black Ball Pots", marker='o', color="#36A2EB")
    plt.xlabel("Frame Number")
    plt.ylabel("Cumulative Pots")
    plt.title("Cumulative Potting Events")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
else:
    print("\nNo potting charts generated (no balls potted).")

# --- Save Results to Files ---
# Save movement data to a text file
with open(os.path.join(output_dir, "movement_data.txt"), "w", encoding="utf-8") as f:
    f.write("Movement Data:\n")
    for ball, coords in movement_data.items():
        f.write(f"{target_classes[ball][0]}: {len(coords)} positions - {coords}\n")
    if red_ball_data:
        f.write(f"red_ball: {len(red_ball_data)} positions - {red_ball_data}\n")

# Save potted balls to a text file
with open(os.path.join(output_dir, "potted_balls.txt"), "w", encoding="utf-8") as f:
    f.write("\nPotted Balls:\n")
    if potted_balls:
        for ball, events in potted_balls.items():
            f.write(f"{ball}: {len(events)} pots - {events}\n")
    else:
        f.write("No balls potted.\n")

# Save plots as images
if plot_data or potted_balls:
    # Save trajectory plot
    if 'fig' in locals():
        fig.savefig(os.path.join(output_dir, "trajectory_plot.png"))
        plt.close(fig)
        print("Trajectory plot saved as 'trajectory_plot.png'")
    else:
        print("Warning: Trajectory plot not saved (figure not created)")

    # Save bar chart
    if potted_balls:
        plt.figure(figsize=(12, 6))
        bar_width = 0.35
        frame_indices = range(frame_count)
        frames_red = {event[0]: 1 for event in potted_balls.get("red_ball", [])}
        frames_black = {event[0]: 1 for event in potted_balls.get("black_ball", [])}
        red_counts = [frames_red.get(i, 0) for i in frame_indices]
        black_counts = [frames_black.get(i, 0) for i in frame_indices]
        plt.bar([i - bar_width / 2 for i in frame_indices], red_counts, bar_width, label="Red Ball Pots",
                color="#FF6384")
        plt.bar([i + bar_width / 2 for i in frame_indices], black_counts, bar_width, label="Black Ball Pots",
                color="#36A2EB")
        plt.xlabel("Frame Number")
        plt.ylabel("Number of Pots")
        plt.title("Potting Events per Frame")
        plt.legend()
        plt.grid(True)
        # Set limits with default if empty
        max_count = max(max(red_counts, default=0), max(black_counts, default=0))
        plt.xlim(-bar_width, frame_count + bar_width)
        plt.ylim(0, max_count + 1 if max_count > 0 else 1)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "potting_events_bar.png"))
        plt.close()
        print("Potting events bar chart saved as 'potting_events_bar.png'")
    else:
        print("Warning: Potting events bar chart not saved (no pots detected)")

    # Save cumulative chart
    if potted_balls:
        plt.figure(figsize=(12, 6))
        frame_indices = range(frame_count)
        frames_red = {event[0]: 1 for event in potted_balls.get("red_ball", [])}
        frames_black = {event[0]: 1 for event in potted_balls.get("black_ball", [])}
        cumulative_red = [sum(frames_red.get(i, 0) for i in range(j + 1)) for j in frame_indices]
        cumulative_black = [sum(frames_black.get(i, 0) for i in range(j + 1)) for j in frame_indices]
        if not cumulative_black and frames_black:
            cumulative_black = [0] * frame_count
            for j in range(frame_count):
                if j >= min(frames_black.keys(), default=frame_count):
                    cumulative_black[j] = 1
        elif not any(cumulative_black) and frames_black:
            cumulative_black = [0] * frame_count
            cumulative_black[min(frames_black.keys(), default=0)] = 1
        plt.plot(frame_indices, cumulative_red, label="Cumulative Red Ball Pots", marker='o', color="#FF6384")
        plt.plot(frame_indices, cumulative_black, label="Cumulative Black Ball Pots", marker='o', color="#36A2EB")
        plt.xlabel("Frame Number")
        plt.ylabel("Cumulative Pots")
        plt.title("Cumulative Potting Events")
        plt.legend()
        plt.grid(True)
        # Set limits with default if empty
        max_cumulative = max(max(cumulative_red, default=0), max(cumulative_black, default=0))
        plt.xlim(-1, frame_count)
        plt.ylim(0, max_cumulative + 1 if max_cumulative > 0 else 1)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "potting_events_cumulative.png"))
        plt.close()
        print("Cumulative potting events chart saved as 'potting_events_cumulative.png'")
    else:
        print("Warning: Cumulative potting chart not saved (no pots detected)")

# --- Statistical Summary of Potting Events ---
if potted_balls:
    with open(os.path.join(output_dir, "potting_stats.txt"), "w", encoding="utf-8") as f:
        f.write("Potting Statistics:\n")
        for ball, events in potted_balls.items():
            if events:
                num_pots = len(events)
                frame_nums = [event[0] for event in events]
                avg_frame = sum(frame_nums) / num_pots if num_pots > 0 else 0
                f.write(f"\n{ball}:\n")
                f.write(f"  Number of pots: {num_pots}\n")
                f.write(f"  Average pot frame: {avg_frame:.2f}\n")
                f.write(f"  Earliest pot frame: {min(frame_nums)}\n")
                f.write(f"  Latest pot frame: {max(frame_nums)}\n")
                f.write(f"  Pot frames: {frame_nums}\n")
        print("Potting statistics saved as 'potting_stats.txt'")
else:
    with open(os.path.join(output_dir, "potting_stats.txt"), "w", encoding="utf-8") as f:
        f.write("No potting statistics available (no balls potted).\n")
    print("Potting statistics saved as 'potting_stats.txt' (no pots detected)")

# Release video capture and cleanup
cap.release()
cv2.destroyAllWindows()