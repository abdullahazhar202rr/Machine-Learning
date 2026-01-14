# utils.py - Utility functions for picture checker

import math
import cv2
import numpy as np

def calculate_angle(p1, p2):
    """Calculate angle between two points in degrees"""
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))

def calculate_distance(p1, p2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def get_head_pose(landmarks, img_width, img_height):
    """
    Calculate head pose angles (pitch, yaw, roll) from facial landmarks
    Returns: (pitch, yaw, roll) in degrees
    """
    # Key facial landmarks for pose estimation
    nose_tip = np.array([landmarks[1].x * img_width, landmarks[1].y * img_height])
    nose_bridge = np.array([landmarks[168].x * img_width, landmarks[168].y * img_height])
    left_eye = np.array([landmarks[33].x * img_width, landmarks[33].y * img_height])
    right_eye = np.array([landmarks[263].x * img_width, landmarks[263].y * img_height])
    left_mouth = np.array([landmarks[61].x * img_width, landmarks[61].y * img_height])
    right_mouth = np.array([landmarks[291].x * img_width, landmarks[291].y * img_height])
    
    # Calculate roll (head tilt left/right)
    roll = calculate_angle(left_eye, right_eye)
    
    # Calculate yaw (head rotation left/right)
    # Using the horizontal distance between nose and eye centers
    eye_center_x = (left_eye[0] + right_eye[0]) / 2
    mouth_center_x = (left_mouth[0] + right_mouth[0]) / 2
    face_center_x = (eye_center_x + mouth_center_x) / 2
    
    # Normalized yaw estimation
    face_width = calculate_distance(left_eye, right_eye)
    nose_offset = (nose_tip[0] - face_center_x) / face_width
    yaw = nose_offset * 60  # Scale factor for yaw
    
    # Calculate pitch (head tilt up/down)
    eye_center_y = (left_eye[1] + right_eye[1]) / 2
    mouth_center_y = (left_mouth[1] + right_mouth[1]) / 2
    face_height = abs(mouth_center_y - eye_center_y)
    
    nose_vertical_offset = (nose_tip[1] - eye_center_y) / face_height
    pitch = (nose_vertical_offset - 0.5) * 60  # Scale and adjust for pitch
    
    return pitch, yaw, roll

def get_mouth_openness(landmarks):
    """
    Calculate mouth openness ratio
    Returns: normalized distance (0 = closed, higher = more open)
    """
    # Upper and lower lip landmarks
    upper_lip = landmarks[13]
    lower_lip = landmarks[14]
    
    # Vertical distance between lips
    mouth_distance = abs(upper_lip.y - lower_lip.y)
    
    # Normalize by face height (distance between eyes and chin)
    left_eye = landmarks[33]
    chin = landmarks[152]
    face_height = abs(chin.y - left_eye.y)
    
    normalized_distance = mouth_distance / face_height if face_height > 0 else 0
    
    return normalized_distance

def get_face_size_ratio(detection, img_width, img_height):
    """
    Calculate the ratio of face size to image size
    """
    bbox = detection.location_data.relative_bounding_box
    face_area = bbox.width * bbox.height
    return face_area

def draw_text_with_background(img, text, position, font_scale=0.7, thickness=2, 
                              text_color=(255, 255, 255), bg_color=(0, 0, 0)):
    """Draw text with background for better visibility"""
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # Get text size
    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    # Draw background rectangle
    x, y = position
    cv2.rectangle(img, (x, y - text_height - 10), (x + text_width + 10, y + 5), bg_color, -1)
    
    # Draw text
    cv2.putText(img, text, (x + 5, y - 5), font, font_scale, text_color, thickness)
    
    return img

def log_result(filename, status, issues):
    """Log validation result to file"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open("logs/check_logs.txt", "a") as f:
        f.write(f"[{timestamp}] {filename}: {status}\n")
        if issues:
            for issue in issues:
                f.write(f"  - {issue}\n")
        f.write("\n")