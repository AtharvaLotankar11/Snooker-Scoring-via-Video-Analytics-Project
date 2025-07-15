import cv2
import numpy as np

basedir = "C:/Users/Manoj/Downloads/Snooker/"

def save_threshold_image(frame1_path, frame2_path, bbox, output_path):
    """
    Generate and save a threshold image for motion detection in a bounding box.
    Args:
        frame1_path, frame2_path: Paths to input frames.
        bbox: [x, y, w, h] for region of interest.
        output_path: Path to save threshold image.
    """
    frame1 = cv2.imread(frame1_path)
    frame2 = cv2.imread(frame2_path)
    if frame1 is None or frame2 is None:
        print(f"Error: Could not load {frame1_path} or {frame2_path}")
        return
    x, y, w, h = bbox
    if x + w > frame1.shape[1] or y + h > frame1.shape[0]:
        print(f"Error: Bbox {bbox} exceeds frame size {frame1.shape}")
        return
    roi1 = frame1[y:y+h, x:x+w]
    roi2 = frame2[y:y+h, x:x+w]
    gray1 = cv2.cvtColor(roi1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(roi2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)  # Lowered from 30
    motion_pixels = np.sum(thresh) / 255
    cv2.imwrite(output_path, thresh)
    print(f"Saved {output_path}, Motion pixels: {motion_pixels}")

if __name__ == "__main__":
    bbox = [180, 140, 30, 30]  # Optimized for 360x640
    save_threshold_image(basedir + "dataset/frame_8.jpg", basedir + "dataset/frame_9.jpg", bbox, basedir + "dataset/thresh_8_9.jpg")
    save_threshold_image(basedir + "dataset/frame_9.jpg", basedir + "dataset/frame_10.jpg", bbox, basedir + "dataset/thresh_9_10.jpg")