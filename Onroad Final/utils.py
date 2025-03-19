import cv2
import numpy as np
import time
import logging
from config import VEHICLE_CLASSES, LOG_DETECTIONS, LOG_PATH
import board
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
from config import ENABLE_OLED, OLED_WIDTH, OLED_HEIGHT, OLED_I2C_ADDRESS, OLED_I2C_BUS

if LOG_DETECTIONS:
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO, 
                        format='%(asctime)s - %(message)s')

# Global OLED display object
oled_display = None

def initialize_oled():
    """Initialize the OLED display"""
    global oled_display
    
    if not ENABLE_OLED:
        return None
    
    try:
        # Create the I2C interface
        i2c = board.I2C()
        
        # Create the SSD1306 OLED display instance
        oled_display = adafruit_ssd1306.SSD1306_I2C(
            OLED_WIDTH, OLED_HEIGHT, i2c, addr=OLED_I2C_ADDRESS)
        
        # Clear the display
        oled_display.fill(0)
        oled_display.show()
        
        print("OLED display initialized successfully")
        return oled_display
    except Exception as e:
        print(f"Error initializing OLED display: {e}")
        return None

def update_oled_display(vehicle_count, vehicle_types=None, fps=0):
    """Update the OLED display with detection results"""
    global oled_display
    
    if not ENABLE_OLED or oled_display is None:
        return
    
    try:
        # Create blank image for drawing
        image = Image.new("1", (oled_display.width, oled_display.height))
        draw = ImageDraw.Draw(image)
        
        # Load fonts - try to load larger fonts for better visibility
        try:
            large_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            # Fall back to default font if custom font fails
            large_font = ImageFont.load_default()
            medium_font = ImageFont.load_default()
        
        # Draw total vehicles count at the top in large font
        total_text = f"Total: {vehicle_count}"
        # Center the text
        total_w = draw.textsize(total_text, font=large_font)[0]
        draw.text(((OLED_WIDTH - total_w) // 2, 0), total_text, font=large_font, fill=255)
        
        # Draw each vehicle type with count
        if vehicle_types and len(vehicle_types) > 0:
            y_position = 18  # Start position after total count
            
            # Sort vehicle types by count (highest first)
            sorted_vehicles = sorted(vehicle_types.items(), key=lambda x: x[1], reverse=True)
            
            # Display each vehicle type with count
            for vehicle_type, count in sorted_vehicles:
                if count > 0:  # Only show types with at least one detection
                    # Capitalize first letter for better readability
                    display_name = vehicle_type[0].upper() + vehicle_type[1:]
                    vehicle_text = f"{display_name}: {count}"
                    
                    # Center each vehicle type text
                    text_w = draw.textsize(vehicle_text, font=medium_font)[0]
                    draw.text(((OLED_WIDTH - text_w) // 2, y_position), 
                             vehicle_text, font=medium_font, fill=255)
                    y_position += 15  # Spacing between lines
                    
                    # Only show top 3 vehicle types to ensure they fit on screen
                    if y_position > 55:
                        break
        
        # If no vehicles detected, show a message
        if vehicle_count == 0:
            no_vehicle_text = "No vehicles"
            # Center the text
            text_w = draw.textsize(no_vehicle_text, font=medium_font)[0]
            draw.text(((OLED_WIDTH - text_w) // 2, 30), 
                     no_vehicle_text, font=medium_font, fill=255)
            
        # Display the image
        oled_display.image(image)
        oled_display.show()
    except Exception as e:
        print(f"Error updating OLED display: {e}")

def load_classes(classes_path):
    """Load class names from file"""
    with open(classes_path, 'r') as f:
        classes = [line.strip() for line in f.readlines()]
    return classes

def get_output_layers(net):
    """Get the names of output layers of the network"""
    layer_names = net.getLayerNames()
    try:
        output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    except:
        output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    return output_layers

def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h, classes):
    """Draw bounding box and label on the detected object"""
    label = str(classes[class_id])
    color = (0, 255, 0) if label in VEHICLE_CLASSES else (255, 0, 0)
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
    cv2.putText(img, f"{label} {confidence:.2f}", (x-10, y-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    if LOG_DETECTIONS and label in VEHICLE_CLASSES:
        logging.info(f"Detected {label} with confidence {confidence:.2f}")
    
    return img

def process_detections(frame, outs, classes, conf_threshold, nms_threshold):
    """Process network outputs and draw predictions"""
    class_ids = []
    confidences = []
    boxes = []
    frame_height = frame.shape[0]
    frame_width = frame.shape[1]

    # Scan through all detections and keep only the ones with high confidence
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            
            if confidence > conf_threshold and classes[class_id] in VEHICLE_CLASSES:
                center_x = int(detection[0] * frame_width)
                center_y = int(detection[1] * frame_height)
                w = int(detection[2] * frame_width)
                h = int(detection[3] * frame_height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])

    # Apply non-maximum suppression to remove redundant overlapping boxes
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
    
    vehicle_count = 0
    vehicle_types = {}
    for i in indices:
        try:
            box = boxes[i]
        except:
            i = i[0]
            box = boxes[i]
            
        x = int(box[0])
        y = int(box[1])
        w = int(box[2])
        h = int(box[3])
        draw_prediction(frame, class_ids[i], confidences[i], x, y, x + w, y + h, classes)
        vehicle_count += 1
        
        try:
            i_value = i[0] if isinstance(i, np.ndarray) else i
            label = classes[class_ids[i_value]]
            if label in VEHICLE_CLASSES:
                if label in vehicle_types:
                    vehicle_types[label] += 1
                else:
                    vehicle_types[label] = 1
        except:
            pass
    
    # Display vehicle count
    cv2.putText(frame, f"Vehicles: {vehicle_count}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return frame, vehicle_count, vehicle_types
