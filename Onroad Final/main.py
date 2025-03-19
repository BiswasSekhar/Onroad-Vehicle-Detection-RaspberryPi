import cv2
import numpy as np
import time
import os
import threading
import queue
from picamera2 import Picamera2
from utils import (
    load_classes, 
    get_output_layers, 
    process_detections, 
    initialize_oled, 
    update_oled_display
)
# Import all configuration parameters
from config import *
from data_logger import VehicleDataLogger

# Global variables for inter-thread communication
frame_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
result_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
stop_event = threading.Event()
fps_value = 0
processed_fps_value = 0

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
    
    # Use GPU if available and enabled
    if ENABLE_GPU:
        print("Attempting to use GPU for inference")
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
    else:
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    
    print("Neural network loaded successfully")
    return net

def capture_thread(picam):
    """Thread function to continuously capture frames"""
    global frame_queue, stop_event, fps_value
    
    frame_count = 0
    start_time = time.time()
    
    print("Camera capture thread started")
    
    try:
        while not stop_event.is_set():
            # Capture frame
            frame = picam.capture_array()
            
            # Put frame in queue if not full (non-blocking)
            if not frame_queue.full():
                frame_queue.put(frame, block=False)
            
            # Calculate FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:  # Update FPS every second
                fps_value = frame_count / elapsed_time
                frame_count = 0
                start_time = time.time()
                
            # Small sleep to prevent CPU maxing out
            time.sleep(0.001)
    except Exception as e:
        print(f"Error in capture thread: {e}")
    finally:
        print("Camera capture thread stopped")

