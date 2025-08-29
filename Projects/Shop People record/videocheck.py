import cv2
from ultralytics import YOLO

# ---------------- CONFIG ----------------
VIDEO_SOURCE = "video3.mp4"  # or 0 for webcam
MODEL_PATH = "best(2).pt"
FRAME_WIDTH, FRAME_HEIGHT = 640, 480
LINE_ENTER = 150  # Green line
LINE_EXIT = 350   # Red line
LINE_RANGE = 5    # Range to detect first touch
# ---------------------------------------

model = YOLO(MODEL_PATH)

# Counters
total_enter = 0
total_exit = 0
current_people = 0

# Tracking dictionaries
tracker_positions = {}   # {person_id: last_y}
person_state = {}        # {person_id: "none"/"touched_green"/"touched_red"/"counted"}

cap = cv2.VideoCapture(VIDEO_SOURCE)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

def rotate_if_portrait(frame):
    """ Rotate the frame if it is in portrait mode to make it landscape. """
    h, w = frame.shape[:2]
    if h > w:
        # Rotate 90 degrees clockwise
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    return frame

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Rotate frame to landscape if necessary
    frame = rotate_if_portrait(frame)

    # Resize frame to match desired dimensions
    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    # Detection + tracking
    results = model.track(frame, tracker="bytetrack.yaml")[0]

    for box in results.boxes:
        cls = int(box.cls[0])
        if cls != 0:
            continue  # Only person

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

        if box.id is None:
            continue
        person_id = int(box.id[0])
        prev_cy = tracker_positions.get(person_id, cy)
        state = person_state.get(person_id, "none")

        # ---------------- STATE MACHINE ----------------
        if state == "none":
            # Detect first touch on green or red line
            if LINE_ENTER - LINE_RANGE <= cy <= LINE_ENTER + LINE_RANGE:
                person_state[person_id] = "touched_green"
            elif LINE_EXIT - LINE_RANGE <= cy <= LINE_EXIT + LINE_RANGE:
                person_state[person_id] = "touched_red"

        elif state == "touched_green":
            # Green → Red = Exit
            if prev_cy <= LINE_EXIT and cy > LINE_EXIT:
                total_exit += 1
                if current_people > 0:
                    current_people -= 1
                person_state[person_id] = "counted"

        elif state == "touched_red":
            # Red → Green = Enter
            if prev_cy >= LINE_ENTER and cy < LINE_ENTER:
                total_enter += 1
                current_people += 1
                person_state[person_id] = "counted"

        tracker_positions[person_id] = cy

        # Draw bbox + ID
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 3, (0, 255, 255), -1)
        cv2.putText(frame, f"ID:{person_id}", (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Draw lines
    cv2.line(frame, (0, LINE_ENTER), (FRAME_WIDTH, LINE_ENTER), (0, 255, 0), 2)
    cv2.line(frame, (0, LINE_EXIT), (FRAME_WIDTH, LINE_EXIT), (0, 0, 255), 2)

    # Overlay counters
    cv2.putText(frame, f"Enter: {total_enter}", (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f"Exit: {total_exit}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(frame, f"Current: {current_people}", (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("People Counter", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
