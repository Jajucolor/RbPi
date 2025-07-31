import os
import time
import logging
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

try:
    from picamera2 import Picamera2
    from picamera2.encoders import JpegEncoder
    from picamera2.outputs import FileOutput
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    logging.warning("picamera2 not available - using simulation mode")


class CameraManager:
    # 카메라
    
    def __init__(self, image_width=1920, image_height=1080, quality=85):
        self.logger = logging.getLogger(__name__)
        self.image_width = image_width
        self.image_height = image_height
        self.quality = quality
        self.camera = None
        self.images_dir = Path("captured_images")
        
        # 이미지 경로 옶으면 만들기
        self.images_dir.mkdir(exist_ok=True)

        self.initialize_camera()
    
    def initialize_camera(self):
       
        if not PICAMERA_AVAILABLE:
            self.logger.warning("Running in simulation mode - camera not available")
            return
        
        try:
            self.camera = Picamera2()
            
            # 카메라 설정
            config = self.camera.create_still_configuration(
                main={"size": (self.image_width, self.image_height)},
                display="main"
            )
            
            self.camera.configure(config)
            self.camera.start()

            time.sleep(2)
            
            self.logger.info(f"Camera initialized successfully at {self.image_width}x{self.image_height}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {str(e)}")
            self.camera = None
    
    def capture_image(self, filename=None):
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
        
        filepath = self.images_dir / filename
        
        try:
            if PICAMERA_AVAILABLE and self.camera:

                self.camera.capture_file(str(filepath))
                self.logger.info(f"Image captured successfully: {filepath}")
                
            else:
                # 카메라 없으면 더미 파일 분석
                self.logger.warning("Using simulation mode - creating dummy image")
                self.create_dummy_image(filepath)
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to capture image: {str(e)}")
            return None
    
    def create_dummy_image(self, filepath):
        
        try:
                 
            img = Image.new('RGB', (self.image_width, self.image_height), color='lightblue')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            text = f"SIMULATION MODE\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            draw.text((50, 50), text, fill='black', font=font)
            
            img.save(filepath, 'JPEG', quality=self.quality)
            
        except ImportError:
            # 최소한의 이미지
            with open(filepath, 'w') as f:
                f.write(f"Dummy image created at {datetime.now()}")
    
    def get_camera_info(self):
        # 카메라 상태
        if not PICAMERA_AVAILABLE:
            return {"status": "simulation", "message": "Camera library not available"}
        
        if not self.camera:
            return {"status": "error", "message": "Camera not initialized"}
        
        try:
           
            return {
                "status": "active",
                "resolution": f"{self.image_width}x{self.image_height}",
                "quality": self.quality,
                "message": "Camera operational"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def cleanup(self):
        #카메라 정리
        if self.camera and PICAMERA_AVAILABLE:
            try:
                self.camera.stop()
                self.camera.close()
                self.logger.info("Camera cleaned up successfully")
            except Exception as e:
                self.logger.error(f"Error during camera cleanup: {str(e)}")
    
    def __del__(self):
        self.cleanup() 