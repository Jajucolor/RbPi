import logging
import threading
import queue
import time
import json
import requests
import openai
from typing import Optional, Dict, Any, List
from pathlib import Path
import tempfile
import os

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper not available - speech recognition disabled")

try:
    import pyaudio
    import wave
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("PyAudio not available - audio recording disabled")

class IntaAIManager:
    """INTA AI Assistant Manager for assistive glasses"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.running = False
        self.listening = False
        
        # Initialize components
        self.whisper_model = None
        self.audio_stream = None
        self.audio = None
        
        # Conversation state
        self.conversation_history = []
        self.max_history_length = 20
        
        # OpenAI for fallback
        self.openai_client = None
        if config.get('openai', {}).get('api_key'):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=config['openai']['api_key'])
            except ImportError:
                # Fallback for older versions
                import openai
                openai.api_key = config['openai']['api_key']
                self.openai_client = openai
        
        # Audio recording settings
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.record_seconds = 5
        self.silence_threshold = 0.01
        self.silence_duration = 1.0
        
        # Threading
        self.listen_thread = None
        self.command_queue = queue.Queue()
        
        # Initialize Whisper
        self._initialize_whisper()
        
        # Initialize audio recording
        self._initialize_audio()
        
        self.logger.info("INTA AI Manager initialized")
    
    def _initialize_whisper(self):
        """Initialize Whisper model for speech recognition"""
        if not WHISPER_AVAILABLE:
            self.logger.error("Whisper not available - speech recognition disabled")
            return
        
        try:
            self.logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
            self.logger.info("Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {str(e)}")
    
    def _initialize_audio(self):
        """Initialize audio recording capabilities"""
        if not AUDIO_AVAILABLE:
            self.logger.error("PyAudio not available - audio recording disabled")
            return
        
        try:
            self.audio = pyaudio.PyAudio()
            self.logger.info("Audio system initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize audio: {str(e)}")
    
    def start_listening(self):
        """Start continuous listening for voice commands"""
        if not self.whisper_model or not self.audio:
            self.logger.error("Cannot start listening - missing dependencies")
            return False
        
        if self.listening:
            self.logger.warning("Already listening")
            return True
        
        self.listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        self.logger.info("Started listening for voice commands")
        return True
    
    def stop_listening(self):
        """Stop listening for voice commands"""
        self.listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=5)
        self.logger.info("Stopped listening for voice commands")
    
    def _listen_loop(self):
        """Main listening loop for voice commands"""
        while self.listening:
            try:
                # Record audio
                audio_data = self._record_audio()
                if audio_data is None:
                    continue
                
                # Convert speech to text
                text = self._speech_to_text(audio_data)
                if text and text.strip():
                    self.logger.info(f"Recognized: {text}")
                    
                    # Process the command
                    response = self.process_command(text)
                    
                    # Add to conversation history
                    self._add_to_history("user", text)
                    self._add_to_history("assistant", response)
                    
                    # Emit response event
                    self._emit_response(response)
                
            except Exception as e:
                self.logger.error(f"Error in listening loop: {str(e)}")
                time.sleep(1)
    
    def _record_audio(self) -> Optional[bytes]:
        """Record audio from microphone"""
        if not self.audio:
            return None
        
        DEVICE_INDEX = 1
        
        try:
            # Open audio stream with proper format for Whisper
            stream = self.audio.open(
                format=pyaudio.paInt16,  # Use 16-bit PCM for better compatibility
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=DEVICE_INDEX
            )
            
            frames = []
            silent_frames = 0
            max_silent_frames = int(self.silence_duration * self.sample_rate / self.chunk_size)
            
            self.logger.debug("Recording audio...")
            
            while self.listening:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                
                # Check for silence (convert to float for comparison)
                audio_float = audio_chunk.astype(np.float32) / 32768.0
                if np.max(np.abs(audio_float)) < self.silence_threshold:
                    silent_frames += 1
                else:
                    silent_frames = 0
                
                frames.append(data)
                
                # Stop recording after silence or max duration
                if silent_frames >= max_silent_frames or len(frames) * self.chunk_size / self.sample_rate >= self.record_seconds:
                    break
            
            stream.stop_stream()
            stream.close()
            
            if len(frames) > 0:
                return b''.join(frames)
            
        except Exception as e:
            self.logger.error(f"Error recording audio: {str(e)}")
        
        return None
    
    def _speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """Convert speech to text using Whisper"""
        if not self.whisper_model:
            return None
        
        try:
            # Save audio to temporary file with proper WAV format
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Write WAV header
                import wave
                import struct
                
                # WAV header for 16-bit PCM, 1 channel, sample_rate
                wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
                    b'RIFF',
                    36 + len(audio_data),  # File size
                    b'WAVE',
                    b'fmt ',
                    16,  # fmt chunk size
                    1,   # Audio format (PCM)
                    1,   # Number of channels
                    self.sample_rate,  # Sample rate
                    self.sample_rate * 2,  # Byte rate
                    2,   # Block align
                    16,  # Bits per sample
                    b'data',
                    len(audio_data)  # Data size
                )
                
                temp_file.write(wav_header)
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(temp_file_path)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            return result["text"].strip()
            
        except Exception as e:
            self.logger.error(f"Error in speech-to-text: {str(e)}")
            return None
    
    def process_command(self, text: str) -> str:
        """Process user command and generate response"""
        try:
            text_lower = text.lower().strip()
            
            # 🆕 COMMAND RECOGNITION
            # Vision commands
            if any(word in text_lower for word in ["capture", "take picture", "snap photo", "capture image"]):
                return self.execute_function("capture_image")
            elif any(word in text_lower for word in ["describe", "what do you see", "describe surroundings", "tell me what's around"]):
                return self.execute_function("describe_surroundings")
            elif any(word in text_lower for word in ["navigate", "help me walk", "guide me", "navigate safely"]):
                return self.execute_function("navigate")
            elif any(word in text_lower for word in ["read", "what does it say", "read text", "read that"]):
                return self.execute_function("read_text")
            elif any(word in text_lower for word in ["identify", "what is that", "identify objects"]):
                return self.execute_function("identify_objects")
            
            # Time and date commands
            elif any(word in text_lower for word in ["time", "what time", "current time", "time now"]):
                return self.execute_function("time")
            elif any(word in text_lower for word in ["date", "what day", "what's the date", "today's date"]):
                return self.execute_function("date")
            
            # Fun commands
            elif any(word in text_lower for word in ["joke", "tell me a joke", "make me laugh", "funny joke"]):
                return self.execute_function("joke")
            
            # System commands
            elif any(word in text_lower for word in ["status", "system status", "how are you"]):
                return self.execute_function("status")
            elif any(word in text_lower for word in ["help", "what can you do", "commands"]):
                return self.execute_function("help")
            
            # Audio commands
            elif any(word in text_lower for word in ["volume up", "louder", "increase volume", "turn up"]):
                return self.execute_function("volume_up")
            elif any(word in text_lower for word in ["volume down", "quieter", "decrease volume", "turn down"]):
                return self.execute_function("volume_down")
            elif any(word in text_lower for word in ["mute", "silence"]):
                return self.execute_function("mute")
            elif any(word in text_lower for word in ["unmute", "unmute audio"]):
                return self.execute_function("unmute")
            
            # Emergency commands
            elif any(word in text_lower for word in ["emergency", "urgent", "help me", "sos"]):
                return self.execute_function("emergency")
            
            # Weather commands
            elif any(word in text_lower for word in ["weather", "what's the weather", "weather forecast", "is it raining"]):
                return self.execute_function("weather")
            
            # Distance and obstacle commands
            elif any(word in text_lower for word in ["distance", "how far", "measure distance"]):
                return self.execute_function("distance")
            elif any(word in text_lower for word in ["obstacles", "obstacle", "scan for obstacles"]):
                return self.execute_function("obstacles")
            
            # Fallback to OpenAI for natural conversation
            if self.openai_client:
                response = self._query_openai(text)
                if response:
                    return response
            
            # Default response
            return "I'm sorry, I couldn't process your request. Try saying 'help' for available commands."
            
        except Exception as e:
            self.logger.error(f"Error processing command: {str(e)}")
            return "I encountered an error processing your request."
 
    def _query_openai(self, text: str) -> Optional[str]:
        """Query OpenAI as fallback"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are Inta, an AI assistant for visually impaired users wearing assistive glasses. 
                    You help users understand their surroundings, navigate safely, and provide companionship. 
                    Be helpful, friendly, and concise in your responses."""
                }
            ]
            
            # Add conversation history
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
                # New OpenAI API (1.0.0+)
                response = self.openai_client.chat.completions.create(
                    model=self.config.get('openai', {}).get('model', 'gpt-4o-mini'),
                    messages=messages,
                    max_tokens=self.config.get('openai', {}).get('max_tokens', 150),
                    temperature=self.config.get('openai', {}).get('temperature', 0.7)
                )
                return response.choices[0].message.content.strip()
            else:
                # Old OpenAI API (< 1.0.0)
                response = self.openai_client.ChatCompletion.create(
                    model=self.config.get('openai', {}).get('model', 'gpt-4o-mini'),
                    messages=messages,
                    max_tokens=self.config.get('openai', {}).get('max_tokens', 150),
                    temperature=self.config.get('openai', {}).get('temperature', 0.7)
                )
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error querying OpenAI: {str(e)}")
        
        return None

    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        # Trim history if too long
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
            # Basic vision commands
            if function_name == "capture_image":
                return "I'll capture an image of your surroundings."
            elif function_name == "describe_surroundings":
                return "I'll analyze and describe what's around you."
            elif function_name == "navigate":
                return "I'll help you navigate safely."
            elif function_name == "read_text":
                return "I'll read any text I can see."
            elif function_name == "identify_objects":
                return "I'll identify objects in your environment."
            
            # 🆕 Time and date commands
            elif function_name == "time":
                import time
                return f"The current time is {time.strftime('%H:%M')}."
            elif function_name == "date":
                import time
                return f"Today is {time.strftime('%A, %B %d, %Y')}."
            
            # 🆕 Fun commands
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
            
            # 🆕 System commands
            elif function_name == "status":
                return "I'm running normally. All systems are operational."
            elif function_name == "help":
                return "I can help you with: taking pictures, describing surroundings, navigation, reading text, telling time, jokes, and more. Just ask!"
            
            # 🆕 Audio commands
            elif function_name == "volume_up":
                return "I'll increase the volume."
            elif function_name == "volume_down":
                return "I'll decrease the volume."
            elif function_name == "mute":
                return "I'll mute the audio."
            elif function_name == "unmute":
                return "I'll unmute the audio."
            
            # 🆕 Emergency commands
            elif function_name == "emergency":
                return "EMERGENCY MODE ACTIVATED! I'm here to help. What do you need?"
            elif function_name == "sos":
                return "SOS RECEIVED! Emergency assistance mode activated. I'm here to help you."
            
            # 🆕 Weather placeholder (you can add real API later)
            elif function_name == "weather":
                return "I'll check the weather for your location. (Weather API not yet connected)"
            
            # 🆕 Distance and obstacle detection
            elif function_name == "distance":
                return "I'll measure the distance to nearby objects."
            elif function_name == "obstacles":
                return "I'll scan for obstacles in your path."
            
            else:
                return f"I don't recognize the function '{function_name}'. Try saying 'help' for available commands."
                
        except Exception as e:
            self.logger.error(f"Error executing function {function_name}: {str(e)}")
            return f"Sorry, I couldn't execute {function_name}."
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of INTA AI"""
        return {
            "listening": self.listening,
            "whisper_available": WHISPER_AVAILABLE,
            "audio_available": AUDIO_AVAILABLE,
            "openai_configured": bool(self.openai_client),
            "conversation_length": len(self.conversation_history)
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        
        if self.audio:
            self.audio.terminate()
        
        self.logger.info("INTA AI Manager cleaned up") 