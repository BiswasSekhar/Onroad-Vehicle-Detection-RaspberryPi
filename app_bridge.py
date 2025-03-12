#!/usr/bin/env python3
import cv2
import numpy as np
import time
import torch
from pathlib import Path
import argparse
import subprocess
import threading
import os

class FrameCaptureThread(threading.Thread):
    """Thread to continuously capture frames using libcamera-still"""
    
    def __init__(self, interval=0.5):
        """Initialize the frame capture thread
        
        Args:
            interval: Time interval between frame captures (in seconds)
        """
        threading.Thread.__init__(self)
        self.interval = interval
        self.running = True
        self.latest_frame_path = "/tmp/latest_frame.jpg"
        self.frame_ready = False
        self.daemon = True  # Thread will exit when main program exits
    
    def run(self):
        """Run the frame capture thread"""
        while self.running:
            # Capture a frame using libcamera-still
            try:
                subprocess.run(
                    ["libcamera-still", "-n", "-o", self.latest_frame_path, 
                     "--immediate", "--rotation", "0"],
                    check=True, capture_output=True
                )
                self.frame_ready = True
                time.sleep(self.interval)
            except subprocess.CalledProcessError:
                print("Error capturing frame")
                time.sleep(1)
    
    def get_frame(self):
        """Get the latest frame
        
        Returns:
            frame: The latest captured frame, or None if no frame is available
        """
        if not self.frame_ready or not os.path.exists(self.latest_frame_path):
            return None
        
        frame = cv2.imread(self.latest_frame_path)
        return frame
    
    def stop(self):
        """Stop the frame capture thread"""
        self.running = False

class VehicleDetector:
    """Vehicle detection class using YOLOv5 optimized for Raspberry Pi"""
    
    def __init__(self, model_path=None, conf_threshold=0.25, device='cpu'):
        """Initialize the vehicle detector with a YOLOv5 model
        
        Args:
            model_path: Path to a custom YOLOv5 model, if None will download from torch hub
            conf_threshold: Confidence threshold for detections
            device: Computing device ('cpu' or 'cuda')
        """
        self.conf_threshold = conf_threshold
        self.device = device
        
        # Load YOLOv5 model - either custom or pre-trained
        if model_path and Path(model_path).exists():
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', 
                                        path=model_path, force_reload=True)
        else:
            # Use YOLOv5s - the smallest and fastest variant
            self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        
        # Move model to the appropriate device
        self.model.to(device)
        
        # Set model parameters
        self.model.conf = conf_threshold  # Confidence threshold
        
        # Vehicle classes in COCO dataset that we're interested in
        self.vehicle_classes = {
            2: 'car', 
            3: 'motorcycle', 
            5: 'bus', 
            7: 'truck'
        }
    
    def detect_vehicles(self, frame):
        """Detect vehicles in the input frame
        
        Args:
            frame: Input image frame
        
        Returns:
            processed_frame: Frame with detection boxes
            detections: List of detected vehicles with coordinates and classes
        """
        # Perform inference
        results = self.model(frame)
        
        # Filter results to only include vehicles we're interested in
        detections = []
        for *box, conf, cls in results.xyxy[0]:  # xyxy format: x1, y1, x2, y2, confidence, class
            if int(cls) in self.vehicle_classes:
                vehicle_type = self.vehicle_classes[int(cls)]
                bbox = [int(x) for x in box]
                detections.append({
                    'type': vehicle_type,
                    'confidence': float(conf),
                    'bbox': bbox
                })
        
        # Draw the detections on the frame
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            vehicle_type = detection['type']
            confidence = detection['confidence']
            
            # Different color for different vehicle types
            color = {
                'car': (0, 255, 0),        # Green
                'motorcycle': (0, 0, 255), # Red
                'bus': (255, 0, 0),        # Blue
                'truck': (255, 255, 0)     # Cyan
            }.get(vehicle_type, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with confidence
            label = f"{vehicle_type}: {confidence:.2f}"
            (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.rectangle(frame, (x1, y1 - label_height - 10), (x1 + label_width + 10, y1), color, -1)
            cv2.putText(frame, label, (x1 + 5, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame, detections

def process_video(source=0, output=None, display=True, model_path=None):
    """Process video stream for vehicle detection
    
    Args:
        source: Video source (0 for webcam, or path to video file)
        output: Path to save output video
        display: Whether to display the processed frames
        model_path: Path to a custom YOLOv5 model
    """
    # Initialize detector
    detector = VehicleDetector(model_path=model_path)
    
    # Initialize frame capture thread
    capture_thread = FrameCaptureThread()
    capture_thread.start()
    
    # Wait for the first frame to be captured
    print("Waiting for first frame to be captured...")
    while not capture_thread.frame_ready:
        time.sleep(0.1)
    
    # Initialize video writer if output is specified
    writer = None
    if output:
        # Get the first frame to determine dimensions
        first_frame = capture_thread.get_frame()
        if first_frame is not None:
            height, width = first_frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            writer = cv2.VideoWriter(output, fourcc, 2, (width, height))  # 2 FPS based on capture interval
    
    # Process video frames
    frame_count = 0
    start_time = time.time()
    
    try:
        while True:
            frame = capture_thread.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            # Detect vehicles
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
            processed_frame, detections = detector.detect_vehicles(rgb_frame)
            processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_RGB2BGR)  # Convert RGB back to BGR
            
            # Display FPS and detection count
            end_time = time.time()
            elapsed_time = end_time - start_time
            if frame_count > 0:
                fps = frame_count / elapsed_time
            else:
                fps = 0
            
            # Add info text to frame
            info_text = f"FPS: {fps:.1f} | Detected: {len(detections)}"
            cv2.putText(processed_frame, info_text, (10, 30), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Write frame to output video if specified
            if writer:
                writer.write(processed_frame)
            
            # Display frame if specified
            if display:
                cv2.imshow('Vehicle Detection', processed_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
                    break
            
            frame_count += 1
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Release resources
        capture_thread.stop()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
    
    print(f"Processed {frame_count} frames in {elapsed_time:.2f} seconds ({frame_count/elapsed_time:.2f} FPS)")

def main():
    parser = argparse.ArgumentParser(description='Vehicle Detection for Raspberry Pi')
    parser.add_argument('--source', type=str, default=0, 
                        help='Video source (0 for webcam, or path to video file)')
    parser.add_argument('--output', type=str, default=None, 
                        help='Path to save output video')
    parser.add_argument('--no-display', action='store_true', 
                        help='Do not display video (useful for headless operation)')
    parser.add_argument('--model', type=str, default=None, 
                        help='Path to custom YOLOv5 model')
    parser.add_argument('--confidence', type=float, default=0.25, 
                        help='Detection confidence threshold')
    
    args = parser.parse_args()
    
    print("Starting vehicle detection system...")
    print(f"Using source: {args.source}")
    print(f"Display enabled: {not args.no_display}")
    
    process_video(
        source=args.source,
        output=args.output,
        display=not args.no_display,
        model_path=args.model
    )

if __name__ == "__main__":
    main()
