from ultralytics import YOLO
import cv2
import time

# Load your YOLO model
model = YOLO("best.pt")  # Update path if needed

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# FPS calculation
prev_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run YOLO detection (uses GPU automatically)
    results = model.predict(source=frame, imgsz=640, conf=0.25)

    # Draw results on frame
    for result in results:
        annotated_frame = result.plot()

    # FPS overlay
    current_time = time.time()
    fps = 1 / (current_time - prev_time) if prev_time != 0 else 0
    prev_time = current_time

    cv2.putText(annotated_frame, f"FPS: {fps:.2f}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Show
    cv2.imshow("YOLO Webcam - GPU + FPS", annotated_frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
