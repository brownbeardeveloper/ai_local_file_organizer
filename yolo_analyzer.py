"""
YOLO Object Detection Analyzer
Handles YOLO-based object detection for images
"""

from typing import Dict, Any
from PIL import Image
from ultralytics import YOLO
from ai_model import AIModel


class YOLOAnalyzer(AIModel):
    """Handles YOLO object detection for images"""

    def _load_model(self):
        """Load YOLO model"""
        try:
            self.model = YOLO(self.model_name)
            print(f"YOLO model '{self.model_name}' loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load YOLO model '{self.model_name}': {e}")
            self.model = None

    def detect_objects(self, image) -> Dict[str, Any]:
        """Use YOLO to detect objects in the image"""
        if not self.is_available():
            return {}

        try:
            # Run YOLO inference on the image
            results = self.model(image, verbose=False)

            if results and len(results) > 0:
                return self._process_yolo_results(results[0])
            else:
                return {}

        except Exception as e:
            return {"object_detection_error": str(e)}

    def _process_yolo_results(self, result) -> Dict[str, Any]:
        """Process YOLO results and return detailed insights"""
        try:
            # Get detected objects
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                return {}

            # Get class names and confidences
            class_ids = boxes.cls.cpu().numpy()
            confidences = boxes.conf.cpu().numpy()

            # Complete YOLO/COCO class names (80 classes)
            yolo_classes = {
                0: "person",
                1: "bicycle",
                2: "car",
                3: "motorcycle",
                4: "airplane",
                5: "bus",
                6: "train",
                7: "truck",
                8: "boat",
                9: "traffic light",
                10: "fire hydrant",
                11: "stop sign",
                12: "parking meter",
                13: "bench",
                14: "bird",
                15: "cat",
                16: "dog",
                17: "horse",
                18: "sheep",
                19: "cow",
                20: "elephant",
                21: "bear",
                22: "zebra",
                23: "giraffe",
                24: "backpack",
                25: "umbrella",
                26: "handbag",
                27: "tie",
                28: "suitcase",
                29: "frisbee",
                30: "skis",
                31: "snowboard",
                32: "sports ball",
                33: "kite",
                34: "baseball bat",
                35: "baseball glove",
                36: "skateboard",
                37: "surfboard",
                38: "tennis racket",
                39: "bottle",
                40: "wine glass",
                41: "cup",
                42: "fork",
                43: "knife",
                44: "spoon",
                45: "bowl",
                46: "banana",
                47: "apple",
                48: "sandwich",
                49: "orange",
                50: "broccoli",
                51: "carrot",
                52: "hot dog",
                53: "pizza",
                54: "donut",
                55: "cake",
                56: "chair",
                57: "couch",
                58: "potted plant",
                59: "bed",
                60: "dining table",
                61: "toilet",
                62: "tv",
                63: "laptop",
                64: "mouse",
                65: "remote",
                66: "keyboard",
                67: "cell phone",
                68: "microwave",
                69: "oven",
                70: "toaster",
                71: "sink",
                72: "refrigerator",
                73: "book",
                74: "clock",
                75: "vase",
                76: "scissors",
                77: "teddy bear",
                78: "hair drier",
                79: "toothbrush",
            }

            # Find highest confidence detection
            if len(confidences) > 0:
                best_idx = confidences.argmax()
                best_class_id = int(class_ids[best_idx])
                best_confidence = float(confidences[best_idx])

                if best_confidence > 0.3:  # At least 30% confidence
                    detected_object = yolo_classes.get(
                        best_class_id, f"unknown_class_{best_class_id}"
                    )

                    return {
                        "primary_object": detected_object,
                        "confidence": f"{best_confidence * 100:.1f}%",
                        "object_category": "detected_object",
                    }

            return {}

        except Exception as e:
            return {"yolo_processing_error": str(e)}
