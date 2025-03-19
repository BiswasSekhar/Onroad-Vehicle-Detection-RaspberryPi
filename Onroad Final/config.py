# Configuration settings for vehicle detection

# Camera settings
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FRAMERATE = 30

# Detection settings
CONFIDENCE_THRESHOLD = 0.5
NMS_THRESHOLD = 0.4

# Classes we want to detect (COCO dataset)
VEHICLE_CLASSES = ["bicycle", "car", "motorbike", "bus", "truck"]

# Paths
MODEL_PATH = "/home/pi/Project/Onroad Final/models/yolov4-tiny.weights"
CONFIG_PATH = "/home/pi/Project/Onroad Final/models/yolov4-tiny.cfg"
CLASSES_PATH = "/home/pi/Project/Onroad Final/models/coco.names"

# Display settings
ENABLE_PREVIEW = True
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 600

# OLED Display settings
ENABLE_OLED = True
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C_ADDRESS = 0x3C  # Common address for SSD1306 displays (might be 0x3D for some)
OLED_I2C_BUS = 1  # Default I2C bus on Raspberry Pi

# Logging
LOG_DETECTIONS = True
LOG_PATH = "/home/pi/Project/Onroad Final/logs/detections.log"

# Performance settings
USE_THREADING = True  # Use threading for better performance
DETECTION_INTERVAL = 0  # 0 for every frame, higher for skipping frames
ENABLE_GPU = False  # Set to True if your Pi has GPU support
OPTIMIZE_NETWORK = True  # Apply network optimization techniques
