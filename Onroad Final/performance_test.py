import cv2
import numpy as np
import time
import os
from picamera2 import Picamera2
from utils import load_classes, get_output_layers, process_detections
from config import *

def run_performance_test():
    """Run a performance test with different configuration settings"""
    print("Starting performance benchmark...")
    
    # Load class names and network
    classes = load_classes(CLASSES_PATH)
    net = cv2.dnn.readNet(MODEL_PATH, CONFIG_PATH)
    
    # Set up camera
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"},
        controls={"FrameRate": CAMERA_FRAMERATE}
    )
    picam2.configure(config)
    picam2.start()
    time.sleep(2)  # Camera warm-up
    
    # Blob sizes to test
    blob_sizes = [320, 416, 512]
    
    # Backend/target combinations to test
    backends = [
        ("CPU", cv2.dnn.DNN_BACKEND_OPENCV, cv2.dnn.DNN_TARGET_CPU),
    ]
    
    # Check if OpenCL is available
    if cv2.ocl.haveOpenCL():
        backends.append(("OpenCL", cv2.dnn.DNN_BACKEND_OPENCV, cv2.dnn.DNN_TARGET_OPENCL))
    
    results = []
    
    # Capture a test frame
    test_frame = picam2.capture_array()
    
    for blob_size in blob_sizes:
        for name, backend, target in backends:
            print(f"Testing {name} with {blob_size}x{blob_size} input...")
            
            # Configure network
            net.setPreferableBackend(backend)
            net.setPreferableTarget(target)
            
            # Warmup
            blob = cv2.dnn.blobFromImage(test_frame, 1/255.0, (blob_size, blob_size), 
                                        swapRB=True, crop=False)
            net.setInput(blob)
            _ = net.forward(get_output_layers(net))
            
            # Benchmarking
            times = []
            for _ in range(20):  # Test 20 frames
                frame = picam2.capture_array()
                
                start_time = time.time()
                
                # Create blob
                blob = cv2.dnn.blobFromImage(frame, 1/255.0, (blob_size, blob_size), 
                                           swapRB=True, crop=False)
                
                # Inference
                net.setInput(blob)
                outs = net.forward(get_output_layers(net))
                
                # Process detections (measure full pipeline)
                _, vehicle_count, _ = process_detections(
                    frame, outs, classes, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)
                
                elapsed = time.time() - start_time
                times.append(elapsed)
            
            # Calculate statistics
            avg_time = sum(times) / len(times)
            fps = 1.0 / avg_time
            
            results.append({
                "backend": name,
                "blob_size": blob_size,
                "avg_time_ms": avg_time * 1000,
                "fps": fps
            })
            
            print(f"  Result: {fps:.1f} FPS ({avg_time*1000:.1f} ms per frame)")
    
    # Clean up
    picam2.stop()
    
    # Print results table
    print("\nPerformance Benchmark Results:")
    print("--------------------------------")
    print("| Backend | Input Size | Time (ms) | FPS |")
    print("|---------|------------|-----------|-----|")
    for r in results:
        print(f"| {r['backend']:7} | {r['blob_size']:4}x{r['blob_size']:<4} | {r['avg_time_ms']:9.1f} | {r['fps']:3.1f} |")
    print("--------------------------------")
    
    # Print recommendations
    print("\nRecommendations based on results:")
    fastest_config = max(results, key=lambda x: x['fps'])
    print(f"1. For best performance, use {fastest_config['backend']} with {fastest_config['blob_size']}x{fastest_config['blob_size']} input")
    print(f"   Expected performance: {fastest_config['fps']:.1f} FPS")
    
    best_compromise = None
    compromise_score = 0
    for r in results:
        # Find a good compromise between size and speed
        score = (r['fps'] / fastest_config['fps']) * (r['blob_size'] / 512)
        if score > compromise_score:
            compromise_score = score
            best_compromise = r
    
    if best_compromise:
        print(f"2. For balance of accuracy and speed, consider: {best_compromise['backend']} with {best_compromise['blob_size']}x{best_compromise['blob_size']} input")
        print(f"   Expected performance: {best_compromise['fps']:.1f} FPS")
    
    print("\nUpdate your config.py with preferred settings:")
    print(f"BLOB_SIZE = {fastest_config['blob_size']}  # Fastest configuration")
    if fastest_config['backend'] == 'OpenCL':
        print("ENABLE_GPU = True  # Enable OpenCL acceleration")
    
    print("\nRestart your application to apply changes.")

if __name__ == "__main__":
    run_performance_test()
