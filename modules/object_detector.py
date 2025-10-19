"""Edge TPU object detection utilities."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from PIL import Image

try:  # Coral accelerated helpers
    from pycoral.utils import edgetpu
    from pycoral.adapters import detect, common
    PY_CORAL_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback to CPU or simulation
    edgetpu = None
    detect = None
    common = None
    PY_CORAL_AVAILABLE = False

try:  # Lightweight TFLite interpreter
    from tflite_runtime.interpreter import Interpreter, load_delegate
    TFLITE_AVAILABLE = True
except ImportError:  # pragma: no cover - optional fallback
    Interpreter = None
    load_delegate = None
    TFLITE_AVAILABLE = False


@dataclass
class Detection:
    label: str
    score: float
    bbox: tuple  # (xmin, ymin, xmax, ymax)


class EdgeTPUObjectDetector:
    """Object detection pipeline optimised for Coral Edge TPU."""

    def __init__(
        self,
        model_path: str,
        label_path: Optional[str] = None,
        score_threshold: float = 0.3,
        top_k: int = 10,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.model_path = Path(model_path)
        self.label_path = Path(label_path) if label_path else None
        self.score_threshold = score_threshold
        self.top_k = top_k

        self.labels = self._load_labels()
        self.interpreter = None
        self.input_size = None

        self._initialize_interpreter()

    def _load_labels(self) -> Dict[int, str]:
        if not self.label_path or not self.label_path.exists():
            self.logger.warning(
                "Object detector label file missing - results will use numeric IDs"
            )
            return {}

        labels: Dict[int, str] = {}
        try:
            with open(self.label_path, "r", encoding="utf-8") as handle:
                for idx, line in enumerate(handle):
                    value = line.strip()
                    if not value:
                        continue
                    parts = value.split(maxsplit=1)
                    if len(parts) == 2 and parts[0].isdigit():
                        labels[int(parts[0])] = parts[1].strip()
                    else:
                        labels[idx] = value
            return labels
        except Exception as exc:  # pragma: no cover - IO failure
            self.logger.error("Failed to load object labels: %s", exc)
            return {}

    def _initialize_interpreter(self) -> None:
        if not self.model_path.exists():
            self.logger.warning(
                "Object detection model '%s' missing - running in simulation mode",
                self.model_path,
            )
            return

        try:
            if PY_CORAL_AVAILABLE:
                interpreter = edgetpu.make_interpreter(str(self.model_path))
            elif TFLITE_AVAILABLE and Interpreter is not None:
                delegates = []
                if load_delegate is not None:
                    try:
                        delegates.append(load_delegate("libedgetpu.so.1"))
                    except Exception:  # pragma: no cover
                        pass
                interpreter = Interpreter(
                    model_path=str(self.model_path), delegates=delegates
                )
            else:
                self.logger.warning(
                    "No interpreter available for object detection - running in simulation"
                )
                return

            interpreter.allocate_tensors()
            self.interpreter = interpreter
            if common is not None:
                width, height = common.input_size(interpreter)
                self.input_size = (width, height)
            else:
                input_tensor_shape = interpreter.get_input_details()[0]["shape"]
                self.input_size = tuple(reversed(input_tensor_shape[1:3]))  # width, height
            self.logger.info("Object detector ready (input size: %s)", self.input_size)
        except Exception as exc:  # pragma: no cover
            self.logger.error("Failed to initialise object detector: %s", exc)
            self.interpreter = None

    def detect(self, image_path: str) -> List[Detection]:
        if not self.interpreter:
            self.logger.info("Object detector not available - returning empty detections")
            return []

        try:
            image = Image.open(image_path).convert("RGB")
            resized = image.resize(self.input_size)

            if common is not None:
                common.set_input(self.interpreter, resized)
            else:
                input_details = self.interpreter.get_input_details()[0]
                input_array = np.array(resized, dtype=input_details["dtype"])
                input_array = np.expand_dims(input_array, axis=0)
                self.interpreter.set_tensor(input_details["index"], input_array)

            self.interpreter.invoke()

            if detect is not None:
                objects = detect.get_objects(
                    self.interpreter,
                    score_threshold=self.score_threshold,
                    top_k=self.top_k,
                )
            else:
                output_details = self.interpreter.get_output_details()[0]
                raw = self.interpreter.get_tensor(output_details["index"])
                objects = self._decode_fallback(raw)

            width, height = self.input_size
            detections: List[Detection] = []
            for obj in objects[: self.top_k]:
                if detect is not None:
                    bbox = (
                        obj.bbox.xmin,
                        obj.bbox.ymin,
                        obj.bbox.xmax,
                        obj.bbox.ymax,
                    )
                    score = obj.score
                    label = self.labels.get(obj.id, f"id_{obj.id}")
                else:
                    bbox = obj["bbox"]
                    score = obj["score"]
                    label = self.labels.get(obj["id"], f"id_{obj['id']}")

                # Map bounding box to relative coordinates (0-1 range)
                rel_bbox = (
                    bbox[0] / width,
                    bbox[1] / height,
                    bbox[2] / width,
                    bbox[3] / height,
                )
                detections.append(Detection(label=label, score=score, bbox=rel_bbox))

            return detections
        except Exception as exc:  # pragma: no cover - runtime failure
            self.logger.error("Object detection failed: %s", exc)
            return []

    def summarise(self, detections: List[Detection]) -> str:
        if not detections:
            return "I didn't detect any notable objects around you."

        parts = []
        for detection in detections:
            xmin, ymin, xmax, ymax = detection.bbox
            x_center = (xmin + xmax) / 2
            if x_center < 0.33:
                position = "to your left"
            elif x_center > 0.66:
                position = "to your right"
            else:
                position = "ahead"
            parts.append(
                f"{detection.label} {position} ({detection.score * 100:.0f}% confidence)"
            )

        return "Detected " + ", ".join(parts) + "."

    def _decode_fallback(self, raw_output):  # pragma: no cover - used without pycoral
        results = []
        if raw_output is None:
            return results
        for item in raw_output.reshape(-1, raw_output.shape[-1]):
            if item.size < 6:
                continue
            score = float(item[5])
            if score < self.score_threshold:
                continue
            results.append(
                {
                    "id": int(item[0]),
                    "bbox": (float(item[1]), float(item[2]), float(item[3]), float(item[4])),
                    "score": score,
                }
            )
        return results

