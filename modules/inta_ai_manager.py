"""
INTA AI Manager Module
Handles AI assistant functionality with low-latency voice recognition
Optimized for Raspberry Pi with ALSA direct access
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

# ALSA imports for direct hardware access
try:
    import alsaaudio
    import audioop
    ALSA_AVAILABLE = True
except ImportError:
    ALSA_AVAILABLE = False
    logging.warning("ALSA not available - falling back to PyAudio")

# Fallback to PyAudio if ALSA not available
if not ALSA_AVAILABLE:
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
    """Low-latency AI assistant optimized for Raspberry Pi with ALSA direct access"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.running = False
        self.listening = False
        
        # Audio settings optimized for Raspberry Pi
        self.sample_rate = config.get('inta', {}).get('sample_rate', 8000)  # Lower for Pi
        self.chunk_size = config.get('inta', {}).get('chunk_size', 512)     # Smaller chunks
        self.channels = 1
        self.format = alsaaudio.PCM_FORMAT_S16_LE  # 16-bit little-endian
        
        # Voice Activity Detection settings
        self.vad_aggressiveness = config.get('inta', {}).get('vad_aggressiveness', 2)
        self.speech_frames_threshold = config.get('inta', {}).get('speech_frames_threshold', 3)
        self.silence_frames_threshold = config.get('inta', {}).get('silence_frames_threshold', 10)
        
        # Real-time processing settings
        self.realtime_buffer_size = config.get('inta', {}).get('realtime_buffer_size', 4096)
        self.max_audio_length = config.get('inta', {}).get('max_audio_length', 10.0)  # seconds
        
        # Audio hardware
        self.alsa_device = None
        self.audio_stream = None
        self.vad = None
        
        # Whisper model
        self.whisper_model = None
        self.whisper_model_size = config.get('inta', {}).get('whisper_model', 'tiny')  # Use tiny for Pi
        
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
        
        # Threading and queues
        self.listen_thread = None
        self.audio_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        # Callbacks
        self._emit_response = None
        self.speech_callback = None
        
        # Initialize components
        self._initialize_audio()
        self._initialize_vad()
        self._initialize_whisper()
        
        self.logger.info("INTA AI Manager initialized with ALSA optimization")
    
    def _initialize_audio(self):
        """Initialize ALSA audio for low-latency recording"""
        if not ALSA_AVAILABLE:
            self.logger.error("ALSA not available - audio recording disabled")
            return False
        
        try:
            # Open ALSA device for capture
            self.alsa_device = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK)
            
            # Set hardware parameters optimized for Raspberry Pi
            self.alsa_device.setchannels(self.channels)
            self.alsa_device.setrate(self.sample_rate)
            self.alsa_device.setformat(self.format)
            self.alsa_device.setperiodsize(self.chunk_size)
            
            # Get actual parameters (hardware might adjust them)
            actual_channels = self.alsa_device.channels()
            actual_rate = self.alsa_device.rate()
            actual_format = self.alsa_device.format()
            actual_period_size = self.alsa_device.periodsize()
            
            self.logger.info(f"ALSA initialized: {actual_channels}ch, {actual_rate}Hz, "
                           f"format={actual_format}, period_size={actual_period_size}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ALSA: {str(e)}")
            return False
    
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
        """Initialize Whisper model optimized for Raspberry Pi"""
        if not WHISPER_AVAILABLE:
            self.logger.error("Whisper not available - speech recognition disabled")
            return
        
        try:
            # Use tiny model for Raspberry Pi performance
            self.logger.info(f"Loading Whisper model: {self.whisper_model_size}")
            self.whisper_model = whisper.load_model(self.whisper_model_size)
            self.logger.info("Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {str(e)}")
    
    def start_listening(self) -> bool:
        """Start continuous low-latency listening"""
        if not self.alsa_device:
            self.logger.error("Audio device not initialized")
            return False
        
        if self.listening:
            self.logger.warning("Already listening")
            return True
        
        self.listening = True
        self.running = True
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._continuous_listen_loop, daemon=True)
        self.listen_thread.start()
        
        self.logger.info("Started continuous low-latency listening")
        return True
    
    def stop_listening(self):
        """Stop listening"""
        self.listening = False
        self.running = False
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)
        
        self.logger.info("Stopped listening")
    
    def _continuous_listen_loop(self):
        """Continuous low-latency listening loop optimized for Raspberry Pi"""
        self.logger.info("Starting continuous listen loop")
        
        audio_buffer = []
        speech_frames = 0
        silence_frames = 0
        is_speaking = False
        
        while self.listening:
            try:
                # Read audio data from ALSA
                length, data = self.alsa_device.read()
                
                if length > 0:
                    # Convert to numpy array for processing
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    audio_buffer.append(audio_chunk)
                    
                    # Check for voice activity
                    if self._is_speech(audio_chunk):
                        speech_frames += 1
                        silence_frames = 0
                        
                        if not is_speaking:
                            is_speaking = True
                            self.logger.debug("Speech detected")
                    else:
                        silence_frames += 1
                        speech_frames = 0
                    
                    # Process speech when detected
                    if is_speaking and speech_frames >= self.speech_frames_threshold:
                        # Continue collecting audio while speaking
                        if len(audio_buffer) * self.chunk_size / self.sample_rate >= self.max_audio_length:
                            # Process the collected audio
                            self._process_audio_buffer(audio_buffer)
                            audio_buffer = []
                            is_speaking = False
                            speech_frames = 0
                            silence_frames = 0
                    
                    # End speech when silence detected
                    elif is_speaking and silence_frames >= self.silence_frames_threshold:
                        if len(audio_buffer) > 0:
                            # Process the collected audio
                            self._process_audio_buffer(audio_buffer)
                            audio_buffer = []
                        is_speaking = False
                        speech_frames = 0
                        silence_frames = 0
                
                # Small delay to prevent CPU overload
                time.sleep(0.001)  # 1ms delay
                
            except Exception as e:
                self.logger.error(f"Error in continuous listen loop: {str(e)}")
                time.sleep(0.1)  # Longer delay on error
        
        self.logger.info("Continuous listen loop ended")
    
    def _is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Detect if audio chunk contains speech"""
        if self.vad and VAD_AVAILABLE:
            # Use WebRTC VAD for accurate speech detection
            try:
                return self.vad.is_speech(audio_chunk.tobytes(), self.sample_rate)
            except Exception as e:
                self.logger.debug(f"VAD error, falling back to amplitude detection: {str(e)}")
        
        # Fallback to simple amplitude detection
        audio_float = audio_chunk.astype(np.float32) / 32768.0
        amplitude = np.max(np.abs(audio_float))
        return amplitude > 0.01  # Simple threshold
    
    def _process_audio_buffer(self, audio_buffer: list):
        """Process collected audio buffer for speech recognition"""
        if not audio_buffer:
            return
        
        try:
            # Combine all audio chunks
            combined_audio = np.concatenate(audio_buffer)
            
            # Convert to bytes
            audio_data = combined_audio.tobytes()
            
            # Process in separate thread to avoid blocking
            threading.Thread(target=self._process_audio_async, args=(audio_data,), daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error processing audio buffer: {str(e)}")
    
    def _process_audio_async(self, audio_data: bytes):
        """Process audio data asynchronously"""
        try:
            # Convert speech to text
            text = self._speech_to_text(audio_data)
            
            if text and text.strip():
                self.logger.info(f"Recognized: {text}")
                
                # Process command
                response = self.process_command(text)
                
                # Emit response
                if self._emit_response:
                    self._emit_response(response)
                
                # Speak response if callback available
                if self.speech_callback:
                    self.speech_callback(response)
            
        except Exception as e:
            self.logger.error(f"Error in async audio processing: {str(e)}")
    
    def _speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """Convert speech to text using Whisper with ALSA optimization"""
        if not self.whisper_model:
            return None
        
        try:
            # Save audio to temporary file with proper WAV format
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Write WAV header for ALSA format
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
            
            # Add to conversation history
            self._add_to_history("user", text)
            
            # Query OpenAI
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
        """Query OpenAI as fallback"""
        if not self.openai_client:
            return None
        
        try:
            # Prepare conversation context
            messages = [
                {
                    "role": "system",
                    "content": """You are INTA, an intelligent AI assistant for visually impaired users. 
                    You help users navigate their environment, understand their surroundings, and execute commands.
                    Be helpful, concise, and accessible. If the user asks to execute a function, respond with the function name."""
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
    
    def _get_conversation_context(self) -> str:
        """Get conversation context for OpenAI"""
        if not self.conversation_history:
            return "This is the start of a conversation with INTA, an AI assistant for visually impaired users."
        
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
        
        # Trim history if too long
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def _emit_response(self, response: str):
        """Emit response event for other components to handle"""
        # This can be extended to emit events to other parts of the system
        self.logger.info(f"INTA Response: {response}")
    
    def set_speech_callback(self, speech_callback: Callable[[str], None]):
        """Set callback for speech output"""
        self.speech_callback = speech_callback
    
    def execute_function(self, function_name: str, params: Dict[str, Any] = None) -> str:
        """Execute specific functions based on commands"""
        try:
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
            else:
                return f"I don't recognize the function '{function_name}'."
                
        except Exception as e:
            self.logger.error(f"Error executing function {function_name}: {str(e)}")
            return f"Sorry, I couldn't execute {function_name}."
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of INTA AI"""
        return {
            "listening": self.listening,
            "whisper_available": WHISPER_AVAILABLE,
            "audio_available": ALSA_AVAILABLE,
            "vad_available": VAD_AVAILABLE,
            "openai_configured": bool(self.openai_client),
            "conversation_length": len(self.conversation_history),
            "sample_rate": self.sample_rate,
            "chunk_size": self.chunk_size
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()
        
        if self.alsa_device:
            self.alsa_device.close()
        
        self.logger.info("INTA AI Manager cleaned up") 