def inference_thread(net, classes):
    """Thread function to process frames for vehicle detection"""
    global frame_queue, result_queue, stop_event, processed_fps_value
    
    frame_count = 0
    process_count = 0
    start_time = time.time()
    
    print("Inference thread started")
    
    try:
        while not stop_event.is_set():
            # Skip if queue is empty
            if frame_queue.empty():
                time.sleep(0.01)
                continue
            
            # Get a frame from the queue
            frame = frame_queue.get()
            frame_count += 1
            
            # Only process every DETECTION_INTERVAL frames
            if DETECTION_INTERVAL > 1 and frame_count % DETECTION_INTERVAL != 0:
                continue
            
            process_count += 1
            process_start = time.time()
            
            # Create a 4D blob from the frame
            blob = cv2.dnn.blobFromImage(frame, 1/255.0, (BLOB_SIZE, BLOB_SIZE), 
                                         swapRB=True, crop=False)
            
            # Set the input blob for the neural network
            net.setInput(blob)
            
            # Run forward pass to get output of the output layers
            outs = net.forward(get_output_layers(net))
            
            # Process detections
            processed_frame, vehicle_count, vehicle_types = process_detections(
                frame, outs, classes, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
            
            # Add inference time as text
            inference_time = time.time() - process_start
            cv2.putText(processed_frame, f"Infer: {inference_time*1000:.1f}ms", (10, 90), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Add results to output queue if not full
            if not result_queue.full():
                result_queue.put((processed_frame, vehicle_count, vehicle_types, inference_time))
            
            # Calculate processed FPS
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:  # Update FPS every second
                processed_fps_value = process_count / elapsed_time
                process_count = 0
                start_time = time.time()
    except Exception as e:
        print(f"Error in inference thread: {e}")
    finally:
        print("Inference thread stopped")

def display_thread(data_logger):
    """Thread function to display results and update OLED"""
    global result_queue, stop_event, fps_value, processed_fps_value
    
    oled_update_count = 0
    
    print("Display thread started")
    
    try:
        while not stop_event.is_set():
            # Skip if queue is empty
            if result_queue.empty():
                time.sleep(0.01)
                continue
            
            # Get processed results
            processed_frame, vehicle_count, vehicle_types, inference_time = result_queue.get()
            
            # Add FPS information
            cv2.putText(processed_frame, f"Camera: {fps_value:.1f} FPS", (10, 30), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(processed_frame, f"Process: {processed_fps_value:.1f} FPS", (10, 60), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            # Update OLED display - use proper OLED_UPDATE_INTERVAL from config
            if ENABLE_OLED:
                oled_update_count += 1
                # Use modulo to decide when to force an update
                force_update = (oled_update_count % OLED_UPDATE_INTERVAL == 0)
                update_oled_display(vehicle_count, vehicle_types, fps=0, force_update=force_update)
            
            # Log vehicle data
            if LOG_DETECTIONS and data_logger:
                data_logger.log_data(vehicle_count, vehicle_types, processed_fps_value)
            
            # Display the resulting frame
            if ENABLE_PREVIEW:
                cv2.imshow("Vehicle Detection", processed_frame)
                
            # Break the loop if 'q' pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
                break
    except Exception as e:
        print(f"Error in display thread: {e}")
    finally:
        print("Display thread stopped")
        cv2.destroyAllWindows()

def main():
    # Create required directories
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    
    # Load COCO class names
    classes = load_classes(CLASSES_PATH)
    
    # Load neural network
    net = load_network()
    
    # Initialize OLED display
    if ENABLE_OLED:
        initialize_oled()
        # Show starting message on OLED
        update_oled_display(0, {}, 0, True)
    
    # Initialize data logger if enabled
    data_logger = None
    if LOG_DETECTIONS:
        try:
            data_logger = VehicleDataLogger()
        except Exception as e:
            print(f"Warning: Could not initialize data logger: {e}")
    
    # Initialize camera
    print("Setting up camera...")
    picam2 = setup_camera()
    picam2.start()
    time.sleep(2)  # Give camera time to warm up
    
    print("Vehicle detection started! Press 'q' to quit.")
    
    # Start threads if threading is enabled
    if USE_THREADING:
        # Create and start the capture thread
        cap_thread = threading.Thread(target=capture_thread, args=(picam2,))
        cap_thread.daemon = True
        cap_thread.start()
        
        # Create and start the inference thread
        inf_thread = threading.Thread(target=inference_thread, args=(net, classes))
        inf_thread.daemon = True
        inf_thread.start()
        
        # Run display in the main thread
        display_thread(data_logger)
        
        # Signal threads to stop
        stop_event.set()
        
        # Wait for threads to finish
        cap_thread.join(timeout=1.0)
        inf_thread.join(timeout=1.0)
    else:
        # Run everything in a single thread (original approach)
        try:
            frame_count = 0
            start_time = time.time()
            
            while True:
                loop_start = time.time()
                
                # Capture frame from camera
                frame = picam2.capture_array()
                
                # Only process every DETECTION_INTERVAL frames
                frame_count += 1
                if DETECTION_INTERVAL > 1 and frame_count % DETECTION_INTERVAL != 0:
                    # Just display the frame without detection
                    if ENABLE_PREVIEW:
                        cv2.imshow("Vehicle Detection", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    continue
                
                # Create a 4D blob from the frame
                blob = cv2.dnn.blobFromImage(frame, 1/255.0, (BLOB_SIZE, BLOB_SIZE), 
                                           swapRB=True, crop=False)
                
                # Set the input blob for the neural network
                net.setInput(blob)
                
                # Run forward pass to get output of the output layers
                outs = net.forward(get_output_layers(net))
                
                # Process detections
                processed_frame, vehicle_count, vehicle_types = process_detections(
                    frame, outs, classes, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
                
                # Calculate FPS
                elapsed = time.time() - start_time
                if elapsed >= 1.0:
                    fps = frame_count / elapsed
                    frame_count = 0
                    start_time = time.time()
                    
                    # Add FPS information
                    cv2.putText(processed_frame, f"FPS: {fps:.1f}", (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Update OLED display
                if ENABLE_OLED:
                    update_oled_display(vehicle_count, vehicle_types)
                
                # Log vehicle data
                if LOG_DETECTIONS and data_logger:
                    data_logger.log_data(vehicle_count, vehicle_types, fps)
                
                # Display the resulting frame
                if ENABLE_PREVIEW:
                    cv2.imshow("Vehicle Detection", processed_frame)
                    
                # Break the loop if 'q' pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                # Add a small delay to prevent high CPU usage
                processing_time = time.time() - loop_start
                if processing_time < 0.03:  # aim for ~30fps max
                    time.sleep(0.03 - processing_time)
                    
        except KeyboardInterrupt:
            print("Stopping detection...")
    
    # Clean up
    picam2.stop()
    cv2.destroyAllWindows()
    print("Vehicle detection stopped.")

if __name__ == "__main__":
    main()
