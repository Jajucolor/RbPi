"""Pose detection and tracking helpers using MoveNet on Edge TPU."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image

try:
    from pycoral.utils import edgetpu
    from pycoral.adapters import common
    PY_CORAL_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback or simulation
    edgetpu = None
    common = None
    PY_CORAL_AVAILABLE = False

try:
    from tflite_runtime.interpreter import Interpreter, load_delegate
    TFLITE_AVAILABLE = True
except ImportError:  # pragma: no cover - optional fallback
    Interpreter = None
    load_delegate = None
    TFLITE_AVAILABLE = False


KEYPOINT_NAMES = [
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]


@dataclass
class PoseKeypoint:
    name: str
    y: float
    x: float
    score: float


@dataclass
class PoseDetection:
    keypoints: List[PoseKeypoint]
    confidence: float
    bbox: tuple


class MoveNetPoseTracker:
    """Wrap a MoveNet pose model running on the Edge TPU."""

    def __init__(
        self,
        model_path: str,
        min_confidence: float = 0.25,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.model_path = Path(model_path)
        self.min_confidence = min_confidence

        self.interpreter = None
        self.input_size = None

        self._initialize_interpreter()

    def _initialize_interpreter(self) -> None:
        if not self.model_path.exists():
            self.logger.warning(
                "Pose model '%s' not found - pose tracking disabled",
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
                    "No interpreter available for pose tracking - running in simulation"
                )
                return

            interpreter.allocate_tensors()
            self.interpreter = interpreter
            if common is not None:
                width, height = common.input_size(interpreter)
                self.input_size = (width, height)
            else:
                tensor_shape = interpreter.get_input_details()[0]["shape"]
                self.input_size = tuple(reversed(tensor_shape[1:3]))  # width, height
            self.logger.info("Pose tracker ready (input size: %s)", self.input_size)
        except Exception as exc:  # pragma: no cover
            self.logger.error("Failed to initialise pose tracker: %s", exc)
            self.interpreter = None

    def detect(self, image_path: str) -> List[PoseDetection]:
        if not self.interpreter:
            self.logger.info("Pose tracker unavailable - returning empty pose list")
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

            output_details = self.interpreter.get_output_details()
            keypoint_output = self.interpreter.get_tensor(output_details[0]["index"])

            poses: List[PoseDetection] = []
            for pose in keypoint_output:
                keypoints = []
                xs, ys, confidences = [], [], []
                for idx, (y, x, score) in enumerate(pose[0]):
                    kp = PoseKeypoint(
                        name=KEYPOINT_NAMES[idx],
                        x=float(x),
                        y=float(y),
                        score=float(score),
                    )
                    keypoints.append(kp)
                    if kp.score >= self.min_confidence:
                        xs.append(kp.x)
                        ys.append(kp.y)
                        confidences.append(kp.score)

                if not confidences:
                    continue

                xmin, xmax = min(xs), max(xs)
                ymin, ymax = min(ys), max(ys)
                avg_conf = sum(confidences) / len(confidences)

                poses.append(
                    PoseDetection(
                        keypoints=keypoints,
                        confidence=avg_conf,
                        bbox=(xmin, ymin, xmax, ymax),
                    )
                )

            return poses
        except Exception as exc:  # pragma: no cover
            self.logger.error("Pose detection failed: %s", exc)
            return []

    def describe(self, poses: List[PoseDetection]) -> str:
        if not poses:
            return "I couldn't detect any people nearby."

        descriptions: List[str] = []
        for idx, pose in enumerate(poses, start=1):
            xmin, ymin, xmax, ymax = pose.bbox
            x_center = (xmin + xmax) / 2
            if x_center < 0.33:
                position = "on your left"
            elif x_center > 0.66:
                position = "on your right"
            else:
                position = "ahead of you"

            height = ymax - ymin
            distance_hint = "close" if height > 0.6 else "a short distance away"
            descriptions.append(
                f"Person {idx} is {position}, {distance_hint} ({pose.confidence * 100:.0f}% confidence)."
            )

        return " ".join(descriptions)

    def summarise_for_llm(self, poses: List[PoseDetection]) -> str:
        if not poses:
            return "PoseSummary: count=0"

        segments: List[str] = [f"PoseSummary: count={len(poses)}"]
        for idx, pose in enumerate(poses, start=1):
            keypoint_parts = []
            for kp in pose.keypoints:
                if kp.score < self.min_confidence:
                    continue
                keypoint_parts.append(
                    f"{kp.name}=(x:{kp.x:.2f}, y:{kp.y:.2f}, c:{kp.score:.2f})"
                )
            bbox = pose.bbox
            segments.append(
                f"person_{idx}: bbox=(x0:{bbox[0]:.2f}, y0:{bbox[1]:.2f}, x1:{bbox[2]:.2f}, y1:{bbox[3]:.2f}), "
                f"confidence={pose.confidence:.2f}; keypoints={{" + ", ".join(keypoint_parts) + "}}"
            )
        return " | ".join(segments)

