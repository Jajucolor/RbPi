import logging
import speech_recognition as sr
import time
import json
import os
from datetime import datetime
import sys
from pathlib import Path
import pygame
import tempfile
import wave  # <-- added for Piper WAV writing
    
import shutil, subprocess, tempfile, os, pygame

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    ollama = None
    OLLAMA_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    whisper = None
    WHISPER_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

# --- REPLACED: Coqui TTS -> Piper ---
try:
    from piper.voice import PiperVoice
    PIPER_TTS_AVAILABLE = True
except ImportError:
    PiperVoice = None
    PIPER_TTS_AVAILABLE = False
# -------------------------------------

from modules.camera_manager import CameraManager
from modules.vision_analyzer import VisionAnalyzer
# from modules.sensor_manager import NavigationSensorManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stt_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class IntaAIAssistant:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.microphone = None
        self.recognizer = None
        self.whisper_model = None
        self.whisper_model_name = None
        self.whisper_device = None
        self.whisper_fp16 = False

        self.tts_engine = None
        
        # 내비게이션 모니터링 상태
        self.navigation_active = False
        self.navigation_thread = None
        self.navigation_stop_event = None
        
        # 설정 불러오기
        self.config = self.load_config()
        
        # TTS를 위한 pygame mixer 초기화
        self.setup_audio_system()
        
        # 컴포넌트 초기화
        self.setup_microphone()
        self.setup_recognizer()
        self.setup_whisper_engine()
        self.setup_tts_engine()
        
        # 보조 안경 모듈 초기화
        self.initialize_assistive_modules()
        
        # 내비게이션 모니터링을 위한 센서 콜백 설정
        if hasattr(self, 'sensor_monitor') and self.sensor_monitor:
            self.sensor_monitor.set_callbacks(
                distance_callback=self._on_distance_update,
                warning_callback=self._on_navigation_warning,
                status_callback=self._on_sensor_status_change
            )
        
        self.logger.info("INTA AI Assistant initialized")

    
    def setup_audio_system(self):
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            volume = self.config.get("tts", {}).get("volume", 0.9)
            pygame.mixer.music.set_volume(volume)
            self.logger.info("Audio system initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize audio system: {e}")
            self.logger.warning("Text-to-speech will use fallback (print only)")
    
    def load_config(self):
        #config 불러오기 
        config_file = Path("config.json")
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load config file: {e}")
        
        # 디폴트 설정
        return {
            "stt": {
                "energy_threshold": 300,
                "dynamic_energy_threshold": True,
                "pause_threshold": 0.8,
                "non_speaking_duration": 0.5,
                "phrase_threshold": 0.3,
                "ambient_noise_duration": 2,
                "timeout": 5,
                "phrase_time_limit": 5,
                "whisper_model": "base",
                "whisper_device": "auto",
                "language": None
            },
            "ai": {
                "model": "gpt-4o-mini",
                "max_tokens": 150,
                "temperature": 0.7,
                "api_key": "your-openai-api-key-here"
            },
            "tts": {
                "rate": 200,
                "volume": 0.9,
                "model_name": "tts_models/en/vctk/vits"
            },
            "system": {
                "wake_word": "hey assistant",
                "log_responses": True
            },
            "hardware": {
                "camera_enabled": True,
                "camera_type": "esp32_cam",
                "esp32_cam_url": "http://192.168.4.1:80/stream",
                "esp32_connection_retries": 5,
                "esp32_retry_delay": 2.0,
                "sensors_enabled": True,
                "sensor_port": "/dev/ttyUSB0",
                "sensor_baudrate": 9600
            }
        }
    
    def setup_microphone(self):
        #마이크
        try:
            # 사용 가능한 모든 마이크 나열
            mics = sr.Microphone.list_microphone_names()
            self.logger.info(f"Available microphones: {mics}")
            
            # 기본 마이크 먼저 시도
            try:
                self.microphone = sr.Microphone()
                self.logger.info("Using default microphone")
                return
            except Exception as e:
                self.logger.warning(f"Default microphone failed: {e}")
            
            # 다른 장치 구성 시도
            for device_index in range(min(5, len(mics))):
                try:
                    self.microphone = sr.Microphone(device_index=device_index)
                    self.logger.info(f"Using microphone device {device_index}")
                    return
                except Exception as e:
                    self.logger.warning(f"Microphone {device_index} failed: {e}")
                    continue
            
            raise Exception("No working microphone found")
            
        except Exception as e:
            self.logger.error(f"Error setting up microphone: {e}")
            raise
    
    def setup_recognizer(self):
        # 음성인식 설정
        self.recognizer = sr.Recognizer()

        # 설정에서 인식기 세팅 구성
        stt_config = self.config["stt"]
        self.recognizer.energy_threshold = stt_config["energy_threshold"]
        self.recognizer.dynamic_energy_threshold = stt_config["dynamic_energy_threshold"]
        self.recognizer.pause_threshold = stt_config["pause_threshold"]
        self.recognizer.non_speaking_duration = stt_config["non_speaking_duration"]
        self.recognizer.phrase_threshold = stt_config["phrase_threshold"]

        self.logger.info("Speech recognizer configured")

    def setup_whisper_engine(self):
        """Initialize the offline Whisper speech recognition engine"""
        if not WHISPER_AVAILABLE:
            self.logger.warning("Whisper library not available. Offline STT will be disabled.")
            self.whisper_model = None
            return

        stt_config = self.config.get("stt", {})
        model_name = stt_config.get("whisper_model", "base")
        preferred_device = stt_config.get("whisper_device", "auto")
        preferred_device_str = preferred_device.lower() if isinstance(preferred_device, str) else preferred_device

        if preferred_device_str == "auto":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        else:
            device = preferred_device_str if isinstance(preferred_device_str, str) else preferred_device

        fp16 = device.lower().startswith("cuda") if isinstance(device, str) else False

        try:
            self.logger.info(
                f"Loading Whisper offline model '{model_name}' on device '{device}'"
            )
            self.whisper_model = whisper.load_model(model_name, device=device)
            self.whisper_model_name = model_name
            self.whisper_device = device
            self.whisper_fp16 = fp16
            self.logger.info("Whisper offline engine initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model '{model_name}': {e}")
            self.whisper_model = None

    def setup_tts_engine(self):
        tts_config = self.config.get("tts", {})
        model_path = tts_config.get("piper_model_path")

        if not PIPER_TTS_AVAILABLE or PiperVoice is None:
            self.logger.warning("Piper TTS library not available. Offline TTS will fall back to console output.")
            self.tts_engine = None
            return

        if not model_path or not os.path.exists(model_path):
            self.logger.error("Piper model not found. Set 'tts.piper_model_path' in config.json to a valid .onnx file.")
            self.tts_engine = None
            return

        try:
            self.tts_engine = PiperVoice.load(model_path)
            self.logger.info(f"Piper TTS initialized with model '{model_path}'")

            # Ensure pygame mixer matches the model's sample rate to avoid pitch issues
            try:
                sr_hz = int(getattr(self.tts_engine.config, "sample_rate", 22050))
                pygame.mixer.quit()
                pygame.mixer.init(frequency=sr_hz, size=-16, channels=2, buffer=512)
                pygame.mixer.music.set_volume(self.config.get("tts", {}).get("volume", 0.9))
                self.logger.info(f"Audio mixer reinitialized at {sr_hz} Hz for Piper voice")
            except Exception as reinit_err:
                self.logger.warning(f"Could not reinit mixer to Piper sample rate: {reinit_err}")

        except Exception as e:
            self.logger.error(f"Failed to initialize Piper TTS: {e}")
            self.tts_engine = None

    def initialize_assistive_modules(self):
        # camera,vision, sensor manager 이잉
        try:
            # 카메라 매니저 초기화
            if self.config.get("hardware", {}).get("camera_enabled", True):
                hardware_config = self.config.get("hardware", {})
                self.camera_manager = CameraManager(
                    camera_type=hardware_config.get("camera_type", "esp32_cam"),
                    stream_url=hardware_config.get("esp32_cam_url"),
                    connection_retries=hardware_config.get(
                        "esp32_connection_retries", 5
                    ),
                    retry_delay=hardware_config.get("esp32_retry_delay", 2.0),
                )
                self.logger.info("Camera manager initialized")
            else:
                self.camera_manager = None
                self.logger.info("Camera disabled in configuration")
            
            # OpenAI API 키로 분석기 초기화
            # api_key = self.config["ai"]["api_key"]
            # if api_key != "":
            #     self.vision_analyzer = VisionAnalyzer(api_key=api_key)
            #     self.logger.info("Vision analyzer initialized with OpenAI API")
            # else:
            #     self.vision_analyzer = VisionAnalyzer(api_key=None)
            #     self.logger.info("Vision analyzer initialized in simulation mode")
            
            # 내비게이션 센서 매니저 초기화
            if self.config.get("hardware", {}).get("sensors_enabled", True):
                sensor_port = self.config["hardware"]["sensor_port"]
                sensor_baudrate = self.config["hardware"]["sensor_baudrate"]
                #self.sensor_monitor = NavigationSensorManager(port=sensor_port, baudrate=sensor_baudrate)
                self.logger.info("Navigation sensor manager initialized")
            else:
                self.sensor_monitor = None
                self.logger.info("Sensors disabled in configuration")
                
        except Exception as e:
            self.logger.error(f"Error initializing assistive modules: {e}")
            # 하드웨어 기능 없이 계속 진행, 깨알 추가과제
            self.camera_manager = None
            self.vision_analyzer = None
            self.sensor_monitor = None
    
    def listen_for_speech(self):
        # 음성 입력 인식
        if not self.microphone:
            self.logger.error("No microphone available")
            return None
        
        try:
            # 주변 소음 보정
            #TODO: 잘 안되는 듯? -------> 필요함
            self.logger.info("Adjusting for ambient noise... Please stay quiet.")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(
                    source, 
                    duration=self.config["stt"]["ambient_noise_duration"]
                )
            
            # 음성 인식
            self.logger.info("Listening for speech...")
            print("[Whisper] Listening...")
            with self.microphone as source:
                try:
                    audio = self.recognizer.listen(
                        source, 
                        timeout=self.config["stt"]["timeout"],
                        phrase_time_limit=self.config["stt"]["phrase_time_limit"]
                    )
                    self.logger.info("Audio captured successfully")
                    return audio
                    
                except sr.WaitTimeoutError:
                    self.logger.info("No speech detected within timeout")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error listening for speech: {e}")
            return None


    
    def speech_to_text(self, audio):
        """Transcribe audio using the offline Whisper model"""
        if not self.whisper_model:
            self.logger.error("Whisper STT is unavailable - offline model not initialized")
            return None

        stt_config = self.config.get("stt", {})
        language = stt_config.get("language")
        if isinstance(language, str) and language.strip().lower() in {"", "auto"}:
            language = None

        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                temp_audio.write(audio.get_wav_data())
                temp_file_path = temp_audio.name

            transcription = self.whisper_model.transcribe(
                temp_file_path,
                fp16=self.whisper_fp16,
                language=language,
            )

            if not transcription:
                self.logger.warning("No transcription returned from Whisper")
                return None

            text = transcription.get("text", "").strip()
            if not text:
                self.logger.info("Whisper transcription was empty")
                return None

            self.logger.info(f"Whisper recognized speech: '{text}'")
            print(f"[Whisper] User said: {text}")
            return text

        except Exception as e:
            self.logger.error(f"Error in Whisper speech recognition: {e}")
            return None
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass
    
    def generate_ai_response(self, user_input):
        if not OLLAMA_AVAILABLE:
            self.logger.error("Ollama client not available")
            return "AI response is unavailable because the Ollama client is not installed."

        try:
            # If you configured a remote host, keep using it; otherwise default client
            ollama_host = self.config["ai"].get("ollama_host")
            client = ollama.Client(host=ollama_host) if ollama_host else ollama

            model_name = self.config["ai"].get("model")

            # Keep responses short and the model warm
            options = {
                "temperature": float(self.config["ai"].get("temperature", 0.2)),
                "num_predict": int(self.config["ai"].get("max_tokens", 96)),
                "keep_alive": "5m",   # avoid reloads on Pi
                "num_ctx": 2048,      # enough for brief history if you add it later
                "num_thread": 0,      # let Ollama auto-select cores
            }

            stream = client.chat(
                model=model_name,
                messages=[{"role": "user", "content": user_input}],
                options=options,
                stream=True,  # <<< streaming enabled
            )

            # Option A: collect full text, return at end (simple)
            chunks = []
            for part in stream:
                msg = part.get("message", {})
                if "content" in msg:
                    chunks.append(msg["content"])
            ai_response = "".join(chunks)

            # (Optional) log/save
            if self.config["system"].get("log_responses"):
                self.log_response(user_input, ai_response)

            return ai_response

        except Exception as e:
            self.logger.error(f"Ollama chat error: {e}")
            return "I'm sorry, I couldn't process that request due to an error."

        
    def test():

        print(12311111111111111)


    def text_to_speech(self, text):
        if not text:
            return

        model = self.config["tts"].get("piper_model_path")
        piper_bin = shutil.which("piper")  # finds the CLI on PATH

        if not piper_bin or not (model and os.path.isfile(model)):
            self.logger.warning("Piper CLI or model missing; printing instead")
            print(f"AI Response: {text}")
            return

        try:
            # make a temp wav
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fp:
                out_wav = fp.name

            # run Piper CLI (this writes a proper WAV header + audio frames)
            cmd = [piper_bin, "--model", model, "--output_file", out_wav]
            proc = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            if proc.returncode != 0 or not os.path.exists(out_wav):
                self.logger.error(f"Piper CLI failed: {proc.stderr.decode(errors='ignore')}")
                print(f"AI Response: {text}")
                return

            # play via pygame
            pygame.mixer.music.load(out_wav)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            os.unlink(out_wav)
            self.logger.info("Piper TTS (CLI) completed")

        except Exception as e:
            self.logger.error(f"Piper CLI error: {e}")
            print(f"AI Response: {text}")



    
    def log_response(self, user_input, ai_response):
       """대화 로그 남기기"""
       try:
           log_file = Path("conversation_log.txt")
           timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           
           with open(log_file, "a", encoding="utf-8") as f:
               f.write(f"[{timestamp}] User: {user_input}\n")
               f.write(f"[{timestamp}] AI: {ai_response}\n")
               f.write("-" * 50 + "\n")
               
       except Exception as e:
           self.logger.error(f"Error logging conversation: {e}")
    
    def process_conversation(self):
        # 파이프라인
        # 음성 인식
        audio = self.listen_for_speech()
        if not audio:
            return False
        
        # 음성을 텍스트로 변환
        user_input = self.speech_to_text(audio)
        if not user_input:
            self.text_to_speech("I didn't catch that. Could you please repeat?")
            return False
        
        # wake word 확인(assistant)
        # wake_word = self.config["system"]["wake_word"].lower()
        # if wake_word and wake_word not in user_input.lower():
        #     self.logger.info("Wake word not detected, ignoring input")
        #     return False
        
        # AI 응답 생성
        ai_response = self.generate_ai_response(user_input)
        print(ai_response + "11111132232")
        
        # 명령어 처리
        processed_response = self.process_ai_response(ai_response)
        
        # 응답을 음성으로 변환
        self.text_to_speech(processed_response)
        
        return True
    
    def process_ai_response(self, ai_response):
        # ai 응답 or 커맨드 실행 
        try:
            # 응답에 명령이 포함되어 있는지 확인
            if ai_response.startswith("COMMAND:"):
                # 명령어와 설명 추출
                lines = ai_response.split('\n')
                command_line = lines[0]
                description_line = lines[1] if len(lines) > 1 else ""
                
                # 명령어 이름 추출
                command_name = command_line.replace("COMMAND:", "").strip()
                description = description_line.replace("DESCRIPTION:", "").strip()
                
                self.logger.info(f"Executing command: {command_name} - {description}")
                
                # 명령 실행
                command_response = self.execute_command(command_name, description)
                return command_response
            else:
                # 일반 응답
                return ai_response
                
        except Exception as e:
            self.logger.error(f"Error processing AI response: {e}")
            return ai_response
    
    def execute_command(self, command_name, description):
        # 커맨드
        try:
            command_name = command_name.lower()
            
            # 시간 및 날짜 명령
            if command_name == "time":
                import datetime
                current_time = datetime.datetime.now().strftime("%I:%M %p")
                return f"The current time is {current_time}"
                
            elif command_name == "date":
                import datetime
                current_date = datetime.datetime.now().strftime("%B %d, %Y")
                return f"Today is {current_date}"
                
            elif command_name == "joke":
                jokes = [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "What do you call a fake noodle? An impasta!",
                    "Why did the scarecrow win an award? He was outstanding in his field!",
                    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
                    "Why don't eggs tell jokes? They'd crack each other up!"
                ]
                import random
                return random.choice(jokes)
                
            elif command_name == "status":
                return self.get_system_status()
                
            elif command_name == "help":
                return self.get_help_information()
            
            # 카메라 및 비전 명령
            elif command_name == "capture_image":
                return self.capture_and_analyze_image("general")
                
            elif command_name == "describe_surroundings":
                return self.capture_and_analyze_image("surroundings")
                
            elif command_name == "read_text":
                return self.capture_and_analyze_image("text")
                
            elif command_name == "identify_objects":
                return self.capture_and_analyze_image("objects")
            
            # 내비게이션 및 센서 명령
            elif command_name == "navigate":
                return self.start_navigation_monitoring()
                
            elif command_name == "stop_navigation":
                return self.stop_navigation_monitoring()
                
            elif command_name == "navigation_status":
                return self.get_navigation_status()
                
            elif command_name == "distance":
                return self.measure_distance()
                
            elif command_name == "obstacles":
                return self.detect_obstacles()
                
            elif command_name == "weather":
                return "I understand you want weather information. This feature requires weather API integration which is not currently available."
                
            else:
                return f"I received the command '{command_name}' but I'm not sure how to execute it yet. Please try a different command."
                
        except Exception as e:
            self.logger.error(f"Error executing command {command_name}: {e}")
            return f"Sorry, there was an error executing the {command_name} command."
    
    def capture_and_analyze_image(self, analysis_type="general"):
        # 요청에 따른 카메라 촬영 답변
        try:
            if not self.camera_manager:
                return "Camera is not available. Please check camera connection."
            
            if not self.vision_analyzer:
                return "Vision analysis is not available. Please check OpenAI API configuration."
            
            # 이미지 캡처
            self.text_to_speech("Capturing image...")
            image_path = self.camera_manager.capture_image()
            
            if not image_path:
                return "Failed to capture image. Please try again."
            
            # 유형에 따라 분석
            if analysis_type == "text":
                analysis = self.vision_analyzer.analyze_with_specific_focus(image_path, "text")
            elif analysis_type == "objects":
                analysis = self.vision_analyzer.analyze_with_specific_focus(image_path, "objects")
            elif analysis_type == "surroundings":
                analysis = self.vision_analyzer.analyze_with_specific_focus(image_path, "navigation")
            else:
                analysis = self.vision_analyzer.analyze_image(image_path)
            
            if analysis:
                return f"Analysis complete: {analysis}"
            else:
                return "Sorry, I couldn't analyze the image. Please try again."
                
        except Exception as e:
            self.logger.error(f"Error in image capture and analysis: {e}")
            return "An error occurred during image analysis. Please try again."
    
    def check_navigation_safety(self):
        # 네비게이션 --> 카메라와 센서
        try:
            # 센서 데이터 가져오기
            sensor_response = self.get_sensor_data()
            
            # 환경 초ㅏㄹ영 및 분석
            camera_response = self.capture_and_analyze_image("surroundings")
            
            # 센서와 카메라 데이터 결합
            if "obstacle" in sensor_response.lower() or "close" in sensor_response.lower():
                return f"Navigation warning: {sensor_response}. Additionally, {camera_response}"
            else:
                return f"Navigation assessment: {sensor_response}. {camera_response}"
                
        except Exception as e:
            self.logger.error(f"Error checking navigation safety: {e}")
            return "Unable to assess navigation safety. Please proceed with caution."
    
    def start_navigation_monitoring(self):
        # 센서로 모니터링
        try:
            if self.navigation_active:
                return "Navigation monitoring is already active."
            
            if not self.sensor_monitor:
                return "Sensors are not available. Cannot start navigation monitoring."
            
            # 센서 매니저로 내비게이션 모니터링 시작
            if self.sensor_monitor.start_navigation_monitoring():
                self.navigation_active = True
                self.logger.info("Navigation monitoring started")
                
                return "Navigation monitoring activated. I will continuously monitor for obstacles and provide real-time updates. Say 'stop navigation' to end monitoring."
            else:
                return "Failed to start navigation monitoring. Please check sensor connection."
            
        except Exception as e:
            self.logger.error(f"Error starting navigation monitoring: {e}")
            return "Failed to start navigation monitoring. Please try again."
    
    def stop_navigation_monitoring(self):
        # 모니터링 중지
        try:
            if not self.navigation_active:
                return "Navigation monitoring is not currently active."
            
            # 중지
            if self.sensor_monitor.stop_navigation_monitoring():
                self.navigation_active = False
                self.logger.info("Navigation monitoring stopped")
                return "Navigation monitoring stopped. You are no longer receiving real-time updates."
            else:
                return "Error stopping navigation monitoring."
            
        except Exception as e:
            self.logger.error(f"Error stopping navigation monitoring: {e}")
            return "Error stopping navigation monitoring."
    
    def get_navigation_status(self):
        # 센서를 통한 상황파악
        if self.navigation_active:
            return "Navigation monitoring is currently active. Say 'stop navigation' to end monitoring."
        else:
            return "Navigation monitoring is not active. Say 'start navigation' to begin monitoring."
    
    def _on_distance_update(self, distance: float):
        # 거리 업데이트 
        self.logger.debug(f"Distance update: {distance:.1f} cm")
    
    def _on_navigation_warning(self, message: str):
        # 경고 callback
        self.logger.info(f"Navigation warning: {message}")
        # 사용자에게 경고 음성 출력
        self.text_to_speech(message)
 
        if hasattr(self, 'sensor_monitor') and self.sensor_monitor:
            self.sensor_monitor.mark_speech_complete()
    
    def _on_sensor_status_change(self, status):
        # 센서 상태
        self.logger.info(f"Sensor status changed to: {status.value}")
    
    def detect_obstacles(self):
        # 장애물 감지
        try:
            # 센서 데이터 가져오기
            sensor_response = self.get_sensor_data()
            
            # 장애물 분석을 위해 캡처 및 분석
            camera_response = self.capture_and_analyze_image("hazards")
            
            return f"Obstacle detection: {sensor_response}. {camera_response}"
                
        except Exception as e:
            self.logger.error(f"Error detecting obstacles: {e}")
            return "Unable to detect obstacles. Please proceed with caution."
    
    def get_sensor_data(self):
        # 데이터 가져오기
        try:
            if not self.sensor_monitor:
                return "Sensors are not available. Please check sensor connection."
            
            distance = self.sensor_monitor.get_latest_distance()
            
            if distance is None:
                return "No sensor data available. Please check sensor connection."
            
            # 거리 데이터 해석
            if distance < 30:
                return f"Warning! Obstacle very close at {distance} centimeters."
            elif distance < 100:
                return f"Caution, object detected at {distance} centimeters ahead."
            elif distance < 200:
                return f"Object detected at {distance} centimeters. Path is clear but be aware."
            else:
                return f"Path appears clear. No obstacles detected within {distance} centimeters."
                
        except Exception as e:
            self.logger.error(f"Error getting sensor data: {e}")
            return "Unable to read sensor data. Please check sensor connection."
    
    def get_system_status(self):
        # 모듈 상태 
        try:
            status_parts = []
            
            # 기본 시스템 상태
            status_parts.append("INTA AI system is running normally.")
            
            # 카메라 상태
            if self.camera_manager:
                camera_info = self.camera_manager.get_camera_info()
                status_parts.append(f"Camera: {camera_info['status']}")
            else:
                status_parts.append("Camera: Not available")
            
            # 분석기 상태
            if self.vision_analyzer:
                vision_stats = self.vision_analyzer.get_analysis_stats()
                status_parts.append(f"Vision analysis: {vision_stats['mode']} mode")
            else:
                status_parts.append("Vision analysis: Not available")
            
            # 센서 상태
            if self.sensor_monitor:
                sensor_data = self.get_sensor_data()
                status_parts.append(f"Sensors: {sensor_data}")
            else:
                status_parts.append("Sensors: Not available")
            
            return " ".join(status_parts)
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return "System status check failed. Basic functions are operational."
    
    def get_help_information(self):
        """Get comprehensive help information"""
        return """I am INTA, your AI assistant for visually impaired users. I can help you with:

CAMERA & VISION:
- Take pictures and describe what I see
- Read text and signs for you
- Identify objects in your environment
- Describe your surroundings

NAVIGATION & SAFETY:
- Start continuous navigation monitoring with real-time obstacle detection
- Stop navigation monitoring when you're done
- Check navigation status
- Measure distances to objects
- Detect obstacles ahead
- Provide real-time safety warnings (warns when objects are closer than 50cm)

UTILITIES:
- Tell you the time and date
- Tell jokes to cheer you up
- Check system status
- Provide help information

NAVIGATION COMMANDS:
- "Start navigation" or "Help me walk" - Begin continuous monitoring
- "Stop navigation" or "Stop guiding me" - End monitoring
- "Navigation status" - Check if monitoring is active

Just speak naturally! I understand context, so you can say things like:
"I can't see what's ahead" or "What's in this room?" and I'll know what you need."""
    
    def start(self):
        # 시스템 루프
        self.logger.info("Starting Simple STT System...")
        self.running = True
        
        # ㅎㅇ
        self.text_to_speech("Assistance glasses is ready. Start speaking!")
        
        try:
            while self.running:
                self.process_conversation()
                time.sleep(0.1)  # Small delay to prevent CPU overuse
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
            self.shutdown()
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
            self.shutdown()
    
    def shutdown(self):
        # 샷다
        self.logger.info("Shutting down INTA AI Assistant...")
        self.running = False
        
        # 내비게이션 모니터링이 활성화된 경우 중지
        if self.navigation_active:
            self.stop_navigation_monitoring()
            self.logger.info("Navigation monitoring stopped during shutdown")
        
        # 하드웨어 모듈 정리
        if hasattr(self, 'camera_manager') and self.camera_manager:
            self.camera_manager.cleanup()
            self.logger.info("Camera manager cleaned up")
        
        if hasattr(self, 'sensor_monitor') and self.sensor_monitor:
            self.sensor_monitor.cleanup()
            self.logger.info("Navigation sensor manager cleaned up")
        
        # 오디오 시스템 정리
        try:
            import pygame
            pygame.mixer.quit()
            self.logger.info("Audio system cleaned up")
        except Exception as e:
            self.logger.debug(f"Audio cleanup error: {e}")
        
        self.text_to_speech("Goodbye! INTA AI Assistant shutting down.")
        self.logger.info("System shutdown complete")







def main():
    try:
        system = IntaAIAssistant()
        system.start()
        
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
