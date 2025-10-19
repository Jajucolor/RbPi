"""Keyword spotting manager for Coral Edge TPU."""

import logging
import time
from pathlib import Path
from typing import Dict, Optional


try:  # Audio capture is required for live keyword spotting
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:  # pragma: no cover - hardware/audio dependency
    sd = None
    SOUNDDEVICE_AVAILABLE = False

try:  # Numerical operations for audio preprocessing
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:  # pragma: no cover - required for realtime mode
    np = None
    NUMPY_AVAILABLE = False

try:  # Coral accelerated inference helpers
    from pycoral.utils import edgetpu
    from pycoral.adapters import common, classify
    PY_CORAL_AVAILABLE = True
except ImportError:  # pragma: no cover - falls back to CPU or simulation
    edgetpu = None
    common = None
    classify = None
    PY_CORAL_AVAILABLE = False

try:  # Lightweight TFLite interpreter (CPU fallback)
    from tflite_runtime.interpreter import Interpreter, load_delegate
    TFLITE_AVAILABLE = True
except ImportError:  # pragma: no cover - optional fallback only
    Interpreter = None
    load_delegate = None
    TFLITE_AVAILABLE = False


class EdgeTPUKeywordSpotter:
    """Run keyword spotting on the Edge TPU with graceful fallbacks."""

    def __init__(
        self,
        model_path: str,
        label_path: Optional[str] = None,
        sample_rate: int = 16000,
        frame_duration: float = 0.5,
        score_threshold: float = 0.6,
        top_k: int = 3,
        fallback_phrase: str = "hey glasses",
        warmup_iterations: int = 2,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.model_path = Path(model_path)
        self.label_path = Path(label_path) if label_path else None
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frame_samples = int(sample_rate * frame_duration)
        self.score_threshold = score_threshold
        self.top_k = top_k
        self.fallback_phrase = fallback_phrase
        self.warmup_iterations = warmup_iterations

        self.labels = self._load_labels()
        self.interpreter = None
        self.input_details = None
        self.input_size = None
        self.uses_simulation = False

        self._initialize_interpreter()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------
    def _load_labels(self) -> Dict[int, str]:
        if not self.label_path or not self.label_path.exists():
            self.logger.warning(
                "Keyword spotter label file missing - defaulting to fallback phrase"
            )
            return {0: self.fallback_phrase}

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
            return labels or {0: self.fallback_phrase}
        except Exception as exc:  # pragma: no cover - file IO error
            self.logger.error("Failed to load keyword labels: %s", exc)
            return {0: self.fallback_phrase}

    def _initialize_interpreter(self) -> None:
        """Load the Edge TPU (or CPU) interpreter for keyword spotting."""

        if not self.model_path.exists():
            self.logger.warning(
                "Keyword spotter model '%s' not found - using simulation mode",
                self.model_path,
            )
            self.uses_simulation = True
            return

        if not NUMPY_AVAILABLE or not SOUNDDEVICE_AVAILABLE:
            self.logger.warning(
                "Audio or NumPy dependencies missing - using simulated keyword spotting"
            )
            self.uses_simulation = True
            return

        try:
            if PY_CORAL_AVAILABLE:
                self.logger.info(
                    "Loading Edge TPU keyword model '%s'", self.model_path
                )
                interpreter = edgetpu.make_interpreter(str(self.model_path))
            elif TFLITE_AVAILABLE and Interpreter is not None:
                self.logger.info(
                    "Loading CPU keyword model '%s' (no Edge TPU delegate)",
                    self.model_path,
                )
                delegates = []
                if load_delegate is not None:
                    try:
                        delegates.append(load_delegate("libedgetpu.so.1"))
                    except Exception:  # pragma: no cover - optional delegate load
                        pass
                interpreter = Interpreter(model_path=str(self.model_path), delegates=delegates)
            else:
                self.logger.warning(
                    "No TFLite interpreter available - using simulated keyword spotting"
                )
                self.uses_simulation = True
                return

            interpreter.allocate_tensors()
            self.interpreter = interpreter
            self.input_details = interpreter.get_input_details()[0]
            self.input_size = int(np.prod(self.input_details["shape"]))
            self.logger.info("Keyword spotter ready (input size: %s)", self.input_size)

            # Warm up the interpreter to avoid first-frame latency
            dummy = np.zeros(self.input_size, dtype=self.input_details["dtype"])
            for _ in range(self.warmup_iterations):
                self._invoke(dummy)

        except Exception as exc:  # pragma: no cover - runtime failure
            self.logger.error("Failed to initialise keyword spotter: %s", exc)
            self.uses_simulation = True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def listen_for_keyword(self, timeout: Optional[float] = None) -> Optional[str]:
        """Block until a keyword is detected or timeout expires."""

        if self.uses_simulation or not self.interpreter:
            self.logger.info(
                "Keyword spotter running in simulation mode - auto triggering '%s'",
                self.fallback_phrase,
            )
            time.sleep(self.frame_duration)
            return self.fallback_phrase

        end_time = time.time() + timeout if timeout else None

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=self.frame_samples,
            ) as stream:
                self.logger.info("Listening for Edge TPU keyword...")
                while True:
                    if end_time and time.time() > end_time:
                        return None

                    frames, overflow = stream.read(self.frame_samples)
                    if overflow:  # pragma: no cover - logging only
                        self.logger.debug("Audio buffer overflow detected")

                    predictions = self._classify(frames)
                    if not predictions:
                        continue

                    for prediction in predictions:
                        phrase = self.labels.get(prediction.id, self.fallback_phrase)
                        if prediction.score >= self.score_threshold:
                            self.logger.info(
                                "Keyword '%s' detected (score %.2f)",
                                phrase,
                                prediction.score,
                            )
                            return phrase

        except Exception as exc:  # pragma: no cover - audio failure
            self.logger.error("Keyword listener error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _classify(self, raw_frames: bytes):
        if not NUMPY_AVAILABLE:
            return []

        audio = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32)
        if audio.size == 0:
            return []

        # Normalise to [-1.0, 1.0] then reshape to the interpreter input size
        audio = audio / np.max([np.abs(audio).max(), 1])

        if audio.size < self.input_size:
            audio = np.pad(audio, (0, self.input_size - audio.size))
        elif audio.size > self.input_size:
            audio = audio[-self.input_size :]

        audio = audio.astype(self.input_details["dtype"])

        if self.input_details["dtype"] in (np.uint8, np.int8):
            # Map floating data to quantised range if required
            scale, zero_point = self.input_details.get("quantization", (1.0, 0))
            if scale and scale != 0:
                audio = (audio / scale + zero_point).astype(self.input_details["dtype"])

        audio = audio.reshape(self.input_details["shape"])
        return self._invoke(audio)

    def _invoke(self, input_tensor):
        if not self.interpreter:
            return []

        if common is not None:
            common.set_input(self.interpreter, input_tensor)
        else:
            self.interpreter.set_tensor(self.input_details["index"], input_tensor)

        self.interpreter.invoke()

        if classify is not None:
            return classify.get_classes(
                self.interpreter, top_k=self.top_k, score_threshold=0.0
            )

        # Fallback classification parsing when pycoral classify helper is unavailable
        output_details = self.interpreter.get_output_details()[0]
        output = self.interpreter.get_tensor(output_details["index"])
        output = output.reshape(-1)

        results = []
        for idx, score in enumerate(output):
            if score >= self.score_threshold:
                results.append(_SimpleClass(id=idx, score=float(score)))
        return results


class _SimpleClass:
    """Lightweight container mirroring pycoral.adapters.classify.Class"""

    def __init__(self, id: int, score: float) -> None:
        self.id = id
        self.score = score

