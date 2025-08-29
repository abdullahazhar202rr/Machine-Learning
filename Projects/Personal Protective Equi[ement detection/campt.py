from ultralytics import YOLO
import cv2, time

# Load trained PPE model
model = YOLO("all.pt")

# Open webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # reduce if FPS is low
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("❌ Cannot access webcam")
    exit()

prev_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # YOLO inference (FP16 + smaller imgsz for speed)
    results = model(frame, stream=True, half=True, imgsz=480)

    # Annotate detections
    for r in results:
        annotated_frame = r.plot()

    # FPS calculation
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if prev_time else 0
    prev_time = curr_time
    cv2.putText(annotated_frame, f"FPS: {int(fps)}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("PPE Detection - Webcam", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
