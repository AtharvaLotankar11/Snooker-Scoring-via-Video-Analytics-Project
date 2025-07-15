from ultralytics import YOLO

# Load YOLOv8s model
model = YOLO("yolov8s.pt")

# Train with custom augmentation
model.train(
    data="C:/Users/Manoj/Downloads/Snooker/dataset/yolo_data/data.yaml",
    epochs=20,
    imgsz=640,
    batch=2,
    name="cue_ball_model_augmented",
    device="cpu",
    project="runs/detect",
    exist_ok=True,
    resume=False,
    patience=10,
    # Custom augmentation overrides
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    scale=0.5,
    shear=2.0,
    perspective=0.001,
    flipud=0.0,   # Disable vertical flip
    fliplr=0.5,   # 50% chance of horizontal flip
    mosaic=1.0,   # Enable mosaic augmentation
    mixup=0.2,    # Slight mixup
)
