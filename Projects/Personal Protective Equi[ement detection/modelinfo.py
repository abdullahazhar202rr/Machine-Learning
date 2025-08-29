from ultralytics import YOLO

# Load the trained model (best.pt)
model = YOLO('all.pt')

# Display model summary (model architecture, number of parameters)
model.info()

# Check the classes the model was trained on
print("Classes: ", model.names)
