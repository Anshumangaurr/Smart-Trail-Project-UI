from pathlib import Path
from typing import Optional

from ultralytics import YOLO


def main(
    data_yaml: Optional[str] = None,
    base_weights: str = "yolov8n.pt",
    epochs: int = 100,
    batch: int = 16,
) -> None:
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

    Args:
        data_yaml: Optional path to a custom data yaml. Defaults to obstacle_data.yaml.
        base_weights: Weights to start from (can be your previously trained best.pt).
        epochs: Number of training epochs.
        batch: Batch size (reduce if you hit out-of-memory).
    """

    project_dir = Path(__file__).parent
    if data_yaml is None:
        data_yaml_path = project_dir / "obstacle_data.yaml"
    else:
        data_yaml_path = Path(data_yaml)

    # Start from the pretrained YOLOv8 nano weights (or your last best.pt).
    model = YOLO(base_weights)

    model.train(
        data=str(data_yaml_path),
        epochs=epochs,
        imgsz=640,
        batch=batch,
        project=str(project_dir / "runs"),
        name="obstacle-yolov8n",
        verbose=True,
        # Better generalization settings
        optimizer="SGD",
        lr0=0.01,
        lrf=0.01,
        weight_decay=0.0005,
        cos_lr=True,
        # Augmentations
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        # Training control
        patience=20,  # early stopping
        device=0,  # use GPU 0 if available, else CPU
    )

    # After training, the best weights will typically be at:
    #   runs/detect/obstacle-yolov8n/weights/best.pt
    # You can either replace yolov8n.pt with that file
    # or update camera.py to point to the new path.


if __name__ == "__main__":
    # Run with default hyperparameters. For custom values you can
    # import this module and call main(...) from another script or notebook.
    main()

