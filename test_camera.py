import cv2

def test_camera(source=0):
    # Open video capture
    cap = cv2.VideoCapture(source, cv2.CAP_V4L2)  # Use V4L2 backend for libcamera
    if not cap.isOpened():
        print(f"Error: Could not open video source {source}")
        return
    
    print("Press 'q' to quit the video stream.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        # Display the frame
        cv2.imshow('Camera Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_camera()
