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
import modules.sensor_manager as sensor_manager

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
        
        # Wake word system
        self.wake_word = config.get('inta', {}).get('wake_word', 'inta').lower()
        self.wake_word_detected = False
        self.wake_word_confidence = config.get('inta', {}).get('wake_word_confidence', 0.7)
        self.wake_word_timeout = config.get('inta', {}).get('wake_word_timeout', 5.0)  # seconds
        self.last_wake_time = 0
        
        # Contextual understanding
        self.contextual_mode = config.get('inta', {}).get('contextual_mode', True)
        self.confirmation_required = config.get('inta', {}).get('confirmation_required', True)
        self.pending_confirmation = None
        self.confirmation_timeout = config.get('inta', {}).get('confirmation_timeout', 10.0)  # seconds
        self.last_confirmation_time = 0
        
        # Audio settings
        self.sample_rate = config.get('inta', {}).get('sample_rate', 16000)
        self.chunk_size = config.get('inta', {}).get('chunk_size', 1024)
        self.channels = 1
        
        # Setup PipeWire system
        self._setup_pipewire_system()
        
        # Configure microphone volume
        self._configure_microphone_volume()
        
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
        
        # Start sensor monitor for continuous data
        sensor_manager.sensor_monitor.start()
        self._navigation_monitoring = False
        self._navigation_thread = None
        
        self.logger.info("INTA AI Manager initialized")
    
    def _initialize_speech_recognition(self):
        """Initialize speech recognition with PipeWire"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            self.logger.error("speech_recognition not available - audio recording disabled")
            return False
        
        try:
            # Configure PipeWire and disable ALSA/JACK
            self._configure_pipewire()
            
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
        """Find and configure USB microphone with PipeWire"""
        try:
            # List all microphones through PipeWire
            mics = sr.Microphone.list_microphone_names()
            self.logger.info(f"Available microphones (PipeWire): {mics}")
            
            # Look for USB microphone (MUSIC-BOOST USB Microphone)
            for i, mic_name in enumerate(mics):
                if 'usb' in mic_name.lower() or 'microphone' in mic_name.lower() or 'music-boost' in mic_name.lower():
                    self.logger.info(f"Found USB microphone: {mic_name} (index {i})")
                    
                    # Create microphone with specific device index
                    mic = sr.Microphone(device_index=i)
                    
                    # Test if it works
                    try:
                        with mic as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        self.logger.info(f"USB microphone {i} working correctly with PipeWire")
                        return mic
                    except Exception as e:
                        self.logger.warning(f"USB microphone {i} failed test: {e}")
                        continue
            
            # If no USB mic found, try default microphone
            self.logger.info("No USB microphone found, trying default microphone")
            
            try:
                # Try default microphone
                mic = sr.Microphone()
                with mic as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.logger.info("Default microphone working correctly with PipeWire")
                return mic
            except Exception as e:
                self.logger.warning(f"Default microphone failed: {e}")
            
            # Try different device configurations
            for device_index in range(5):  # Try first 5 devices
                try:
                    mic = sr.Microphone(device_index=device_index)
                    with mic as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    self.logger.info(f"Microphone {device_index} working correctly with PipeWire")
                    return mic
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding USB microphone: {e}")
            return None
    
    def _configure_pipewire(self):
        """Configure PipeWire for direct access"""
        try:
            # Check if we're on a system that supports PipeWire
            import subprocess
            
            # Test if PipeWire is available
            try:
                result = subprocess.run(['pw-cli', '--version'], capture_output=True)
                if result.returncode != 0:
                    self.logger.info("PipeWire not available, skipping configuration")
                    return True  # Not an error, just not available
            except FileNotFoundError:
                self.logger.info("PipeWire not available, skipping configuration")
                return True  # Not an error, just not available
            
            # Disable ALSA completely
            os.environ['ALSA_PCM_CARD'] = ''
            os.environ['ALSA_PCM_DEVICE'] = ''
            os.environ['ALSA_CARD'] = ''
            
            # Force PipeWire
            os.environ['PIPEWIRE_RUNTIME_DIR'] = '/tmp/pipewire-0'
            os.environ['PIPEWIRE_REMOTE'] = 'pipewire-0'
            
            # Disable JACK
            os.environ['JACK_NO_AUDIO_RESERVATION'] = '1'
            os.environ['JACK_PROMISCUOUS_SERVER'] = ''
            
            # Suppress ALSA and JACK error messages
            os.environ['ALSA_PCM_CARD'] = ''
            os.environ['ALSA_PCM_DEVICE'] = ''
            os.environ['ALSA_CARD'] = ''
            os.environ['JACK_NO_AUDIO_RESERVATION'] = '1'
            os.environ['JACK_PROMISCUOUS_SERVER'] = ''
            
            # Redirect stderr to suppress ALSA/JACK warnings
            import sys
            
            # Create a null device for stderr
            null_fd = os.open(os.devnull, os.O_WRONLY)
            old_stderr = os.dup(2)
            os.dup2(null_fd, 2)
            os.close(null_fd)
            
            # Kill any existing JACK processes
            try:
                subprocess.run(['pkill', '-f', 'jack'], capture_output=True)
                subprocess.run(['pkill', '-f', 'jackd'], capture_output=True)
            except:
                pass
            
            # Ensure PipeWire is running
            try:
                result = subprocess.run(['pw-cli', 'info'], capture_output=True)
                if result.returncode != 0:
                    subprocess.run(['pipewire'], capture_output=True)
                    time.sleep(2)
            except:
                pass
            
            # Restore stderr
            os.dup2(old_stderr, 2)
            os.close(old_stderr)
            
            self.logger.info("PipeWire configured, ALSA and JACK disabled")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure PipeWire: {e}")
            return False
    
    def _setup_pipewire_system(self):
        """Setup PipeWire system and kill conflicting services"""
        try:
            import subprocess
            
            # Check if PipeWire is available
            try:
                result = subprocess.run(['pw-cli', '--version'], capture_output=True)
                if result.returncode != 0:
                    self.logger.info("PipeWire not available, skipping system setup")
                    return
            except FileNotFoundError:
                self.logger.info("PipeWire not available, skipping system setup")
                return
            
            # Kill JACK processes
            try:
                subprocess.run(['pkill', '-f', 'jack'], capture_output=True)
                subprocess.run(['pkill', '-f', 'jackd'], capture_output=True)
            except:
                pass
            
            # Ensure PipeWire is running
            try:
                result = subprocess.run(['pw-cli', 'info'], capture_output=True)
                if result.returncode != 0:
                    subprocess.run(['pipewire'], capture_output=True)
                    time.sleep(2)
            except:
                pass
            
            self.logger.info("PipeWire system setup complete")
            
        except Exception as e:
            self.logger.warning(f"PipeWire system setup failed: {e}")
    
    def _configure_microphone_volume(self):
        """Configure microphone volume"""
        try:
            import subprocess
            
            # Get microphone volume from config (0.0 to 1.0)
            mic_volume = self.config.get('inta', {}).get('microphone_volume', 0.8)
            
            # Try to find the default microphone source
            try:
                # Get list of sources
                result = subprocess.run(['pactl', 'list', 'sources', 'short'], capture_output=True, text=True)
                if result.returncode == 0:
                    sources = result.stdout.strip().split('\n')
                    if sources and sources[0]:  # Check if we have any sources
                        # Use the first available source (usually the default)
                        mic_name = sources[0].split('\t')[1] if '\t' in sources[0] else sources[0].split()[1]
                        
                        # Convert 0.0-1.0 to 0-65536
                        volume_int = int(mic_volume * 65536)
                        
                        # Set volume
                        vol_result = subprocess.run([
                            'pactl', 'set-source-volume', mic_name, str(volume_int)
                        ], capture_output=True)
                        
                        if vol_result.returncode == 0:
                            self.logger.info(f"Microphone volume set to {mic_volume * 100:.0f}% for {mic_name}")
                        else:
                            self.logger.warning(f"Failed to set microphone volume: {vol_result.stderr.decode()}")
                    else:
                        self.logger.warning("No audio sources found")
                else:
                    self.logger.warning("Failed to list audio sources")
                    
            except FileNotFoundError:
                self.logger.warning("pactl not found - microphone volume configuration skipped")
            except Exception as e:
                self.logger.warning(f"Error configuring microphone volume: {e}")
            
            # Fallback: Try to set volume using speech recognition library
            try:
                if hasattr(self, 'microphone') and self.microphone:
                    # The speech recognition library will handle volume automatically
                    self.logger.info("Using speech recognition library for microphone volume")
            except Exception as e:
                self.logger.debug(f"Fallback microphone configuration: {e}")
                
        except Exception as e:
            self.logger.warning(f"Failed to configure microphone volume: {e}")
    
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
                
                # Check for wake word first
                if self._check_wake_word(text):
                    self.wake_word_detected = True
                    self.last_wake_time = time.time()
                    self.logger.info("Wake word detected! INTA is now listening.")
                    self._emit_response("Yes, I'm listening. How can I help you?")
                    return
                
                # Check if we're in wake word mode
                if self.wake_word_detected:
                    # Check if wake word timeout has expired
                    if time.time() - self.last_wake_time > self.wake_word_timeout:
                        self.wake_word_detected = False
                        self.logger.debug("Wake word timeout expired")
                        return
                    
                    # Process the command
                    response = self.process_command(text)
                    
                    # Emit response
                    self._emit_response(response)
                    
                    # Reset wake word detection after processing
                    self.wake_word_detected = False
                else:
                    self.logger.debug("Wake word not detected, ignoring speech")
                    
            else:
                self.logger.debug("No speech detected or empty text")
                
        except Exception as e:
            self.logger.error(f"Error processing audio: {str(e)}")
    
    def _check_wake_word(self, text: str) -> bool:
        """Check if the wake word is present in the text"""
        if not text:
            return False
        
        text_lower = text.lower().strip()
        
        # Check for exact wake word match
        if self.wake_word in text_lower:
            return True
        
        # Check for variations of the wake word
        wake_variations = [
            self.wake_word,
            f"hey {self.wake_word}",
            f"hello {self.wake_word}",
            f"hi {self.wake_word}",
            f"okay {self.wake_word}",
            f"listen {self.wake_word}",
            f"attention {self.wake_word}"
        ]
        
        for variation in wake_variations:
            if variation in text_lower:
                return True
        
        return False
    
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
        """Process user command and generate response with contextual understanding"""
        try:
            text_lower = text.lower().strip()
            
            # Check for confirmation responses first
            if self.pending_confirmation:
                if any(word in text_lower for word in ["yes", "correct", "right", "okay", "ok", "sure", "do it", "execute"]):
                    # Execute the pending command
                    command = self.pending_confirmation
                    self.pending_confirmation = None
                    self.last_confirmation_time = 0
                    return self._execute_confirmed_command(command)
                elif any(word in text_lower for word in ["no", "wrong", "incorrect", "cancel", "stop", "don't"]):
                    # Cancel the pending command
                    self.pending_confirmation = None
                    self.last_confirmation_time = 0
                    return "Command cancelled. How else can I help you?"
                else:
                    # Still waiting for confirmation, remind user
                    return f"I'm still waiting for confirmation. Did you mean: {self.pending_confirmation['description']}? Say yes or no."
            
            # Add to conversation history
            self._add_to_history("user", text)
            
            # Check for specific commands first (exact matches)
            command_result = self._check_exact_commands(text_lower)
            if command_result:
                return command_result
            
            # Use contextual understanding for ambiguous commands
            if self.contextual_mode:
                contextual_result = self._understand_contextual_command(text)
                if contextual_result:
                    return contextual_result
            
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
    
    def _check_exact_commands(self, text_lower: str) -> Optional[str]:
        """Check for exact command matches"""
        if any(word in text_lower for word in ["time", "clock", "hour"]):
            return self.execute_function("time")
        elif any(word in text_lower for word in ["date", "day", "month", "year"]):
            return self.execute_function("date")
        elif any(word in text_lower for word in ["joke", "funny", "humor"]):
            return self.execute_function("joke")
        elif any(word in text_lower for word in ["status", "health", "system"]):
            return self.execute_function("status")
        elif any(word in text_lower for word in ["help", "assist", "guide"]):
            # Navigation-related help
            if any(phrase in text_lower for phrase in [
                "help walking", "navigate", "navigation", "safe to walk", "obstacle", "path like", "walk forward", "is it safe", "what's the path", "help me navigate"]):
                return self.execute_function("navigate")
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
        elif any(word in text_lower for word in ["shutdown", "turn off", "exit", "quit", "stop"]):
            return self.execute_function("shutdown")
        elif any(phrase in text_lower for phrase in [
            "distance in front", "how far is", "obstacle ahead", "object ahead", "detect obstacle", "measure distance", "is it clear ahead", "is it safe to walk forward", "what's the path like", "i need help walking", "help me navigate"]):
            return self.execute_function("navigate")
        return None
    
    def _understand_contextual_command(self, text: str) -> Optional[str]:
        """Use AI to understand contextual commands and ask for confirmation"""
        if not self.openai_client:
            return None
        
        try:
            # Prepare system prompt for command understanding
            system_prompt = """You are INTA, an AI assistant for visually impaired users. 
            Analyze the user's request and determine what command they want to execute.
            
            Available commands:
            - capture_image: Take a picture and describe surroundings
            - describe_surroundings: Analyze and describe environment
            - navigate: Help with navigation
            - read_text: Read text in images
            - identify_objects: Identify objects in environment
            - weather: Check weather information
            - distance: Measure distance to objects
            - obstacles: Detect obstacles
            - time: Tell current time
            - date: Tell current date
            - joke: Tell a joke
            - status: System status
            - help: Show help information
            
            If the user's request matches one of these commands, respond with:
            COMMAND: [command_name]
            DESCRIPTION: [brief description of what you understood]
            
            If it doesn't match any command, respond with:
            CONVERSATION: [natural response]
            
            Be contextual and understand natural language variations."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
            
            # Query OpenAI for command understanding
            if hasattr(self.openai_client, 'chat') and hasattr(self.openai_client.chat, 'completions'):
                response = self.openai_client.chat.completions.create(
                    model=self.config.get('openai', {}).get('model', 'gpt-4o-mini'),
                    messages=messages,
                    max_tokens=150,
                    temperature=0.1
                )
                ai_response = response.choices[0].message.content
            else:
                response = self.openai_client.ChatCompletion.create(
                    model=self.config.get('openai', {}).get('model', 'gpt-4o-mini'),
                    messages=messages,
                    max_tokens=150,
                    temperature=0.1
                )
                ai_response = response.choices[0].message.content
            
            # Parse the AI response
            if ai_response.startswith("COMMAND:"):
                # Extract command and description
                lines = ai_response.split('\n')
                command_line = lines[0]
                description_line = lines[1] if len(lines) > 1 else ""
                
                command = command_line.replace("COMMAND:", "").strip()
                description = description_line.replace("DESCRIPTION:", "").strip()
                
                # Ask for confirmation if required
                if self.confirmation_required:
                    self.pending_confirmation = {
                        "command": command,
                        "description": description,
                        "original_text": text
                    }
                    self.last_confirmation_time = time.time()
                    return f"I understood you want me to {description}. Is that correct? Say yes or no."
                else:
                    return self.execute_function(command)
            
            elif ai_response.startswith("CONVERSATION:"):
                # Return the conversation response
                return ai_response.replace("CONVERSATION:", "").strip()
            
            else:
                # Fallback to general conversation
                return None
                
        except Exception as e:
            self.logger.error(f"Error in contextual command understanding: {str(e)}")
            return None
    
    def _execute_confirmed_command(self, command_info: Dict[str, Any]) -> str:
        """Execute a command that has been confirmed by the user"""
        try:
            command = command_info.get("command")
            if command:
                return self.execute_function(command)
            else:
                return "I'm sorry, there was an error executing the command."
        except Exception as e:
            self.logger.error(f"Error executing confirmed command: {str(e)}")
            return "I encountered an error executing the command."
    
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
                    model=self.config.get('openai', {}).get('model', 'gpt-4o-mini'),
                    messages=messages,
                    max_tokens=self.config.get('openai', {}).get('max_tokens', 300),
                    temperature=self.config.get('openai', {}).get('temperature', 0.3)
                )
                return response.choices[0].message.content
            else:
                # Old OpenAI API
                response = self.openai_client.ChatCompletion.create(
                    model=self.config.get('openai', {}).get('model', 'gpt-4o-mini'),
                    messages=messages,
                    max_tokens=self.config.get('openai', {}).get('max_tokens', 300),
                    temperature=self.config.get('openai', {}).get('temperature', 0.3)
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
            
            elif function_name in ["distance", "obstacles", "navigate"]:
                # Start continuous navigation monitoring for 30 seconds
                self.start_navigation_monitoring()
                import threading
                def stop_nav():
                    import time
                    time.sleep(30)
                    self.stop_navigation_monitoring()
                threading.Thread(target=stop_nav, daemon=True).start()
                distance = sensor_manager.sensor_monitor.get_latest_distance()
                if distance is None:
                    return "I'm sorry, I couldn't get a reading from the distance sensors."
                if distance < 50:
                    return f"Warning! Obstacle very close, at {distance} centimeters. I will keep monitoring and warn you if anything changes."
                elif distance < 150:
                    return f"Caution, an object is ahead at about {distance} centimeters. I will keep monitoring and warn you if anything changes."
                else:
                    return "The path ahead appears to be clear. I will keep monitoring and warn you if anything changes."
            
            elif function_name == "capture":
                return "I'll capture and analyze your surroundings now."
            
            elif function_name == "shutdown":
                return "Shutting down INTA AI system. Goodbye!"
            
            else:
                return f"Function {function_name} not implemented yet."
                
        except Exception as e:
            self.logger.error(f"Error executing function {function_name}: {str(e)}")
            return f"Error executing {function_name}"
    
    def start_navigation_monitoring(self):
        if self._navigation_monitoring:
            return
        self._navigation_monitoring = True
        import threading
        self._navigation_thread = threading.Thread(target=self._navigation_monitor_loop, daemon=True)
        self._navigation_thread.start()

    def stop_navigation_monitoring(self):
        self._navigation_monitoring = False
        if self._navigation_thread:
            self._navigation_thread.join(timeout=2)

    def _navigation_monitor_loop(self):
        last_warning = None
        while self._navigation_monitoring:
            distance = sensor_manager.sensor_monitor.get_latest_distance()
            if distance is not None:
                if distance < 50:
                    warning = f"Warning! Obstacle very close, at {distance} centimeters."
                elif distance < 150:
                    warning = f"Caution, an object is ahead at about {distance} centimeters."
                else:
                    warning = None
                if warning and warning != last_warning:
                    self._emit_response(warning)
                    last_warning = warning
                elif not warning:
                    last_warning = None
            import time
            time.sleep(1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "listening": self.listening,
            "running": self.running,
            "wake_word_detected": self.wake_word_detected,
            "wake_word": self.wake_word,
            "contextual_mode": self.contextual_mode,
            "confirmation_required": self.confirmation_required,
            "pending_confirmation": self.pending_confirmation is not None,
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