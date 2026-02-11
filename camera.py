import cv2
import numpy as np

try:
    # Import here so that the rest of the app can still run
    # even if ultralytics is not installed.
    from ultralytics import YOLO
except Exception as e:  # pragma: no cover - import-time guard
    print(f"Warning: could not import ultralytics.YOLO: {e}")
    YOLO = None  # type: ignore


# Labels we consider as "obstacles" when using a COCO-pretrained model.
# If you train a custom obstacle model, include its class name (e.g. "obstacle")
# in this set.
OBSTACLE_LABELS = {
    "obstacle",
    "chair",
    "bench",
    "table",
    "backpack",
    "handbag",
    "suitcase",
    "bicycle",
    "motorbike",
    "car",
    "truck",
    "dog",
    "cat",
    "traffic light",
    "stop sign",
}


class VideoCamera(object):
    """
    Video camera wrapper used by the Flask app.

    Responsibilities:
      - Manage the OpenCV capture device
      - Optionally run YOLOv8 person detection
      - Render steering guidance overlays
      - Support a simple "privacy mode" via set_running(False)
    """

    def __init__(self):
        # Using OpenCV to capture from the default camera
        self.video = cv2.VideoCapture(0)
        self.is_running = True  # Privacy mode toggle

        # Try to load YOLOv8 nano model (lightweight and fast).
        # If loading fails (missing file, no GPU, etc.), we fall back
        # to a simple camera view without detection instead of crashing.
        self.model = None
        if YOLO is not None:
            try:
                print("Loading YOLOv8 model...")
                self.model = YOLO("yolov8n.pt")  # Nano model is fastest
                print("YOLOv8 model loaded successfully!")
            except Exception as e:
                print(f"Warning: YOLO model could not be loaded: {e}")

        # Track the target person across frames (reserved for future use)
        self.target_id = None

    def __del__(self):
        if self.video.isOpened():
            self.video.release()

    def set_running(self, running):
        self.is_running = running

    def get_frame(self):
        """
        Capture a single JPEG-encoded frame.

        Honors the privacy toggle and degrades gracefully if the camera or
        model are not available.
        """
        if not self.is_running:
            return self.get_blank_frame("PRIVACY MODE ON")

        if not self.video.isOpened():
            return self.get_blank_frame("Camera Not Accessible")

        success, image = self.video.read()
        if not success:
            return self.get_blank_frame("No Camera Signal")

        try:
            # Resize for faster processing
            image = cv2.resize(image, (640, 480))

            # Only attempt detection if we actually have a model
            if self.model is not None:
                height, width, _ = image.shape
                center_x, _ = width // 2, height // 2

                # Run YOLOv8 detection (all classes so we can see obstacles too)
                results = self.model(image, verbose=False, conf=0.4)

                # Get detections
                det = results[0]
                boxes = det.boxes
                names = det.names if hasattr(det, "names") else getattr(self.model, "names", {})

                people = []
                obstacles = []

                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf[0])
                        cls_id = int(box.cls[0]) if box.cls is not None else -1

                        label = None
                        if isinstance(names, dict):
                            label = names.get(cls_id, str(cls_id))
                        elif isinstance(names, (list, tuple)) and 0 <= cls_id < len(names):
                            label = str(names[cls_id])
                        else:
                            label = str(cls_id)

                        label_lower = label.lower()

                        # Categorize detections
                        if label_lower == "person":
                            people.append((x1, y1, x2, y2, conf, label))
                            box_color = (0, 255, 0)  # green for people
                        elif label_lower in OBSTACLE_LABELS:
                            obstacles.append((x1, y1, x2, y2, conf, label))
                            box_color = (0, 0, 255)  # red for obstacles
                        else:
                            # Other classes (ignored for navigation but still drawn)
                            box_color = (255, 255, 0)

                        # Draw bounding box
                        cv2.rectangle(image, (x1, y1), (x2, y2), box_color, 1)
                        cv2.putText(
                            image,
                            f"{label} {conf:.2f}",
                            (x1, max(20, y1 - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            box_color,
                            1,
                        )

                    # Follow-the-person steering (use the largest person box)
                    if people:
                        max_area = 0
                        target_box = None
                        for x1, y1, x2, y2, conf, _ in people:
                            area = (x2 - x1) * (y2 - y1)
                            if area > max_area:
                                max_area = area
                                target_box = (x1, y1, x2, y2, conf)

                        if target_box is not None:
                            x1, y1, x2, y2, conf = target_box

                            # Draw strong box for the target person
                            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)

                            # Calculate center of the person
                            target_cx = (x1 + x2) // 2

                            # Draw Steering Arrow (From Bottom Center to Target)
                            start_point = (center_x, height - 50)
                            end_point = (target_cx, y2)  # Point to feet/base of person

                            color = (0, 255, 255)  # Yellow arrow
                            thickness = 4

                            cv2.arrowedLine(
                                image,
                                start_point,
                                end_point,
                                color,
                                thickness,
                                tipLength=0.3,
                            )

                            # Calculate steering direction
                            deviation = target_cx - center_x
                            direction_text = "FORWARD"
                            if deviation < -50:
                                direction_text = "LEFT"
                            elif deviation > 50:
                                direction_text = "RIGHT"

                            # Display steering info
                            cv2.putText(
                                image,
                                f"STEERING: {direction_text}",
                                (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                color,
                                2,
                            )

                    # Simple obstacle-avoidance suggestion
                    if obstacles:
                        danger_zone_y = int(height * 0.6)
                        mid_left = width // 3
                        mid_right = 2 * width // 3

                        left_blocked = False
                        center_blocked = False
                        right_blocked = False

                        for ox1, oy1, ox2, oy2, _, _ in obstacles:
                            # Focus on obstacles near the bottom of the frame (close to robot)
                            if oy2 < danger_zone_y:
                                continue

                            ocx = (ox1 + ox2) // 2
                            if ocx < mid_left:
                                left_blocked = True
                            elif ocx > mid_right:
                                right_blocked = True
                            else:
                                center_blocked = True

                        avoid_text = None
                        if center_blocked:
                            if not left_blocked:
                                avoid_text = "OBSTACLE AHEAD - GO LEFT"
                            elif not right_blocked:
                                avoid_text = "OBSTACLE AHEAD - GO RIGHT"
                            else:
                                avoid_text = "OBSTACLE AHEAD - STOP"
                        elif left_blocked and not right_blocked:
                            avoid_text = "KEEP RIGHT"
                        elif right_blocked and not left_blocked:
                            avoid_text = "KEEP LEFT"

                        if avoid_text:
                            cv2.putText(
                                image,
                                avoid_text,
                                (50, 110),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                (0, 255, 255),
                                2,
                            )
                else:
                    cv2.putText(
                        image,
                        "SEARCHING FOR USER...",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2,
                    )
            else:
                # No model available; show a subtle message but still stream video
                cv2.putText(
                    image,
                    "YOLO MODEL UNAVAILABLE",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                )

        except Exception as e:
            print(f"Error during detection: {e}")
            err_str = str(e)
            error_msg = err_str[:30] if len(err_str) > 30 else err_str
            cv2.putText(
                image,
                f"Detection Error: {error_msg}",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )

        # Encode frame as JPEG
        ret, jpeg = cv2.imencode(".jpg", image)
        return jpeg.tobytes()

    def get_blank_frame(self, message):
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        # Gentle pulsing dark background
        image[:] = (20, 20, 20) 
        
        cv2.putText(image, message, (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()
