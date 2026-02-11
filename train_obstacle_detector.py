from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    """
    Fine-tune YOLOv8n for obstacle detection.

    Expected dataset layout (relative to project root):

        data/
          obstacles/
            images/
              train/
                *.jpg / *.png
              val/
                *.jpg / *.png
            labels/
              train/
                *.txt
              val/
                *.txt

    Labels follow standard YOLO format: <class_id> <x_center> <y_center> <w> <h>
    all normalized to [0, 1].
    """

    project_dir = Path(__file__).parent
    data_yaml = project_dir / "obstacle_data.yaml"

    # Start from the pretrained YOLOv8 nano weights that you already have.
    model = YOLO("yolov8n.pt")

    model.train(
        data=str(data_yaml),
        epochs=50,
        imgsz=640,
        batch=8,
        project=str(project_dir / "runs"),
        name="obstacle-yolov8n",
        verbose=True,
    )

    # After training, the best weights will typically be at:
    #   runs/detect/obstacle-yolov8n/weights/best.pt
    # You can either replace yolov8n.pt with that file
    # or update camera.py to point to the new path.


if __name__ == "__main__":
    main()

