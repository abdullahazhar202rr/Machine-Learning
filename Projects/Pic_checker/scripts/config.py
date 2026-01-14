# config.py - Configuration settings for picture checker

# Thresholds for validation
MAX_TILT_ANGLE = 10      # Maximum allowed head tilt in degrees
MAX_YAW_ANGLE = 15       # Maximum left/right rotation in degrees
MAX_PITCH_ANGLE = 15     # Maximum up/down rotation in degrees
MAX_MOUTH_OPEN = 0.03    # Maximum normalized distance for closed mouth

# Detection confidence
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# Image settings
MIN_FACE_SIZE_RATIO = 0.08  # Minimum face size relative to image (lowered for more flexibility)
MAX_FACE_SIZE_RATIO = 0.85  # Maximum face size relative to image

# Colors for GUI (BGR format)
COLOR_SUCCESS = (0, 255, 0)
COLOR_WARNING = (0, 165, 255)
COLOR_ERROR = (0, 0, 255)
COLOR_TEXT = (255, 255, 255)

# Validation messages
MSG_NO_FACE = "No face detected"
MSG_MULTIPLE_FACES = "Multiple faces detected - only one person allowed"
MSG_HEAD_TILTED = "Head is tilted - keep it straight"
MSG_HEAD_YAW = "Turn your face forward"
MSG_HEAD_PITCH = "Look straight ahead"
MSG_MOUTH_OPEN = "Close your mouth"
MSG_FACE_TOO_SMALL = "Move closer to camera"
MSG_FACE_TOO_LARGE = "Move away from camera"
MSG_SUCCESS = "Perfect! Picture approved"