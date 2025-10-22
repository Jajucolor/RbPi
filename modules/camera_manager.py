import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

from PIL import Image, ImageDraw, ImageFont

try:
    import cv2

    OPENCV_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    cv2 = None
    OPENCV_AVAILABLE = False

try:
    from picamera2 import Picamera2  # pragma: no cover - hardware dependency

    PICAMERA_AVAILABLE = True
except ImportError:
    Picamera2 = None  # type: ignore
    PICAMERA_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "picamera2 not available - defaulting to simulation/ESP32 modes"
    )


class CameraManager:
    """Manage camera interactions for different hardware backends."""

    def __init__(
        self,
        image_width: int = 1920,
        image_height: int = 1080,
        quality: int = 85,
        camera_type: str = "esp32_cam",
        stream_url: Optional[str] = None,
        connection_retries: int = 5,
        retry_delay: float = 2.0,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.image_width = image_width
        self.image_height = image_height
        self.quality = quality
        self.camera_type = (camera_type or "picamera2").lower()
        self.stream_url = stream_url
        self.connection_retries = max(1, int(connection_retries))
        self.retry_delay = float(retry_delay)

        self.camera = None
        self.images_dir = Path("captured_images")
        self.images_dir.mkdir(exist_ok=True)

        self.initialize_camera()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------
    def initialize_camera(self) -> None:
        if self.camera_type in {"esp32", "esp32_cam", "esp32-cam"}:
            self._initialize_esp32_cam()
        else:
            self._initialize_picamera()

    def _initialize_picamera(self) -> None:
        if not PICAMERA_AVAILABLE:
            self.logger.warning(
                "picamera2 library is not available. Running in simulation mode."
            )
            return

        try:
            self.camera = Picamera2()
            config = self.camera.create_still_configuration(
                main={"size": (self.image_width, self.image_height)},
                display="main",
            )
            self.camera.configure(config)
            self.camera.start()

            time.sleep(2)  # allow auto-exposure to settle

            self.logger.info(
                "picamera2 initialized successfully at %dx%d",
                self.image_width,
                self.image_height,
            )
        except Exception as exc:  # pragma: no cover - hardware failure path
            self.logger.error("Failed to initialize picamera2: %s", exc)
            self.camera = None

    def _initialize_esp32_cam(self) -> None:
        if not OPENCV_AVAILABLE:
            self.logger.error(
                "OpenCV (cv2) is required for ESP32-CAM streaming but is not installed."
            )
            return

        if not self.stream_url:
            self.logger.error("ESP32-CAM stream URL is not configured.")
            return

        self.logger.info(
            "Attempting to connect to ESP32-CAM stream at %s", self.stream_url
        )

        for attempt in range(1, self.connection_retries + 1):
            self.camera = cv2.VideoCapture(self.stream_url)

            if self.camera.isOpened():
                # Reduce latency by keeping only the most recent frame.
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.logger.info(
                    "ESP32-CAM stream connected successfully on attempt %d", attempt
                )
                return

            self.logger.warning(
                "ESP32-CAM stream connection failed (attempt %d/%d).",
                attempt,
                self.connection_retries,
            )
            self.camera.release()
            self.camera = None
            time.sleep(self.retry_delay)

        self.logger.error("Failed to establish ESP32-CAM stream connection after retries.")

    # ------------------------------------------------------------------
    # Capture helpers
    # ------------------------------------------------------------------
    def capture_image(self, filename: Optional[str] = None) -> Optional[str]:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"

        filepath = self.images_dir / filename

        try:
            if self.camera_type in {"esp32", "esp32_cam", "esp32-cam"}:
                return self._capture_from_esp32(filepath)

            if PICAMERA_AVAILABLE and self.camera:
                self.camera.capture_file(str(filepath))
                self.logger.info("Image captured successfully: %s", filepath)
                return str(filepath)

            self.logger.warning("Using simulation mode - creating dummy image")
            self.create_dummy_image(filepath)
            return str(filepath)

        except Exception as exc:
            self.logger.error("Failed to capture image: %s", exc)
            return None

    def _capture_from_esp32(self, filepath: Path) -> Optional[str]:
        if not OPENCV_AVAILABLE or cv2 is None:
            self.logger.error("OpenCV is not available to capture from ESP32-CAM stream.")
            return None

        if not self.camera or not self.camera.isOpened():
            self.logger.error("ESP32-CAM stream is not initialized.")
            return None

        ret, frame = self.camera.read()

        if not ret or frame is None:
            self.logger.error("Failed to read frame from ESP32-CAM stream.")
            return None

        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            success = cv2.imwrite(
                str(filepath),
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), int(self.quality)],
            )
        except Exception as exc:  # pragma: no cover - cv2 failure path
            self.logger.error("Error while writing image from ESP32-CAM stream: %s", exc)
            return None

        if not success:
            self.logger.error("cv2.imwrite returned False while saving ESP32-CAM frame.")
            return None

        self.logger.info("Image captured successfully from ESP32-CAM: %s", filepath)
        return str(filepath)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def create_dummy_image(self, filepath: Path) -> None:
        try:
            img = Image.new(
                "RGB",
                (self.image_width, self.image_height),
                color="lightblue",
            )
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except Exception:  # pragma: no cover - font availability varies
                font = ImageFont.load_default()

            text = "SIMULATION MODE\n" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            draw.text((50, 50), text, fill="black", font=font)

            img.save(filepath, "JPEG", quality=self.quality)
        except ImportError:
            with open(filepath, "w", encoding="utf-8") as handle:
                handle.write(f"Dummy image created at {datetime.now()}")

    def get_camera_info(self) -> Dict[str, Union[str, int, None]]:
        if self.camera_type in {"esp32", "esp32_cam", "esp32-cam"}:
            if not OPENCV_AVAILABLE:
                return {
                    "status": "error",
                    "message": "OpenCV library not available for ESP32-CAM",
                }

            if not self.camera or not self.camera.isOpened():
                return {
                    "status": "error",
                    "message": "ESP32-CAM stream not initialized",
                }

            return {
                "status": "active",
                "type": "esp32_cam",
                "stream_url": self.stream_url,
                "quality": self.quality,
                "message": "ESP32-CAM stream operational",
            }

        if not PICAMERA_AVAILABLE:
            return {"status": "simulation", "message": "Camera library not available"}

        if not self.camera:
            return {"status": "error", "message": "Camera not initialized"}

        return {
            "status": "active",
            "type": "picamera2",
            "resolution": f"{self.image_width}x{self.image_height}",
            "quality": self.quality,
            "message": "Camera operational",
        }

    def cleanup(self) -> None:
        if self.camera_type in {"esp32", "esp32_cam", "esp32-cam"}:
            if self.camera:
                try:
                    self.camera.release()
                    self.logger.info("ESP32-CAM stream released successfully")
                except Exception as exc:  # pragma: no cover - cleanup failure path
                    self.logger.error("Error during ESP32-CAM cleanup: %s", exc)
        elif self.camera and PICAMERA_AVAILABLE:
            try:
                self.camera.stop()
                self.camera.close()
                self.logger.info("picamera2 cleaned up successfully")
            except Exception as exc:  # pragma: no cover - cleanup failure path
                self.logger.error("Error during picamera2 cleanup: %s", exc)

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        self.cleanup()
