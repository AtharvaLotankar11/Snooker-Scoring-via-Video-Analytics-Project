import cv2
import numpy as np

basedir = "C:/Users/Manoj/Downloads/Snooker/"
frame1 = cv2.imread(basedir + "dataset/frame_8.jpg")
frame2 = cv2.imread(basedir + "dataset/frame_9.jpg")
if frame1 is None or frame2 is None:
    print("Error: Could not load frames")
    exit()

gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
diff = cv2.absdiff(gray1, gray2)
_, thresh = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)
motion_pixels = np.sum(thresh) / 255
cv2.imwrite(basedir + "dataset/diff.jpg", thresh)
print(f"Saved {basedir}dataset/diff.jpg, Motion pixels: {motion_pixels}")