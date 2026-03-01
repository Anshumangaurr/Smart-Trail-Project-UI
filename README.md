SmartTrail – AI-Based Luggage Tracking System
📌 Overview

SmartTrail is a computer vision-based luggage tracking system designed for high-traffic environments such as airports, railway stations, and malls.

The system detects and tracks individuals and their associated luggage in real time using computer vision and machine learning techniques.

The goal is to improve luggage monitoring, reduce theft/misplacement, and enhance safety in crowded environments.

🎯 Problem Statement

In crowded public spaces, luggage misplacement and theft are common issues. Traditional CCTV systems only record footage but do not actively track objects or people.

SmartTrail aims to:

Detect individuals in real time

Track movement across frames

Maintain bounding box consistency

Assist in identifying luggage-owner association

🛠️ Tech Stack

Python

OpenCV

Machine Learning (Supervised object detection techniques)

Computer Vision

Embedded Systems (for potential hardware deployment)

🧠 System Architecture

Video input captured from camera feed

Frame preprocessing (noise reduction, resizing, grayscale conversion)

Person detection using computer vision model

Bounding box generation

Object tracking across frames

Output video with tracked subjects

🔍 Features

Real-time person detection

Bounding box tracking

Frame-by-frame analysis

Optimized detection pipeline

80–85% tracking accuracy

Designed for scalable deployment

📊 Performance

Achieved 80–85% detection accuracy

Improved tracking consistency through OpenCV preprocessing

Reduced frame-level noise for better detection stability

🚧 Challenges Faced

Lighting variations

Occlusion in crowded environments

Fast-moving subjects

Maintaining tracking consistency

🔒 Limitations

Struggles with heavy crowd overlap

Performance dependent on camera resolution

Accuracy decreases in low-light conditions

🚀 Future Improvements

Integrate Deep Learning models (YOLO / SSD)

Add luggage-person association algorithm

Deploy using edge devices (Raspberry Pi / Jetson Nano)

Integrate real-time alert system

Add cloud-based monitoring dashboard

📦 Installation
git clone <repo-link>
cd smarttrail
pip install -r requirements.txt
python main.py
📈 Potential Use Cases

Airports

Railway stations

Shopping malls

Large events

Smart city surveillance systems

👨‍💻 Author

Anshuman Gaur
B.Tech Computer Science
VIT Vellore


## ⚙️ Model Setup (Important)

This project uses the YOLOv8 model for detection.

Due to GitHub file size limits, the model file is not included in this repository.

### Download the model:
Download `yolov8n.pt` from the official Ultralytics link:  
https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

### After downloading:
Place the `yolov8n.pt` file inside the main project folder (same location as `app.py`).

Then run the project normally.

The application will automatically load the model from that location.

