# checker.py - Core validation logic for picture checker

import cv2
import mediapipe as mp
from utils import (get_head_pose, get_mouth_openness, get_face_size_ratio, 
                   draw_text_with_background, log_result)
from config import *

class PictureChecker:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, 
            min_detection_confidence=MIN_DETECTION_CONFIDENCE
        )
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=2,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE
        )
    
    def validate_image(self, image, draw_feedback=True):
        """
        Validate image according to requirements
        Returns: (is_valid, issues, annotated_image)
        """
        issues = []
        img_height, img_width = image.shape[:2]
        
        # Convert to RGB for MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Step 1: Detect faces
        detection_results = self.face_detection.process(image_rgb)
        
        if not detection_results.detections:
            issues.append(MSG_NO_FACE)
            if draw_feedback:
                image = draw_text_with_background(image, MSG_NO_FACE, (20, 50), 
                                                  bg_color=COLOR_ERROR)
            return False, issues, image
        
        if len(detection_results.detections) > 1:
            issues.append(MSG_MULTIPLE_FACES)
            if draw_feedback:
                image = draw_text_with_background(image, MSG_MULTIPLE_FACES, (20, 50), 
                                                  bg_color=COLOR_ERROR)
            return False, issues, image
        
        # Step 2: Check face size
        face_size_ratio = get_face_size_ratio(detection_results.detections[0], img_width, img_height)
        
        if face_size_ratio < MIN_FACE_SIZE_RATIO:
            issues.append(MSG_FACE_TOO_SMALL)
        elif face_size_ratio > MAX_FACE_SIZE_RATIO:
            issues.append(MSG_FACE_TOO_LARGE)
        
        # Step 3: Get facial landmarks
        mesh_results = self.face_mesh.process(image_rgb)
        
        if not mesh_results.multi_face_landmarks:
            issues.append("Could not detect facial features")
            return False, issues, image
        
        landmarks = mesh_results.multi_face_landmarks[0].landmark
        
        # Step 4: Check head pose
        pitch, yaw, roll = get_head_pose(landmarks, img_width, img_height)
        
        if abs(roll) > MAX_TILT_ANGLE:
            issues.append(f"{MSG_HEAD_TILTED} ({abs(roll):.1f}°)")
        
        if abs(yaw) > MAX_YAW_ANGLE:
            issues.append(f"{MSG_HEAD_YAW} ({abs(yaw):.1f}°)")
        
        if abs(pitch) > MAX_PITCH_ANGLE:
            issues.append(f"{MSG_HEAD_PITCH} ({abs(pitch):.1f}°)")
        
        # Step 5: Check mouth openness
        mouth_openness = get_mouth_openness(landmarks)
        
        if mouth_openness > MAX_MOUTH_OPEN:
            issues.append(MSG_MOUTH_OPEN)
        
        # Draw feedback on image
        if draw_feedback:
            y_offset = 50
            if not issues:
                image = draw_text_with_background(image, MSG_SUCCESS, (20, y_offset), 
                                                  bg_color=COLOR_SUCCESS)
            else:
                for issue in issues:
                    color = COLOR_WARNING if len(issues) <= 2 else COLOR_ERROR
                    image = draw_text_with_background(image, issue, (20, y_offset), 
                                                      bg_color=color)
                    y_offset += 40
            
            # Draw debug info
            debug_text = f"Tilt: {abs(roll):.1f}° | Yaw: {abs(yaw):.1f}° | Pitch: {abs(pitch):.1f}°"
            image = draw_text_with_background(image, debug_text, (20, img_height - 30), 
                                             font_scale=0.5, bg_color=(50, 50, 50))
        
        is_valid = len(issues) == 0
        return is_valid, issues, image
    
    def validate_from_file(self, image_path):
        """Validate image from file path"""
        image = cv2.imread(image_path)
        if image is None:
            return False, ["Could not load image"], None
        
        is_valid, issues, annotated_image = self.validate_image(image)
        
        # Log result
        log_result(image_path, "APPROVED" if is_valid else "REJECTED", issues)
        
        return is_valid, issues, annotated_image
    
    def close(self):
        """Release resources"""
        self.face_detection.close()
        self.face_mesh.close()