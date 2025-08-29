import cv2
from ultralytics import YOLO
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- CONFIG ----------------
VIDEO_SOURCE = "video2.mp4"  # or 0 for webcam
MODEL_PATH = "best(2).pt"
FRAME_WIDTH, FRAME_HEIGHT = 640, 480
LINE_OUTER = 150  # Green line (outer, entrance)
LINE_INNER = 350  # Red line (inner, shop)
LINE_RANGE = 10   # Range for line crossing
CONF_THRESHOLD = 0.5  # Detection confidence
MIN_FRAMES = 5    # Min frames for stable track
MIN_BOX_AREA = 500  # Min box area to filter noise
LOG_FILE = "people_counts.log"
FPS_DISPLAY = True
# ---------------------------------------

try:
    model = YOLO(MODEL_PATH)
    logger.info(f"Loaded model: {MODEL_PATH}")
except Exception as e:
    logger.error(f"Failed to load model {MODEL_PATH}: {e}")
    exit(1)

# Counters
total_enter = 0
total_exit = 0
current_people = 0

# Tracking dictionaries
tracker_positions = {}   # {person_id: last_y}
person_state = {}        # {person_id: "none"/"touched_outer"/"touched_inner"/"counted"}
person_frame_count = {}  # {person_id: frames_seen}

try:
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    logger.info(f"Video source: {VIDEO_SOURCE}, Resolution: {FRAME_WIDTH}x{FRAME_HEIGHT}")
except Exception as e:
    logger.error(f"Failed to initialize video source {VIDEO_SOURCE}: {e}")
    exit(1)

# FPS calculation
prev_time = time.time()
fps = 0

# Log file
try:
    count_log = open(LOG_FILE, 'a')
    logger.info(f"Logging counts to: {LOG_FILE}")
except Exception as e:
    logger.error(f"Failed to open log file {LOG_FILE}: {e}")
    count_log = None

while True:
    ret, frame = cap.read()
    if not ret:
        logger.warning("Failed to read frame. Exiting.")
        break

    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

    # Detection + tracking
    try:
        results = model.track(
            frame,
            tracker="bytetrack.yaml",
            conf=CONF_THRESHOLD,
            iou=0.6,
            persist=True
        )[0]
    except Exception as e:
        logger.error(f"Tracking error: {e}")
        continue

    current_ids = set()

    for box in results.boxes:
        if box.cls is None or int(box.cls[0]) != 0:  # Only person (class 0)
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        box_area = (x2 - x1) * (y2 - y1)
        if box_area < MIN_BOX_AREA:
            continue

        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)

        if box.id is None:
            continue
        person_id = int(box.id[0])
        current_ids.add(person_id)

        prev_cy = tracker_positions.get(person_id, cy)
        state = person_state.get(person_id, "none")
        frames_seen = person_frame_count.get(person_id, 0) + 1
        person_frame_count[person_id] = frames_seen

        # ---------------- STATE MACHINE ----------------
        if state == "none":
            if abs(cy - LINE_OUTER) <= LINE_RANGE:
                person_state[person_id] = "touched_outer"
            elif abs(cy - LINE_INNER) <= LINE_RANGE:
                person_state[person_id] = "touched_inner"

        elif state == "touched_outer":
            # Outer (green) → Inner (red) = Enter
            if cy > prev_cy and cy > LINE_INNER and prev_cy <= LINE_INNER and frames_seen >= MIN_FRAMES:
                total_enter += 1
                current_people += 1
                person_state[person_id] = "counted"
                logger.info(f"Enter detected: ID {person_id}, Total Enter: {total_enter}, Current: {current_people}")
                if count_log:
                    count_log.write(f"{time.time()}: Enter, Total: {total_enter}, Current: {current_people}\n")
                    count_log.flush()

        elif state == "touched_inner":
            # Inner (red) → Outer (green) = Exit
            if cy < prev_cy and cy < LINE_OUTER and prev_cy >= LINE_OUTER and frames_seen >= MIN_FRAMES:
                total_exit += 1
                if current_people > 0:
                    current_people -= 1
                person_state[person_id] = "counted"
                logger.info(f"Exit detected: ID {person_id}, Total Exit: {total_exit}, Current: {current_people}")
                if count_log:
                    count_log.write(f"{time.time()}: Exit, Total: {total_exit}, Current: {current_people}\n")
                    count_log.flush()

        tracker_positions[person_id] = cy

        # Draw bbox + ID
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 3, (0, 255, 255), -1)
        cv2.putText(frame, f"ID:{person_id}", (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Clean up lost trackers
    all_keys = set(tracker_positions) | set(person_state) | set(person_frame_count)
    for pid in list(all_keys):
        if pid not in current_ids:
            tracker_positions.pop(pid, None)
            person_state.pop(pid, None)
            person_frame_count.pop(pid, None)

    # Draw lines
    cv2.line(frame, (0, LINE_OUTER), (FRAME_WIDTH, LINE_OUTER), (0, 255, 0), 2)
    cv2.line(frame, (0, LINE_INNER), (FRAME_WIDTH, LINE_INNER), (0, 0, 255), 2)

    # Overlay counters
    cv2.putText(frame, f"Enter: {total_enter}", (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f"Exit: {total_exit}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(frame, f"Current: {current_people}", (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # FPS display
    if FPS_DISPLAY:
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time)
        prev_time = curr_time
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    cv2.imshow("People Counter", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
if count_log:
    count_log.close()
logger.info("Application stopped.")