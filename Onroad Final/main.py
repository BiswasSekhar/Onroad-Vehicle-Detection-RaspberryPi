import cv2
import numpy as np
import time
import os
from picamera2 import Picamera2
from utils import (
    load_classes, 
    get_output_layers, 
    process_detections, 
    initialize_oled, 
    update_oled_display
)
from config import *
from data_logger import VehicleDataLogger

def setup_camera():
    """Initialize and configure the Raspberry Pi camera"""
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"},
        controls={"FrameRate": CAMERA_FRAMERATE}
    )
    picam2.configure(config)
    return picam2

def load_network():
    """Load YOLO network from disk"""
    # Check if model files exist
    if not os.path.exists(MODEL_PATH) or not os.path.exists(CONFIG_PATH):
        print("Error: Model files not found. Please download them first.")
        print("Run download_models.py to fetch the required files.")
        exit(1)
        
    # Load YOLO network
    net = cv2.dnn.readNet(MODEL_PATH, CONFIG_PATH)
    
    # Use GPU if available
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)  # Change to DNN_TARGET_OPENCL for GPU
    
    print("Neural network loaded successfully")
    return net

def main():
    # Create required directories
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    
    # Load COCO class names
    classes = load_classes(CLASSES_PATH)
    
    # Load neural network
    net = load_network()
    
    # Initialize OLED display
    if ENABLE_OLED:
        oled_display = initialize_oled()
    
    # Initialize data logger if enabled
    data_logger = None
    if LOG_DETECTIONS:
        data_logger = VehicleDataLogger()
    
    # Initialize camera
    print("Setting up camera...")
    picam2 = setup_camera()
    picam2.start()
    time.sleep(2)  # Give camera time to warm up
    
    print("Vehicle detection started! Press 'q' to quit.")
    
    try:
        while True:
            start_time = time.time()
            
            # Capture frame from camera
            frame = picam2.capture_array()
            
            # Create a 4D blob from the frame
            blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
            
            # Set the input blob for the neural network
            net.setInput(blob)
            
            # Run forward pass to get output of the output layers
            outs = net.forward(get_output_layers(net))
            
            # Process detections
            processed_frame, vehicle_count, vehicle_types = process_detections(
                frame, outs, classes, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
            
            # Calculate FPS
            fps = 1.0 / (time.time() - start_time)
            cv2.putText(processed_frame, f"FPS: {fps:.1f}", (10, 60), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Update OLED display
            if ENABLE_OLED:
                update_oled_display(vehicle_count, vehicle_types, fps)
            
            # Log vehicle data
            if LOG_DETECTIONS and data_logger:
                data_logger.log_data(vehicle_count, vehicle_types, fps)
            
            # Display the resulting frame
            if ENABLE_PREVIEW:
                cv2.imshow("Vehicle Detection", processed_frame)
                
            # Break the loop if 'q' pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("Stopping detection...")
    
    finally:
        picam2.stop()
        cv2.destroyAllWindows()
        print("Vehicle detection stopped.")

if __name__ == "__main__":
    main()
