from ultralytics import YOLO
import cv2, time

# Load trained PPE model
model = YOLO("all.pt")

# Open video file (replace 'your_video.mp4' with the path to your video file)
video_path = 'video.mp4'
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("❌ Cannot access video file")
    exit()

# Get video properties for saving the output video
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps_video = cap.get(cv2.CAP_PROP_FPS)

# Create VideoWriter to save output video (change output file name if needed)
output_path = 'output_video.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4
out = cv2.VideoWriter(output_path, fourcc, fps_video, (frame_width, frame_height))

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

    # Display the annotated video frame
    cv2.imshow("PPE Detection - Video", annotated_frame)

    # Write the annotated frame to the output video
    out.write(annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
        break

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()
