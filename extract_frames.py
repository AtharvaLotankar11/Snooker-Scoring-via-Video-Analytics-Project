import cv2
cap = cv2.VideoCapture("dataset/sample_snooker.mp4")
if not cap.isOpened():
      print("Error: Could not open video")
      exit()
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)
frame_interval = 50  # Extract every 10th frame
i = 0
frame_idx = 0
while i < 80 and frame_idx < frame_count:
      cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
      ret, frame = cap.read()
      if ret:
          cv2.imwrite(f"dataset/frame_{i}.jpg", frame)
          i += 1
      frame_idx += frame_interval
cap.release()
print(f"Extracted {i} frames at {frame_interval}-frame intervals")