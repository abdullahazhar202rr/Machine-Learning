from ultralytics import YOLO
import cv2
import pygame
import time
import os

pygame.mixer.init()

USE_TIME_BASED = True
USE_FRAME_BASED = True
GRACE_PERIOD = 2  # Seconds to wait before resetting alert after detection lost
FIRE_TIME_THRESHOLD = 4  # Seconds fire must be detected before alert
SMOKE_TIME_THRESHOLD = 5  # Seconds smoke must be detected before alert
FIRE_FRAME_THRESHOLD = 120  # approx 4 seconds at 30 FPS
SMOKE_FRAME_THRESHOLD = 150  # approx 5 seconds

model = YOLO("11.pt")
capture = cv2.VideoCapture(0)

if not capture.isOpened():
    print("Error: Could not open video source.")
    exit()

def play_alert_sound():
    pygame.mixer.music.load('alert_sound.mp3')
    pygame.mixer.music.play()

fire_first_time = None
smoke_first_time = None
fire_last_time = None
smoke_last_time = None

fire_frame_count = 0
smoke_frame_count = 0

alert_sent_fire = False
alert_sent_smoke = False

prev_time = time.time()

while True:
    isTrue, frame = capture.read()
    current_time = time.time()

    if isTrue:
        results = model.predict(source=frame, imgsz=640, conf=0.5, show=False)
        detections = results[0].boxes
        fire_detected = False
        smoke_detected = False
        filtered_boxes = []

        for box in detections:
            class_index = int(box.cls)
            confidence = box.conf

            # Increased confidence thresholds for robustness
            if class_index == 0 and confidence > 0.5:
                fire_detected = True
                filtered_boxes.append(box)
            elif class_index == 1 and confidence > 0.5:
                smoke_detected = True
                filtered_boxes.append(box)

        # Time-based detection logic
        if USE_TIME_BASED:
            if fire_detected:
                if fire_first_time is None:
                    fire_first_time = current_time
                fire_last_time = current_time
            if smoke_detected:
                if smoke_first_time is None:
                    smoke_first_time = current_time
                smoke_last_time = current_time

        # Frame-based detection count (do NOT reset alerts here)
        if USE_FRAME_BASED:
            fire_frame_count = fire_frame_count + 1 if fire_detected else 0
            smoke_frame_count = smoke_frame_count + 1 if smoke_detected else 0

        # Reset alert flags only if detection has been lost for GRACE_PERIOD seconds
        if fire_last_time and (current_time - fire_last_time > GRACE_PERIOD):
            alert_sent_fire = False
            fire_first_time = None
            fire_last_time = None
            fire_frame_count = 0

        if smoke_last_time and (current_time - smoke_last_time > GRACE_PERIOD):
            alert_sent_smoke = False
            smoke_first_time = None
            smoke_last_time = None
            smoke_frame_count = 0

        # Fire alert trigger
        trigger_fire_alert = False
        if USE_TIME_BASED and fire_first_time:
            if (current_time - fire_first_time >= FIRE_TIME_THRESHOLD) and not alert_sent_fire:
                trigger_fire_alert = True
        if USE_FRAME_BASED:
            if fire_frame_count >= FIRE_FRAME_THRESHOLD and not alert_sent_fire:
                trigger_fire_alert = True

        if trigger_fire_alert:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"./fire_detected_{timestamp}.jpg"
            results[0].boxes = filtered_boxes
            annotated_frame = results[0].plot()
            cv2.imwrite(screenshot_path, annotated_frame)
            play_alert_sound()
            alert_sent_fire = True
            print(f"🔥 Fire alert triggered. Screenshot saved: {screenshot_path}")

        # Smoke alert trigger
        trigger_smoke_alert = False
        if USE_TIME_BASED and smoke_first_time:
            if (current_time - smoke_first_time >= SMOKE_TIME_THRESHOLD) and not alert_sent_smoke:
                trigger_smoke_alert = True
        if USE_FRAME_BASED:
            if smoke_frame_count >= SMOKE_FRAME_THRESHOLD and not alert_sent_smoke:
                trigger_smoke_alert = True

        if trigger_smoke_alert:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"./smoke_detected_{timestamp}.jpg"
            results[0].boxes = filtered_boxes
            annotated_frame = results[0].plot()
            cv2.imwrite(screenshot_path, annotated_frame)
            play_alert_sound()
            alert_sent_smoke = True
            print(f"💨 Smoke alert triggered. Screenshot saved: {screenshot_path}")

        # Calculate FPS
        fps = 1 / (current_time - prev_time)
        prev_time = current_time

        # Annotate FPS on frame before displaying
        results[0].boxes = filtered_boxes
        annotated_frame = results[0].plot()

        cv2.putText(
            annotated_frame,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        cv2.imshow('YOLOv8 Webcam', annotated_frame)

        if cv2.waitKey(5) & 0xFF == ord('d'):
            break
    else:
        break

capture.release()
cv2.destroyAllWindows()
