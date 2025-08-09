from ultralytics import YOLO

# Load a trained YOLO model
model = YOLO('11.pt')  # or yolov5s.pt, or your custom trained model

# Export the model to TensorRT engine format
# The 'engine' format will be generated in the same directory as the original model
model.export(format='engine',  # Specify the target format as 'engine'
             imgsz=640,       # Input image size (can be a single int or a list/tuple for width, height)
             half=True,       # Export with FP16 precision (recommended for performance)
             int8=False,      # Export with INT8 quantization (requires calibration, more advanced)
             dynamic=False)   # Enable dynamic input shapes (can be useful for varying image sizes)