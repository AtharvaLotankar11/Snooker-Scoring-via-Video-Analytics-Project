import cv2
import numpy as np
import os

basedir = "C:/Users/Manoj/Downloads/Snooker/"
def detect_motion(frame, prev_frame):
    """
    Detect general motion between two frames using frame differencing.
    Returns True if motion exceeds threshold.
    """
    gray1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(diff, 1, 255, cv2.THRESH_BINARY)  # Lowered from 5 to 1
    motion_pixels = np.sum(thresh) / 255
    print(f"General motion pixels: {motion_pixels}")
    return motion_pixels > 10  # Lowered from 50


def detect_cue_ball_motion(frame, prev_frame, bbox):
    """
    Detect motion in a bounding box (e.g., cue ball region).
    Saves threshold image for debugging.
    Returns True if motion exceeds threshold.
    """
    x, y, w, h = bbox
    if x + w > frame.shape[1] or y + h > frame.shape[0]:
        print(f"Error: Bbox {bbox} exceeds frame size {frame.shape}")
        return False
    roi1 = frame[y:y + h, x:x + w]
    roi2 = prev_frame[y:y + h, x:x + w]
    gray1 = cv2.cvtColor(roi1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(roi2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)

    # Ensure output directory exists
    os.makedirs(basedir + "dataset", exist_ok=True)
    cv2.imwrite(basedir + "dataset/diff_debug.jpg", diff)  # Save diff image for debugging

    _, thresh = cv2.threshold(diff, 1, 255, cv2.THRESH_BINARY)  # Lowered from 5 to 1
    motion_pixels = np.sum(thresh) / 255
    print(f"Cue ball motion pixels: {motion_pixels}")
    cv2.imwrite(basedir + "dataset/thresh.jpg", thresh)
    return motion_pixels > 5  # Lowered from 20


class ShotDetector:
    """
    Tracks shot start (motion begins) and end (no motion for 2 frames).
    Uses detect_cue_ball_motion to analyze frames.
    """

    def __init__(self):
        self.motion_count = 0
        self.no_motion_count = 0
        self.shot_active = False

    def detect_shot(self, frame, prev_frame, bbox):
        """
        Detect shot start/end based on cue ball motion.
        Returns (shot_start, shot_end) as booleans.
        """
        motion = detect_cue_ball_motion(frame, prev_frame, bbox)
        print(f"Motion: {motion}, Shot active: {self.shot_active}, No motion count: {self.no_motion_count}")
        if motion and not self.shot_active:
            self.shot_active = True
            self.no_motion_count = 0
            return True, False
        elif not motion and self.shot_active:
            self.no_motion_count += 1
            if self.no_motion_count >= 2:
                self.shot_active = False
                return False, True
        else:
            self.no_motion_count = 0 if motion else self.no_motion_count + 1
            return False, False


if __name__ == "__main__":
    frame1 = cv2.imread(basedir + "dataset/frame_8.jpg")
    frame2 = cv2.imread(basedir + "dataset/frame_9.jpg")

    if frame1 is None or frame2 is None:
        print("Error: Could not load frames")
        exit()

    print(f"Frame shape: {frame1.shape}")

    has_motion = detect_motion(frame1, frame2)
    print("General motion detected:", has_motion)

    bbox = [0, 0, 640, 360]  # Changed to cover entire frame
    has_cue_motion = detect_cue_ball_motion(frame1, frame2, bbox)
    print("Cue ball motion detected:", has_cue_motion)

    detector = ShotDetector()
    shot_start, shot_end = detector.detect_shot(frame1, frame2, bbox)
    print(f"Shot start: {shot_start}, Shot end: {shot_end}")
