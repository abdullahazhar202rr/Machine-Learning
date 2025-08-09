from ultralytics import YOLO
import cv2

# Load your trained YOLOv8 model
model = YOLO("11.pt") 

# ======================
# IMAGE INFERENCE
# ======================
def run_image_inference(image_path, conf=0.5):
    results = model.predict(
        source=image_path,
        imgsz=640,
        conf=conf,
        save=True,  
        show=True    
    )
    print("Image inference done. Saved to /runs/detect/")

# ======================
# VIDEO INFERENCE
# ======================
def run_video_inference(video_path, fire_conf=0.55, smoke_conf=0.75):
    capture = cv2.VideoCapture(video_path)

    if not capture.isOpened():
        print(f"Error: Could not open video source: {video_path}")
        return

    delay = 1  # Adjust for display speed

    while True:
        isTrue, frame = capture.read()
        if not isTrue:
            break

        # Run inference on the current frame
        results = model.predict(
            source=frame,
            imgsz=640,
            conf=min(fire_conf, smoke_conf),  # Use min to catch both classes
            show=False
        )

        # Get YOLO detections
        detections = results[0].boxes

        # Filter detections: only keep boxes matching fire/smoke thresholds
        filtered_boxes = []
        for box in detections:
            class_index = int(box.cls)
            confidence = float(box.conf)

            if class_index == 0 and confidence >= fire_conf:  # Fire
                filtered_boxes.append(box)
            elif class_index == 1 and confidence >= smoke_conf:  # Smoke
                filtered_boxes.append(box)

        # Overwrite results with filtered detections
        results[0].boxes = filtered_boxes

        # Draw results on frame
        annotated_frame = results[0].plot()

        # Show the frame
        cv2.imshow("YOLOv8 Fire & Smoke Detection", annotated_frame)

        # Press 'q' to quit
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break

    capture.release()
    cv2.destroyAllWindows()
    print("Video inference complete.")

# ======================
# RUN
# ======================

if __name__ == "__main__":
    # ---- IMAGE ----
    run_image_inference("check2.jpg")

    # ---- VIDEO ----
    # Uncomment to test video
    # run_video_inference("test_videos/smoke.mp4")

