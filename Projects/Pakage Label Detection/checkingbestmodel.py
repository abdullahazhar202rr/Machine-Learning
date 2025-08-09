from ultralytics import YOLO

# ✅ Load your model
model = YOLO('best.pt')

# ✅ Run validation
metrics = model.val(
    data='datasetforyolov8/data.yaml',
    imgsz=640,   # or your training image size
    save=True
)

# ✅ Print all results
print(f"✅ Mean Precision: {metrics.box.mp:.4f}")
print(f"✅ Mean Recall: {metrics.box.mr:.4f}")
print(f"✅ mAP50: {metrics.box.map50:.4f}")
print(f"✅ mAP50-95: {metrics.box.map:.4f}")

print(f"Results saved to: {metrics.save_dir}")
