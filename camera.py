import cv2
import numpy as np
from ultralytics import YOLO

class VideoCamera(object):
    def __init__(self):
        # Using OpenCV to capture from the default camera
        self.video = cv2.VideoCapture(0)
        self.is_running = True  # Privacy mode toggle
        
        # Load YOLOv8 nano model (lightweight and fast)
        # First run will download the model automatically
        print("Loading YOLOv8 model...")
        self.model = YOLO('yolov8n.pt')  # Nano model is fastest
        print("YOLOv8 model loaded successfully!")
        
        # Track the target person across frames
        self.target_id = None

    def __del__(self):
        if self.video.isOpened():
            self.video.release()

    def set_running(self, running):
        self.is_running = running

    def get_frame(self):
        if not self.is_running:
            return self.get_blank_frame("PRIVACY MODE ON")

        if not self.video.isOpened():
             return self.get_blank_frame("Camera Not Accessible")

        success, image = self.video.read()
        if not success:
            return self.get_blank_frame("No Camera Signal")
        else:
            try:
                # Resize for faster processing
                image = cv2.resize(image, (640, 480))
                height, width, _ = image.shape
                center_x, center_y = width // 2, height // 2
                
                # Run YOLOv8 detection
                # classes=0 means only detect people (class 0 in COCO dataset)
                results = self.model(image, classes=0, verbose=False, conf=0.4)
                
                # Get detections
                boxes = results[0].boxes
                
                if len(boxes) > 0:
                    # Track the largest/closest person (largest bounding box area)
                    max_area = 0
                    target_box: tuple | None = None  # Type hint for IDE
                    
                    # Draw all detections with faint boxes
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf[0])
                        
                        # Calculate area
                        area = (x2 - x1) * (y2 - y1)
                        
                        # Draw faint green box for all detected people
                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 1)
                        
                        # Track largest box
                        if area > max_area:
                            max_area = area
                            target_box = (x1, y1, x2, y2, conf)
                    
                    if target_box is not None:
                        x1, y1, x2, y2, conf = target_box
                        
                        # Draw strong box for the target person
                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        
                        # Calculate center of the person
                        target_cx = (x1 + x2) // 2
                        target_cy = (y1 + y2) // 2
                        
                        # Draw Steering Arrow (From Bottom Center to Target)
                        start_point = (center_x, height - 50)
                        end_point = (target_cx, y2)  # Point to feet/base of person
                        
                        color = (0, 255, 255)  # Yellow arrow
                        thickness = 4
                        
                        cv2.arrowedLine(image, start_point, end_point, color, thickness, tipLength=0.3)
                        
                        # Calculate steering direction
                        deviation = target_cx - center_x
                        direction_text = "FORWARD"
                        if deviation < -50: 
                            direction_text = "LEFT"
                        elif deviation > 50: 
                            direction_text = "RIGHT"
                        
                        # Display steering info
                        cv2.putText(image, f"STEERING: {direction_text}", 
                                   (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                        
                        # Display confidence
                        cv2.putText(image, f"Confidence: {conf:.2f}", 
                                   (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                else:
                    cv2.putText(image, "SEARCHING FOR USER...", 
                               (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            except Exception as e:
                print(f"Error during detection: {e}")
                err_str = str(e)
                error_msg = err_str[:30] if len(err_str) > 30 else err_str
                cv2.putText(image, f"Detection Error: {error_msg}", 
                           (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Encode frame as JPEG
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def get_blank_frame(self, message):
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        # Gentle pulsing dark background
        image[:] = (20, 20, 20) 
        
        cv2.putText(image, message, (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
