import os

# Base directory - automatically detects project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
YOLO_DATA_DIR = os.path.join(DATASET_DIR, "yolo_data")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts", "detection")
MODEL_PATH = os.path.join(SCRIPTS_DIR, "runs", "detect", "cue_ball_model_augmented", "weights", "best.pt")
VIDEO_PATH = os.path.join(DATASET_DIR, "sample_snooker.mp4")

# Ball classes (fixed inconsistency)
BALL_CLASSES = {
    0: ("cue_ball", (255, 255, 255)),
    1: ("yellow_ball", (0, 255, 255)),
    2: ("red_ball", (255, 0, 0)),
    3: ("orange_ball", (165, 42, 42)),
    4: ("green_ball", (0, 128, 0)),
    5: ("pink_ball", (255, 20, 147)),
    6: ("blue_ball", (0, 0, 255)),
    7: ("black_ball", (0, 0, 0))
}

# Pocket coordinates (adjust based on your video)
POCKETS = [
    ((550, 190), (560, 200)),  # Top-right pocket
    ((610, 300), (630, 340)),  # Right pocket
    ((0, 380), (100, 480)),    # Bottom-left pocket
    ((540, 380), (640, 480))   # Bottom-right pocket
]

# Detection parameters
CONFIDENCE_THRESHOLD = 0.2
MOTION_THRESHOLD = 10
CUE_MOTION_THRESHOLD = 5