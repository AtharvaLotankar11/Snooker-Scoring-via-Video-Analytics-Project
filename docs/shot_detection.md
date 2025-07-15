## YOLOv8 Training Fix (2025-06-26)
- Issue: FileNotFoundError in `train_yolo.py` due to incorrect `data.yaml` paths.
- Fix: Updated `train` and `val` to `./yolo_data/images`, set `nc: 1`, `names: ['cue_ball']`.
- Scripts: `train_yolo.py`, `test_yolo.py`
- Outputs: Model at `runs/detect/cue_ball_model/weights/best.pt`, detected bbox [195, 145, 20, 20].