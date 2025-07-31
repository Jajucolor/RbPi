import logging
import speech_recognition as sr
import time
import json
import os
from datetime import datetime
import sys
from pathlib import Path
from gtts import gTTS
import pygame
import tempfile
import os
import openai

from modules.camera_manager import CameraManager
from modules.vision_analyzer import VisionAnalyzer
from modules.sensor_manager import NavigationSensorManager

# 추곽가과제로그형식
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
                "phrase_time_limit": 5
            },
            "ai": {
                "model": "gpt-4o-mini",
                "max_tokens": 150,
                "temperature": 0.7,
                "api_key": "your-openai-api-key-here"
            },
            "tts": {
                "rate": 200,
                "volume": 0.9
            },
            "system": {
                "wake_word": "hey assistant",
                "log_responses": True
            },
            "hardware": {
                "camera_enabled": True,
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
    
    def initialize_assistive_modules(self):
        # camera,vision, sensor manager 이잉
        try:
            # 카메라 매니저 초기화
            if self.config.get("hardware", {}).get("camera_enabled", True):
                self.camera_manager = CameraManager()
                self.logger.info("Camera manager initialized")
            else:
                self.camera_manager = None
                self.logger.info("Camera disabled in configuration")
            
            # OpenAI API 키로 분석기 초기화
            api_key = self.config["ai"]["api_key"]
            if api_key != "your-openai-api-key-here":
                self.vision_analyzer = VisionAnalyzer(api_key=api_key)
                self.logger.info("Vision analyzer initialized with OpenAI API")
            else:
                self.vision_analyzer = VisionAnalyzer(api_key=None)
                self.logger.info("Vision analyzer initialized in simulation mode")
            
            # 내비게이션 센서 매니저 초기화
            if self.config.get("hardware", {}).get("sensors_enabled", True):
                sensor_port = self.config["hardware"]["sensor_port"]
                sensor_baudrate = self.config["hardware"]["sensor_baudrate"]
                self.sensor_monitor = NavigationSensorManager(port=sensor_port, baudrate=sensor_baudrate)
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
        # google speech_recognition 을 활용한 stt
        try:
            text = self.recognizer.recognize_google(audio)
            self.logger.info(f"Recognized speech: '{text}'")
            return text
            
        except sr.UnknownValueError:
            self.logger.warning("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Google Speech Recognition service error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error in speech recognition: {e}")
            return None
    
    def generate_ai_response(self, user_input):
        # t2t? openai에게 음성 정보 보내고 답 받기
        try:
            
            # 설정에서 API...
            api_key = self.config["ai"]["api_key"]
            if api_key == "your-openai-api-key-here":
                self.logger.warning("OpenAI API key not configured, using fallback response")
                return f"I heard you say: '{user_input}'. Please configure your OpenAI API key in config.json."
            
            # OpenAI API 로 클라이언트 설정
            client = openai.OpenAI(api_key=api_key)
            
            # 프롬프트
            system_prompt = """You are INTA, an advanced AI assistant for visually impaired users. You have access to a camera, ultrasonic sensors, and infrared sensors to help users navigate and understand their environment. Do not say more than 3 sentences.

            Analyze the user's request and determine what command they want to execute. Understand contextual language - users may not use exact keywords but express their needs naturally.

            Available commands and their contextual variations:

            CAMERA & VISION COMMANDS:
            - capture_image: "take a picture", "what do you see", "describe what's around me", "show me my surroundings", "what's in front of me"
            - describe_surroundings: "what's the environment like", "describe the area", "what's around here", "tell me about this place"
            - read_text: "read that sign", "what does that say", "read the text", "what's written there", "read the label"
            - identify_objects: "what objects do you see", "what's that thing", "identify what's there", "what items are visible"

            NAVIGATION & SENSOR COMMANDS:
            - navigate: "help me walk", "is it safe to move forward", "guide me", "help me navigate", "which way should I go", "start navigation", "begin navigation"
            - stop_navigation: "stop navigation", "end navigation", "stop guiding me", "stop monitoring", "stop walking assistance"
            - navigation_status: "navigation status", "is navigation active", "am I being guided", "navigation status check"
            - distance: "how far is that", "measure the distance", "how close is that object", "what's the distance"
            - obstacles: "are there any obstacles", "what's blocking my path", "is the way clear", "any hazards ahead", "check for obstacles"

            UTILITY COMMANDS:
            - time: "what time is it", "tell me the time", "current time"
            - date: "what's today's date", "what day is it", "current date"
            - weather: "what's the weather like", "weather forecast", "is it raining"
            - joke: "tell me a joke", "make me laugh", "say something funny"
            - status: "system status", "how are you working", "are you functioning properly"
            - help: "help", "what can you do", "show me your capabilities"

            RESPONSE FORMAT:
            If the user's request matches one of these commands, respond with:
            COMMAND: [command_name]
            DESCRIPTION: [brief description of what you understood]

            If it doesn't match any command, respond with:
            [natural response]

            Be intelligent and contextual. Users may say things like:
            - "I can't see what's ahead" → COMMAND: obstacles
            - "What's in this room?" → COMMAND: describe_surroundings  
            - "I need to read something" → COMMAND: read_text
            - "Is it safe to walk?" → COMMAND: navigate
            - "What's that object?" → COMMAND: identify_objects"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # api 호출
            response = client.chat.completions.create(
                model=self.config["ai"]["model"],
                messages=messages,
                max_tokens=self.config["ai"]["max_tokens"],
                temperature=self.config["ai"]["temperature"]
            )
            
            ai_response = response.choices[0].message.content
            
            # 상호작용 로그
            if self.config["system"]["log_responses"]:
                self.log_response(user_input, ai_response)
            
            return ai_response
            
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return "I'm sorry, I couldn't process that request due to an error."
    
    def text_to_speech(self, text):
        #gtts 를 이용한 tts 모델
        try:
            # 오디오를 위한 임시 파일 생성(이후에 gtts로 덮어쓴다)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_filename = fp.name
            
            # 음성 생성
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_filename)
            
            # 오디오 재생
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # 오디오가 끝날 때까지 대기
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # 정리
            os.unlink(temp_filename)
            
            self.logger.info(f"TTS completed: '{text}'")
            
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {e}")
            # 에러 발생 시 프린트로 대체
            print(f"AI Response: {text}")
    
    #def log_response(self, user_input, ai_response):
    #    """대화 로그 남기기"""
    #    try:
    #        log_file = Path("conversation_log.txt")
    #        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #        
    #        with open(log_file, "a", encoding="utf-8") as f:
    #            f.write(f"[{timestamp}] User: {user_input}\n")
    #            f.write(f"[{timestamp}] AI: {ai_response}\n")
    #            f.write("-" * 50 + "\n")
    #            
    #    except Exception as e:
    #        self.logger.error(f"Error logging conversation: {e}")
    
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
        wake_word = self.config["system"]["wake_word"].lower()
        if wake_word and wake_word not in user_input.lower():
            self.logger.info("Wake word not detected, ignoring input")
            return False
        
        # AI 응답 생성
        ai_response = self.generate_ai_response(user_input)
        
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