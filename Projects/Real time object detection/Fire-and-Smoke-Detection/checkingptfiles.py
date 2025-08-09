from ultralytics import YOLO

# Load your best.pt
model = YOLO("best (1).pt")

# Show model info
print(model.names)   # class names
print(f"Number of classes: {len(model.names)}")




