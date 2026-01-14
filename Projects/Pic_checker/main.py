# picture-checker-api/app.py
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import cv2
import numpy as np
import base64
import os
import tempfile
from datetime import datetime
import sys
import json
import time

# Add scripts directory to Python path
scripts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, scripts_path)

from checker import PictureChecker
from config import *

app = Flask(__name__)
CORS(app)

# Initialize the checker
checker = PictureChecker()

# Create directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("approved", exist_ok=True)

def base64_to_image(base64_string):
    """Convert base64 string to OpenCV image"""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error decoding base64: {e}")
        return None

def image_to_base64(image):
    """Convert OpenCV image to base64 string"""
    try:
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_str = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        print(f"Error encoding to base64: {e}")
        return None

def get_feedback_messages(issues, is_valid):
    """Convert issues list to feedback messages"""
    feedback = []
    
    if not is_valid:
        for issue in issues:
            if "No face" in issue:
                feedback.append("❌ No face detected - Position yourself in center")
            elif "Multiple faces" in issue:
                feedback.append("⚠️ Multiple faces detected - Ensure only one person is in frame")
            elif "tilted" in issue.lower():
                feedback.append("⚠️ Head is tilted - Keep your head straight")
            elif "turn" in issue.lower() or "yaw" in issue.lower():
                feedback.append("⚠️ Turn your face forward - Look straight at camera")
            elif "look straight" in issue.lower():
                feedback.append("⚠️ Look straight ahead - Don't look up or down")
            elif "mouth" in issue.lower():
                feedback.append("⚠️ Close your mouth for professional photo")
            elif "too small" in issue.lower():
                feedback.append("⚠️ Move closer to camera - Face is too small")
            elif "too large" in issue.lower():
                feedback.append("⚠️ Move away from camera - Face is too large")
            else:
                feedback.append(f"⚠️ {issue}")
    else:
        feedback = [
            "✅ Single face detected - Good!",
            "✅ Head straight - Perfect!",
            "✅ Looking straight - Good eye contact!",
            "✅ Mouth closed - Professional!",
            "✅ Good lighting and clear image"
        ]
    
    return feedback

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'picture-validator',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/validate-image', methods=['POST'])
def validate_image():
    """Validate an uploaded image"""
    try:
        data = request.json
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'No image data provided'
            }), 400
        
        # Get image data
        image_data = data['image']
        
        # Convert base64 to image
        image = base64_to_image(image_data)
        if image is None:
            return jsonify({
                'success': False,
                'error': 'Invalid image data'
            }), 400
        
        # Get mode (webcam or upload)
        mode = data.get('mode', 'upload')
        draw_feedback = data.get('draw_feedback', True)
        
        # Validate image using your existing checker
        is_valid, issues, annotated_image = checker.validate_image(image, draw_feedback=draw_feedback)
        
        # Save to uploads folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        upload_filename = f"uploads/{timestamp}_{mode}.jpg"
        cv2.imwrite(upload_filename, image)
        
        # If valid, save to approved folder
        if is_valid:
            approved_filename = f"approved/{timestamp}_approved.jpg"
            cv2.imwrite(approved_filename, image)
        
        # Convert annotated image to base64
        annotated_base64 = image_to_base64(annotated_image)
        
        # Generate feedback messages
        feedback = get_feedback_messages(issues, is_valid)
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'issues': issues,
            'feedback': feedback,
            'annotated_image': annotated_base64,
            'upload_path': upload_filename,
            'approved_path': f"approved/{timestamp}_approved.jpg" if is_valid else None,
            'timestamp': timestamp,
            'mode': mode
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/validate-webcam-frame', methods=['POST'])
def validate_webcam_frame():
    """Validate webcam frame with real-time feedback"""
    try:
        data = request.json
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'No image data provided'
            }), 400
        
        # Convert base64 to image
        image = base64_to_image(data['image'])
        if image is None:
            return jsonify({
                'success': False,
                'error': 'Invalid image data'
            }), 400
        
        # Validate with real-time feedback (always draw feedback for webcam)
        is_valid, issues, annotated_image = checker.validate_image(image, draw_feedback=True)
        
        # Convert annotated image to base64
        annotated_base64 = image_to_base64(annotated_image)
        
        # Generate real-time feedback messages
        feedback = get_feedback_messages(issues, is_valid)
        
        # Generate specific real-time instructions
        realtime_feedback = []
        
        # Check each issue for specific guidance
        for issue in issues:
            if "No face" in issue:
                realtime_feedback.append("❌ No face detected - Move into frame")
            elif "Multiple faces" in issue:
                realtime_feedback.append("⚠️ Multiple faces - Ensure only you are visible")
            elif "tilted" in issue.lower():
                if "left" in issue.lower():
                    realtime_feedback.append("⚠️ Head tilted left - Straighten to right")
                elif "right" in issue.lower():
                    realtime_feedback.append("⚠️ Head tilted right - Straighten to left")
                else:
                    realtime_feedback.append("⚠️ Head is tilted - Keep head straight")
            elif "yaw" in issue.lower() or "turn" in issue.lower():
                realtime_feedback.append("⚠️ Face not straight - Look directly at camera")
            elif "mouth" in issue.lower():
                realtime_feedback.append("⚠️ Mouth is open - Close your mouth")
            elif "too small" in issue.lower():
                realtime_feedback.append("⚠️ Move closer - Face is too small")
            elif "too large" in issue.lower():
                realtime_feedback.append("⚠️ Move back - Face is too large")
        
        # If no issues but not perfect yet
        if not issues and not is_valid:
            realtime_feedback.append("✅ Good start! Keep adjusting...")
        
        # If valid, show success messages
        if is_valid:
            realtime_feedback = [
                "✅ Perfect! Single face detected",
                "✅ Head is straight",
                "✅ Looking directly at camera",
                "✅ Mouth is closed",
                "✅ Good lighting and position"
            ]
        
        # If we have no realtime feedback yet but have issues
        if not realtime_feedback and issues:
            realtime_feedback = [f"⚠️ {issue}" for issue in issues]
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'issues': issues,
            'feedback': feedback,
            'realtime_feedback': realtime_feedback,
            'annotated_image': annotated_base64,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get-validation-status', methods=['GET'])
