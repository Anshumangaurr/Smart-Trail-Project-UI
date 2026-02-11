import cv2
import numpy as np

# Quick test to see if camera is accessible
print("Testing camera access...")
video = cv2.VideoCapture(0)

if video.isOpened():
    print("Camera opened successfully!")
    success, frame = video.read()
    if success:
        print(f"Frame captured! Size: {frame.shape}")
    else:
        print("Camera opened but couldn't read frame")
    video.release()
else:
    print("Could not open camera")
    print("Possible issues:")
    print("  - Camera is being used by another application")
    print("  - Camera permissions not granted")
    print("  - No camera connected to the system")

# Test if ultralytics is installed
try:
    from ultralytics import YOLO
    print("\nUltralytics (YOLO) is installed")
    print("Testing YOLO model load...")
    model = YOLO('yolov8n.pt')
    print("YOLO model loaded successfully!")
except ImportError as e:
    print(f"\nUltralytics not found: {e}")
except Exception as e:
    print(f"\nError loading YOLO: {e}")
