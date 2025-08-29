import cv2
from ultralytics import YOLO
import time

# Load your trained YOLOv8n model
model = YOLO("best(2).pt")  # path to your trained weights

# Choose video source
# 0 = default webcam, or replace with video file path
source = 0  
cap = cv2.VideoCapture(source)

# Get original video dimensions
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Optional: Resize for faster FPS
resize_width = 640
resize_height = int(height * (resize_width / width))

# FPS calculation
prev_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Resize frame for speed
    frame_resized = cv2.resize(frame, (resize_width, resize_height))

    # Inference
    results = model.predict(frame_resized, verbose=False,conf=0.7)

    # Draw boxes and labels
    annotated_frame = results[0].plot()

    # Calculate FPS
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    cv2.putText(
        annotated_frame,
        f"FPS: {fps:.2f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
    )

    # Show frame
    cv2.imshow("YOLOv8 People Detection", annotated_frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