def get_validation_status():
    """Get current validation system status"""
    return jsonify({
        'success': True,
        'status': 'running',
        'model': 'PictureChecker',
        'requirements': [
            "Exactly one person in frame",
            "Face looking straight at camera",
            "Head not tilted left or right",
            "Mouth closed",
            "Good lighting and clear image"
        ]
    })

@app.route('/api/get-guidelines', methods=['GET'])
def get_guidelines():
    """Get picture validation guidelines"""
    return jsonify({
        'success': True,
        'guidelines': {
            'general': [
                "Stand in front of a plain background",
                "Use good, even lighting",
                "Wear professional attire",
                "Make sure only you are in the frame"
            ],
            'position': [
                "Look directly at the camera",
                "Keep your head straight (no tilt)",
                "Position your face in the center",
                "Keep shoulders level"
            ],
            'expression': [
                "Keep your mouth closed",
                "Maintain a neutral or slight smile",
                "Keep eyes open and natural",
                "Relax your facial muscles"
            ],
            'technical': [
                "Camera at eye level",
                "Good resolution and focus",
                "No red eye or glare",
                "Natural skin tones"
            ]
        }
    })

@app.route('/api/save-approved-image', methods=['POST'])
def save_approved_image():
    """Save an approved image"""
    try:
        data = request.json
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'No image data provided'
            }), 400
        
        image = base64_to_image(data['image'])
        if image is None:
            return jsonify({
                'success': False,
                'error': 'Invalid image data'
            }), 400
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"approved/professional_{timestamp}.jpg"
        cv2.imwrite(filename, image)
        
        return jsonify({
            'success': True,
            'message': 'Image saved successfully',
            'filename': filename,
            'path': os.path.abspath(filename)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analyze-pose', methods=['POST'])
def analyze_pose():
    """Detailed pose analysis for debugging"""
    try:
        data = request.json
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'No image data provided'
            }), 400
        
        image = base64_to_image(data['image'])
        if image is None:
            return jsonify({
                'success': False,
                'error': 'Invalid image data'
            }), 400
        
        # Your existing validation logic
        is_valid, issues, annotated_image = checker.validate_image(image, draw_feedback=True)
        
        # Get image dimensions
        img_height, img_width = image.shape[:2]
        
        # Convert to RGB for MediaPipe
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect faces for face count
        detection_results = checker.face_detection.process(image_rgb)
        num_faces = len(detection_results.detections) if detection_results.detections else 0
        
        # Get face mesh for detailed analysis
        mesh_results = checker.face_mesh.process(image_rgb)
        
        pose_analysis = {
            'num_faces': num_faces,
            'is_valid': is_valid,
            'issues': issues,
            'face_detected': num_faces > 0,
            'single_face': num_faces == 1
        }
        
        if mesh_results.multi_face_landmarks:
            landmarks = mesh_results.multi_face_landmarks[0].landmark
            
            # Import utilities
            from utils import get_head_pose, get_mouth_openness, get_face_size_ratio
            
            # Get detailed measurements
            pitch, yaw, roll = get_head_pose(landmarks, img_width, img_height)
            mouth_openness = get_mouth_openness(landmarks)
            
            pose_analysis.update({
                'head_pitch': float(pitch),
                'head_yaw': float(yaw),
                'head_roll': float(roll),
                'mouth_openness': float(mouth_openness),
                'head_tilt_detected': abs(roll) > MAX_TILT_ANGLE,
                'head_yaw_detected': abs(yaw) > MAX_YAW_ANGLE,
                'head_pitch_detected': abs(pitch) > MAX_PITCH_ANGLE,
                'mouth_open_detected': mouth_openness > MAX_MOUTH_OPEN
            })
        
        return jsonify({
            'success': True,
            'analysis': pose_analysis,
            'annotated_image': image_to_base64(annotated_image) if annotated_image is not None else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 PROFESSIONAL PICTURE VALIDATOR API")
    print("=" * 60)
    print("📁 Uploads directory:", os.path.abspath("uploads"))
    print("✅ Approved directory:", os.path.abspath("approved"))
    print("🌐 API URL: http://localhost:5001")
    print("📋 Health check: GET /api/health")
    print("📸 Webcam validation: POST /api/validate-webcam-frame")
    print("🖼️ Image validation: POST /api/validate-image")
    print("🔧 Pose analysis: POST /api/analyze-pose")
    print("=" * 60)
    print("✅ Ready to validate professional pictures!")
    print("=" * 60)
    
    app.run(debug=True, port=5001, host='0.0.0.0')