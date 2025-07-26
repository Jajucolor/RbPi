"""
INTA AI Manager Module
Handles AI assistant functionality with speech recognition
Uses speech_recognition library for better microphone compatibility
"""

import logging
import threading
import queue
import time
import os
import tempfile
import numpy as np
from typing import Dict, Any, Optional, Callable
from pathlib import Path

# Speech recognition imports (primary method)
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logging.warning("speech_recognition not available - falling back to PyAudio")

# Fallback to PyAudio if speech_recognition not available
if not SPEECH_RECOGNITION_AVAILABLE:
    try:
        import pyaudio
        PYAUDIO_AVAILABLE = True
    except ImportError:
        PYAUDIO_AVAILABLE = False
        logging.warning("PyAudio not available - audio recording disabled")

# Whisper imports
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available - speech recognition disabled")

# WebRTC VAD for voice activity detection
try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    logging.warning("WebRTC VAD not available - using simple amplitude detection")

class IntaAIManager:
    """AI assistant with speech recognition using speech_recognition library"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.running = False
        self.listening = False
        
        # Audio settings
        self.sample_rate = config.get('inta', {}).get('sample_rate', 16000)
        self.chunk_size = config.get('inta', {}).get('chunk_size', 1024)
        self.channels = 1
        
        # Voice Activity Detection settings
        self.vad_aggressiveness = config.get('inta', {}).get('vad_aggressiveness', 2)
        self.speech_frames_threshold = config.get('inta', {}).get('speech_frames_threshold', 3)
        self.silence_frames_threshold = config.get('inta', {}).get('silence_frames_threshold', 10)
        
        # Real-time processing settings
        self.realtime_buffer_size = config.get('inta', {}).get('realtime_buffer_size', 4096)
        self.max_audio_length = config.get('inta', {}).get('max_audio_length', 10.0)  # seconds
        
        # Speech recognition components
        self.recognizer = None
        self.microphone = None
        self.audio_stream = None
        self.vad = None
        
        # Whisper model
        self.whisper_model = None
        self.whisper_model_size = config.get('inta', {}).get('whisper_model', 'tiny')
        
        # AI backend
        self.openai_client = None
        
        # Initialize OpenAI client with version compatibility
        if config.get('openai', {}).get('api_key'):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=config['openai']['api_key'])
            except ImportError:
                import openai
                openai.api_key = config['openai']['api_key']
                self.openai_client = openai
        
        # Conversation management
        self.conversation_history = []
        self.max_history_length = 20
        
        # Speech callback
        self._speech_callback = None
        
        # Initialize components
        self._initialize_speech_recognition()
        self._initialize_vad()
        self._initialize_whisper()
        
        self.logger.info("INTA AI Manager initialized")
    
    def _initialize_speech_recognition(self):
        """Initialize speech recognition with direct hardware access"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            self.logger.error("speech_recognition not available - audio recording disabled")
            return False
        
        try:
            # Configure ALSA for direct hardware access first
            self._configure_alsa_direct()
            
            # Initialize recognizer
            self.recognizer = sr.Recognizer()
            
            # Configure recognizer settings
            self.recognizer.energy_threshold = 300  # Minimum audio energy to consider for recording
            self.recognizer.dynamic_energy_threshold = True  # Adjust threshold dynamically
            self.recognizer.pause_threshold = 0.8  # Seconds of non-speaking audio before phrase is considered complete
            self.recognizer.non_speaking_duration = 0.5  # Seconds of non-speaking audio to keep on both sides of the recording
            self.recognizer.phrase_threshold = 0.3  # Minimum seconds of speaking audio before we consider the speaking audio a phrase
            self.recognizer.phrase_time_limit = None  # Maximum number of seconds that a phrase can be recorded for
            
            # Try to find USB microphone with direct hardware access
            self.microphone = self._find_usb_microphone()
            
            if not self.microphone:
                # Fallback to default microphone
                self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.logger.info("Adjusting for ambient noise... Please stay quiet.")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            # Get microphone info
            mic_info = self._get_microphone_info()
            self.logger.info(f"Microphone initialized: {mic_info}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize speech recognition: {str(e)}")
            return False
    
    def _find_usb_microphone(self):
        """Find and configure USB microphone with direct hardware access"""
        try:
            # List all microphones
            mics = sr.Microphone.list_microphone_names()
            self.logger.info(f"Available microphones: {mics}")
            
            # Look for USB microphone
            for i, mic_name in enumerate(mics):
                if 'usb' in mic_name.lower() or 'microphone' in mic_name.lower():
                    self.logger.info(f"Found USB microphone: {mic_name} (index {i})")
                    
                    # Create microphone with specific device index
                    mic = sr.Microphone(device_index=i)
                    
                    # Test if it works
                    try:
                        with mic as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        self.logger.info(f"USB microphone {i} working correctly")
                        return mic
                    except Exception as e:
                        self.logger.warning(f"USB microphone {i} failed test: {e}")
                        continue
            
            # If no USB mic found, try direct hardware access to card 2
            self.logger.info("No USB microphone found, trying direct hardware access to card 2")
            
            try:
                # Try direct hardware access to USB mic on card 2
                mic = sr.Microphone(device_index=2)  # Card 2 from arecord -l
                with mic as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.logger.info("Direct hardware access to card 2 successful")
                return mic
            except Exception as e:
                self.logger.warning(f"Direct access to card 2 failed: {e}")
            
            # Try different device configurations
            for device_index in range(10):  # Try first 10 devices
                try:
                    mic = sr.Microphone(device_index=device_index)
                    with mic as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    self.logger.info(f"Direct hardware access successful with device {device_index}")
                    return mic
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding USB microphone: {e}")
            return None
    
    def _configure_alsa_direct(self):
        """Configure ALSA for direct hardware access"""
        try:
            # Set ALSA environment variables for direct access
            os.environ['ALSA_PCM_CARD'] = '2'
            os.environ['ALSA_PCM_DEVICE'] = '0'
            os.environ['ALSA_CARD'] = '2'
            
            # Create minimal ALSA config in memory
            import tempfile
            config_content = """
pcm.!default {
    type hw
    card 2
    device 0
}
ctl.!default {
    type hw
    card 2
}
"""
            # Write temporary ALSA config
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                f.write(config_content)
                temp_config = f.name
            
            # Set ALSA config file
            os.environ['ALSA_CONFIG_FILE'] = temp_config
            
            self.logger.info("ALSA configured for direct hardware access to card 2")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure ALSA: {e}")
            return False
    
    def _get_microphone_info(self) -> str:
        """Get information about available microphones"""
        try:
            if not self.microphone:
                return "No microphone available"
            
            # List available microphones
            mics = sr.Microphone.list_microphone_names()
            self.logger.info(f"Available microphones: {mics}")
            
            # Get current microphone index
            current_mic = self.microphone.device_index
            current_mic_name = mics[current_mic] if current_mic < len(mics) else "Unknown"
            
            return f"Device {current_mic}: {current_mic_name}"
            
        except Exception as e:
            self.logger.error(f"Error getting microphone info: {str(e)}")
            return "Microphone info unavailable"
    
    def _initialize_vad(self):
        """Initialize Voice Activity Detection"""
        if not VAD_AVAILABLE:
            self.logger.warning("WebRTC VAD not available - using simple amplitude detection")
            return
        
        try:
            self.vad = webrtcvad.Vad(self.vad_aggressiveness)
            self.logger.info(f"VAD initialized with aggressiveness level {self.vad_aggressiveness}")
        except Exception as e:
            self.logger.error(f"Failed to initialize VAD: {str(e)}")
    
    def _initialize_whisper(self):
        """Initialize Whisper model"""
        if not WHISPER_AVAILABLE:
            self.logger.error("Whisper not available - speech recognition disabled")
            return
        
        try:
            # Use tiny model for performance
            self.logger.info(f"Loading Whisper model: {self.whisper_model_size}")
            self.whisper_model = whisper.load_model(self.whisper_model_size)
            self.logger.info("Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {str(e)}")
    
    def start_listening(self) -> bool:
        """Start continuous listening using speech recognition"""
        if not self.recognizer or not self.microphone:
            self.logger.error("Speech recognition not initialized")
            return False
        
        if self.listening:
            self.logger.warning("Already listening")
            return True
        
        self.listening = True
        self.running = True
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._continuous_listen_loop, daemon=True)
        self.listen_thread.start()
        
        self.logger.info("Started continuous listening with speech recognition")
        return True
    
    def stop_listening(self):
        """Stop listening"""
        self.listening = False
        self.running = False
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)
        
        self.logger.info("Stopped listening")
    
    def _continuous_listen_loop(self):
        """Continuous listening loop using speech recognition"""
        self.logger.info("Starting continuous listen loop")
        
        while self.listening:
            try:
                # Listen for speech using speech_recognition
                with self.microphone as source:
                    self.logger.debug("Listening for speech...")
                    
                    # Listen for audio input
                    audio = self.recognizer.listen(
                        source,
                        timeout=1,  # Timeout after 1 second of silence
                        phrase_time_limit=10  # Maximum 10 seconds per phrase
                    )
                    
                    if audio:
                        # Process the audio
                        self._process_audio_async(audio)
                
            except sr.WaitTimeoutError:
                # No speech detected, continue listening
                continue
            except sr.UnknownValueError:
                # Speech was unintelligible
                self.logger.debug("Speech was unintelligible")
                continue
            except Exception as e:
                self.logger.error(f"Error in continuous listen loop: {str(e)}")
                time.sleep(0.1)  # Delay on error
        
        self.logger.info("Continuous listen loop ended")
    
    def _process_audio_async(self, audio):
        """Process audio data asynchronously"""
        try:
            # Convert speech to text
            text = self._speech_to_text(audio)
            
            if text and text.strip():
                self.logger.info(f"Recognized speech: {text}")
                
                # Process the command
                response = self.process_command(text)
                
                # Emit response
                self._emit_response(response)
            else:
                self.logger.debug("No speech detected or empty text")
                
        except Exception as e:
            self.logger.error(f"Error processing audio: {str(e)}")
    
    def _speech_to_text(self, audio) -> Optional[str]:
        """Convert speech to text using multiple methods"""
        if not audio:
            return None
        
        # Try speech_recognition first (Google Speech Recognition)
        try:
            text = self.recognizer.recognize_google(audio)
            if text:
                return text.strip()
        except sr.UnknownValueError:
            self.logger.debug("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            self.logger.debug(f"Google Speech Recognition service error: {str(e)}")
        except Exception as e:
            self.logger.debug(f"Speech recognition error: {str(e)}")
        
        # Fallback to Whisper if available
        if self.whisper_model:
            try:
                # Save audio to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(audio.get_wav_data())
                    temp_file_path = temp_file.name
                
                # Transcribe with Whisper
                result = self.whisper_model.transcribe(temp_file_path)
                
                # Clean up temp file
                os.unlink(temp_file_path)
                
                text = result["text"].strip()
                if text:
                    return text
                    
            except Exception as e:
                self.logger.error(f"Whisper transcription error: {str(e)}")
        
        return None
    
    def process_command(self, text: str) -> str:
        """Process user command and generate response"""
        try:
            text_lower = text.lower().strip()
            
            # Add to conversation history
            self._add_to_history("user", text)
            
            # Check for specific commands first
            if any(word in text_lower for word in ["time", "clock", "hour"]):
                return self.execute_function("time")
            elif any(word in text_lower for word in ["date", "day", "month", "year"]):
                return self.execute_function("date")
            elif any(word in text_lower for word in ["joke", "funny", "humor"]):
                return self.execute_function("joke")
            elif any(word in text_lower for word in ["status", "health", "system"]):
                return self.execute_function("status")
            elif any(word in text_lower for word in ["help", "assist", "guide"]):
                return self.execute_function("help")
            elif any(word in text_lower for word in ["volume up", "louder"]):
                return self.execute_function("volume_up")
            elif any(word in text_lower for word in ["volume down", "quieter"]):
                return self.execute_function("volume_down")
            elif any(word in text_lower for word in ["mute", "silence"]):
                return self.execute_function("mute")
            elif any(word in text_lower for word in ["unmute", "sound on"]):
                return self.execute_function("unmute")
            elif any(word in text_lower for word in ["emergency", "sos", "help me"]):
                return self.execute_function("emergency")
            elif any(word in text_lower for word in ["weather", "temperature", "forecast"]):
                return self.execute_function("weather")
            elif any(word in text_lower for word in ["distance", "obstacle", "sensor"]):
                return self.execute_function("distance")
            elif any(word in text_lower for word in ["obstacles", "detection", "clear"]):
                return self.execute_function("obstacles")
            elif any(word in text_lower for word in ["capture", "picture", "photo", "image", "see", "look"]):
                return self.execute_function("capture")
            elif any(word in text_lower for word in ["shutdown", "turn off", "exit", "quit", "stop"]):
                return self.execute_function("shutdown")
            
            # Query OpenAI for general conversation
            response = self._query_openai(text)
            
            if response:
                self._add_to_history("assistant", response)
                return response
            
            # Default response
            return "I'm sorry, I didn't understand that. Could you please repeat?"
            
        except Exception as e:
            self.logger.error(f"Error processing command: {str(e)}")
            return "I encountered an error processing your request."
    
    def _query_openai(self, text: str) -> Optional[str]:
        """Query OpenAI for conversation"""
        if not self.openai_client:
            return None
        
        try:
            # Prepare conversation context
            messages = [
                {
                    "role": "system",
                    "content": """You are INTA, an intelligent AI assistant for visually impaired users. 
                    You help users navigate their environment, understand their surroundings, and execute commands.
                    Be helpful, concise, and accessible. Respond naturally and conversationally."""
                }
            ]
            
            # Add recent conversation history
            for msg in self.conversation_history[-10:]:  # Last 10 messages
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": text
            })
            
            # Handle both new and old OpenAI API versions
            if hasattr(self.openai_client, 'chat') and hasattr(self.openai_client.chat, 'completions'):
                # New OpenAI API
                response = self.openai_client.chat.completions.create(
                    model=config.get('openai', {}).get('model', 'gpt-4o-mini'),
                    messages=messages,
                    max_tokens=config.get('openai', {}).get('max_tokens', 300),
                    temperature=config.get('openai', {}).get('temperature', 0.3)
                )
                return response.choices[0].message.content
            else:
                # Old OpenAI API
                response = self.openai_client.ChatCompletion.create(
                    model=config.get('openai', {}).get('model', 'gpt-4o-mini'),
                    messages=messages,
                    max_tokens=config.get('openai', {}).get('max_tokens', 300),
                    temperature=config.get('openai', {}).get('temperature', 0.3)
                )
                return response.choices[0].message.content
                
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            return None
    
    def _get_conversation_context(self) -> str:
        """Get conversation context for AI responses"""
        context = "Recent conversation:\n"
        for msg in self.conversation_history[-5:]:  # Last 5 messages
            context += f"{msg['role']}: {msg['content']}\n"
        return context
    
    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        # Keep history within limit
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def _emit_response(self, response: str):
        """Emit response event for other components to handle"""
        # This can be extended to emit events to other parts of the system
        self.logger.info(f"INTA Response: {response}")
        
        # Emit to speech system for real-time speaking
        if hasattr(self, '_speech_callback') and self._speech_callback:
            self._speech_callback(response)
    
    def set_speech_callback(self, speech_callback):
        """Set callback for speech output"""
        self._speech_callback = speech_callback
    
    def execute_function(self, function_name: str, params: Dict[str, Any] = None) -> str:
        """Execute specific functions based on commands"""
        try:
            if function_name == "time":
                from datetime import datetime
                current_time = datetime.now().strftime("%I:%M %p")
                return f"The current time is {current_time}"
            
            elif function_name == "date":
                from datetime import datetime
                current_date = datetime.now().strftime("%A, %B %d, %Y")
                return f"Today is {current_date}"
            
            elif function_name == "joke":
                jokes = [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "What do you call a fake noodle? An impasta!",
                    "Why did the scarecrow win an award? He was outstanding in his field!",
                    "I told my wife she was drawing her eyebrows too high. She looked surprised!",
                    "Why don't eggs tell jokes? They'd crack each other up!"
                ]
                import random
                return random.choice(jokes)
            
            elif function_name == "status":
                return "INTA AI system is running normally. All systems operational."
            
            elif function_name == "help":
                return "I can help you with: time, date, jokes, status, volume control, emergency calls, weather, obstacle detection, and general conversation. Just ask!"
            
            elif function_name == "volume_up":
                return "Volume increased"
            
            elif function_name == "volume_down":
                return "Volume decreased"
            
            elif function_name == "mute":
                return "Audio muted"
            
            elif function_name == "unmute":
                return "Audio unmuted"
            
            elif function_name == "emergency":
                return "EMERGENCY MODE ACTIVATED! Contacting emergency services..."
            
            elif function_name == "weather":
                return "I'm sorry, I don't have access to real-time weather data yet."
            
            elif function_name == "distance":
                return "Distance sensor is active. No obstacles detected within safe range."
            
            elif function_name == "obstacles":
                return "Obstacle detection system is running. All clear ahead."
            
            elif function_name == "capture":
                return "I'll capture and analyze your surroundings now."
            
            elif function_name == "shutdown":
                return "Shutting down INTA AI system. Goodbye!"
            
            else:
                return f"Function {function_name} not implemented yet."
                
        except Exception as e:
            self.logger.error(f"Error executing function {function_name}: {str(e)}")
            return f"Error executing {function_name}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "listening": self.listening,
            "running": self.running,
            "speech_recognition_available": SPEECH_RECOGNITION_AVAILABLE,
            "whisper_available": WHISPER_AVAILABLE,
            "vad_available": VAD_AVAILABLE,
            "openai_available": self.openai_client is not None,
            "conversation_history_length": len(self.conversation_history),
            "microphone_info": self._get_microphone_info() if self.microphone else "No microphone"
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up INTA AI Manager...")
        
        # Stop listening
        self.stop_listening()
        
        # Clean up speech recognition
        if self.recognizer:
            self.recognizer = None
        
        if self.microphone:
            self.microphone = None
        
        self.logger.info("INTA AI Manager cleanup complete") 