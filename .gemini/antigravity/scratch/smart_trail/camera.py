import cv2
import numpy as np
import os
import sys

class VideoCamera(object):
    def __init__(self):
        # Using OpenCV to capture from the default camera
        self.video = cv2.VideoCapture(0)
        self.is_running = True  # Privacy mode toggle
        
        # Load the cascade classifier for body detection
        try:
            if not hasattr(cv2, 'data'):
                raise ImportError("cv2.data is missing")

            self.body_cascade = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, 'haarcascade_fullbody.xml'))
            if self.body_cascade.empty():
                 self.body_cascade = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, 'haarcascade_upperbody.xml'))
            if self.body_cascade.empty():
                 self.body_cascade = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml'))
        except Exception as e:
            print(f"Warning: Could not load Haar Cascades cleanly: {e}")
            self.body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')

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
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                height, width, _ = image.shape
                center_x, center_y = width // 2, height // 2
                
                # Detect people
                bodies = self.body_cascade.detectMultiScale(gray, 1.1, 4)

                if len(bodies) > 0:
                    # Track the largest body (closest to camera usually)
                    max_area = 0
                    target_body = None
                    
                    for (x, y, w, h) in bodies:
                        area = w * h
                        if area > max_area:
                            max_area = area
                            target_body = (x, y, w, h)
                        
                        # Draw faint boxes for all
                        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0, 100), 1)

                    if target_body:
                        x, y, w, h = target_body
                        # Strong box for target
                        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        target_cx = x + w // 2
                        target_cy = y + h // 2
                        
                        # Draw Steering Arrow (From Bottom Center to Target)
                        # This simulates the "Hardware" deciding where to go
                        start_point = (center_x, height - 50)
                        end_point = (target_cx, target_cy + h//2) # Point to feet/base
                        
                        color = (0, 255, 255) # Yellow arrow
                        thickness = 3
                        
                        cv2.arrowedLine(image, start_point, end_point, color, thickness, tipLength=0.3)
                        
                        # Calculate steering angle for UI (Simulation)
                        deviation = target_cx - center_x
                        direction_text = "FORWARD"
                        if deviation < -50: direction_text = "LEFT"
                        elif deviation > 50: direction_text = "RIGHT"
                        
                        cv2.putText(image, f"STEERING: {direction_text}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                else:
                    cv2.putText(image, "SEARCHING FOR USER...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            except Exception as e:
                print(f"Error during detection: {e}")

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
