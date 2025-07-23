"""
Voice Command Manager Module
Handles speech recognition using OpenAI Whisper for voice-activated commands in the assistive glasses system
"""

import logging
import threading
import time
import os
import tempfile
import wave
from typing import Callable, Optional, List
from pathlib import Path
import numpy as np

try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("whisper not available - using simulation mode")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logging.warning("pyaudio not available - microphone may not work")

class VoiceCommandManager:
    """Manages voice command recognition using Whisper for the assistive glasses"""
    
    def __init__(self, model_size: str = "base", language: str = "en", 
                 chunk_duration: float = 2.0, silence_threshold: float = 0.01, 
                 silence_duration: float = 1.0):
        self.logger = logging.getLogger(__name__)
        self.model_size = model_size
        self.language = language
        self.chunk_duration = chunk_duration
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        
        # Audio recording settings
        self.sample_rate = 16000  # Whisper works best with 16kHz
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        
        # Voice commands that trigger capture
        self.capture_commands = [
            "capture", "take picture", "analyze", "describe", "look", 
            "see", "what do you see", "take photo", "picture", "camera",
            "show me", "scan", "examine"
        ]
        
        # Voice commands that trigger shutdown
        self.shutdown_commands = [
            "shutdown", "quit", "exit", "stop", "goodbye", "turn off",
            "sleep", "standby", "power off"
        ]
        
        # Callback functions
        self.capture_callback = None
        self.shutdown_callback = None
        self.conversation_callback = None  # For general conversation
        
        # AI Companion integration
        self.companion_mode = False
        self.companion = None
        self.conversation_priority = False  # Prioritize conversation over commands
        
        # Recognition state
        self.listening = False
        self.recognition_thread = None
        self.whisper_model = None
        self.audio_interface = None
        
        # Temporary files
        self.temp_dir = Path(tempfile.gettempdir()) / "glasses_whisper"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize Whisper and audio
        self.initialize_whisper()
        self.initialize_audio()
        
        # For simulation mode
        self.simulation_mode = not (WHISPER_AVAILABLE and PYAUDIO_AVAILABLE and self.whisper_model is not None)
    
    def initialize_whisper(self):
        """Initialize Whisper model"""
        if not WHISPER_AVAILABLE:
            self.logger.warning("Whisper not available - running in simulation mode")
            return
        
        try:
            self.logger.info(f"Loading Whisper model '{self.model_size}'... This may take a moment.")
            self.whisper_model = whisper.load_model(self.model_size)
            
            # Check if CUDA is available for faster processing
            if torch.cuda.is_available():
                self.logger.info("CUDA available - using GPU acceleration")
            else:
                self.logger.info("Using CPU for Whisper processing")
            
            self.logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {str(e)}")
            self.whisper_model = None
    
    def initialize_audio(self):
        """Initialize audio recording interface"""
        if not PYAUDIO_AVAILABLE:
            self.logger.warning("PyAudio not available - running in simulation mode")
            return
        
        try:
            self.audio_interface = pyaudio.PyAudio()
            
            # List available microphones
            self.logger.info("Available audio devices:")
            for i in range(self.audio_interface.get_device_count()):
                info = self.audio_interface.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    self.logger.info(f"  {i}: {info['name']} (inputs: {info['maxInputChannels']})")
            
            self.logger.info("Audio interface initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio interface: {str(e)}")
            self.audio_interface = None
    
    def set_capture_callback(self, callback: Callable):
        """Set the callback function for capture commands"""
        self.capture_callback = callback
        self.logger.info("Capture callback set")
    
    def set_shutdown_callback(self, callback: Callable):
        """Set the callback function for shutdown commands"""
        self.shutdown_callback = callback
        self.logger.info("Shutdown callback set")
    
    def set_conversation_callback(self, callback: Callable):
        """Set the callback function for general conversation"""
        self.conversation_callback = callback
        self.logger.info("Conversation callback set")
    
    def set_companion(self, companion, conversation_priority: bool = True):
        """Set the AI companion for conversational mode"""
        self.companion = companion
        self.companion_mode = True
        self.conversation_priority = conversation_priority
        self.logger.info(f"AI Companion integration enabled (conversation priority: {conversation_priority})")
    
    def add_capture_command(self, command: str):
        """Add a new voice command that triggers capture"""
        command_lower = command.lower().strip()
        if command_lower not in self.capture_commands:
            self.capture_commands.append(command_lower)
            self.logger.info(f"Added capture command: '{command}'")
    
    def add_shutdown_command(self, command: str):
        """Add a new voice command that triggers shutdown"""
        command_lower = command.lower().strip()
        if command_lower not in self.shutdown_commands:
            self.shutdown_commands.append(command_lower)
            self.logger.info(f"Added shutdown command: '{command}'")
    
    def start_listening(self):
        """Start listening for voice commands"""
        if self.listening:
            self.logger.warning("Voice command listening already started")
            return
        
        self.listening = True
        
        if (WHISPER_AVAILABLE and PYAUDIO_AVAILABLE and 
            self.whisper_model is not None and self.audio_interface is not None):
            # Real speech recognition with Whisper
            self.recognition_thread = threading.Thread(target=self._listen_for_commands, daemon=True)
            self.recognition_thread.start()
            self.logger.info("Started Whisper voice command recognition")
        else:
            # Simulation mode
            self.logger.info("Running in simulation mode - voice commands disabled")
    
    def stop_listening(self):
        """Stop listening for voice commands"""
        self.listening = False
        
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=3)
        
        self.logger.info("Voice command listening stopped")
    
    def _listen_for_commands(self):
        """Listen for voice commands using Whisper (runs in separate thread)"""
        self.logger.info("Whisper voice command listener started. Say 'capture' or 'analyze' to take a picture.")
        
        while self.listening:
            try:
                # Record audio chunk
                audio_data = self._record_audio_chunk()
                
                if audio_data is not None and self._has_speech(audio_data):
                    # Save to temporary file
                    temp_file = self._save_audio_to_file(audio_data)
                    
                    if temp_file:
                        # Transcribe with Whisper
                        text = self._transcribe_audio(temp_file)
                        
                        if text:
                            self.logger.info(f"Whisper heard: '{text}'")
                            self._process_command(text)
                        
                        # Clean up temporary file
                        try:
                            temp_file.unlink()
                        except Exception as e:
                            self.logger.warning(f"Failed to delete temp audio file: {e}")
                
                # Brief pause before next recording
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in Whisper voice command listener: {str(e)}")
                time.sleep(1)
    
    def _record_audio_chunk(self) -> Optional[np.ndarray]:
        """Record a chunk of audio from microphone"""
        try:
            # Open audio stream
            stream = self.audio_interface.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            frames_to_record = int(self.sample_rate * self.chunk_duration / self.chunk_size)
            
            for _ in range(frames_to_record):
                if not self.listening:
                    break
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Convert to numpy array
            audio_data = b''.join(frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            return audio_array
            
        except Exception as e:
            self.logger.error(f"Error recording audio: {str(e)}")
            return None
    
    def _has_speech(self, audio_data: np.ndarray) -> bool:
        """Check if audio data contains speech (simple energy-based detection)"""
        if audio_data is None or len(audio_data) == 0:
            return False
        
        # Calculate RMS (Root Mean Square) energy
        rms_energy = np.sqrt(np.mean(audio_data ** 2))
        
        # Check if energy is above threshold
        return rms_energy > self.silence_threshold
    
    def _save_audio_to_file(self, audio_data: np.ndarray) -> Optional[Path]:
        """Save audio data to a temporary WAV file"""
        try:
            # Create temporary file
            temp_file = self.temp_dir / f"voice_command_{int(time.time() * 1000)}.wav"
            
            # Convert float32 to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Save as WAV file
            with wave.open(str(temp_file), 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 2 bytes for int16
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            return temp_file
            
        except Exception as e:
            self.logger.error(f"Error saving audio to file: {str(e)}")
            return None
    
    def _transcribe_audio(self, audio_file: Path) -> Optional[str]:
        """Transcribe audio file using Whisper"""
        try:
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                str(audio_file),
                language=self.language if self.language != "auto" else None,
                fp16=False  # Use fp32 for better Raspberry Pi compatibility
            )
            
            text = result["text"].strip()
            return text if text else None
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio with Whisper: {str(e)}")
            return None
    
    def _process_command(self, text: str):
        """Process transcribed text for commands"""
        text_lower = text.lower().strip()
        
        # If conversation priority is enabled, try conversation first
        if self.conversation_priority and self.companion_mode and self.companion:
            # Only check for explicit shutdown commands when in conversation priority mode
            for command in self.shutdown_commands:
                if command in text_lower:
                    self.logger.info(f"Shutdown command detected: '{text}'")
                    self._handle_shutdown_command()
                    return
            
            # Check for very explicit capture commands (more specific matching)
            explicit_capture_phrases = [
                "take a picture", "capture image", "analyze surroundings", 
                "take photo", "capture now", "scan environment"
            ]
            
            for phrase in explicit_capture_phrases:
                if phrase in text_lower:
                    self.logger.info(f"Explicit capture command detected: '{text}'")
                    self._handle_capture_command()
                    return
            
            # Everything else goes to conversation
            self.logger.info(f"Processing conversation: '{text}'")
            self._handle_conversation(text)
            return
        
        # Original command-first logic (when conversation priority is disabled)
        # Check for capture commands
        for command in self.capture_commands:
            if command in text_lower:
                self.logger.info(f"Capture command detected: '{text}'")
                self._handle_capture_command()
                return
        
        # Check for shutdown commands
        for command in self.shutdown_commands:
            if command in text_lower:
                self.logger.info(f"Shutdown command detected: '{text}'")
                self._handle_shutdown_command()
                return
        
        # If in companion mode and no specific command detected, treat as conversation
        if self.companion_mode and self.companion:
            self.logger.info(f"Processing conversation: '{text}'")
            self._handle_conversation(text)
        elif self.conversation_callback:
            self.logger.info(f"Processing general input: '{text}'")
            self.conversation_callback(text)
        else:
            self.logger.info(f"Unrecognized input: '{text}' - no conversation handler available")
    
    def _handle_capture_command(self):
        """Handle capture voice command"""
        if self.capture_callback:
            try:
                self.capture_callback()
            except Exception as e:
                self.logger.error(f"Error in capture callback: {str(e)}")
        else:
            self.logger.warning("No capture callback set")
    
    def _handle_shutdown_command(self):
        """Handle shutdown voice command"""
        if self.shutdown_callback:
            try:
                self.shutdown_callback()
            except Exception as e:
                self.logger.error(f"Error in shutdown callback: {str(e)}")
        else:
            self.logger.warning("No shutdown callback set")
    
    def _handle_conversation(self, text: str):
        """Handle conversational input with AI companion"""
        if self.companion:
            try:
                response = self.companion.handle_conversation(text)
                self.companion.speak(response)
            except Exception as e:
                self.logger.error(f"Error in companion conversation: {str(e)}")
        elif self.conversation_callback:
            try:
                self.conversation_callback(text)
            except Exception as e:
                self.logger.error(f"Error in conversation callback: {str(e)}")
        else:
            self.logger.warning("No conversation handler available")
    
    def test_microphone(self) -> bool:
        """Test if microphone is working"""
        if not WHISPER_AVAILABLE or not PYAUDIO_AVAILABLE or not self.whisper_model:
            self.logger.warning("Cannot test microphone - required libraries not available")
            return False
        
        try:
            self.logger.info("Testing microphone with Whisper... Say something!")
            
            # Record a test chunk
            audio_data = self._record_audio_chunk()
            
            if audio_data is None:
                self.logger.error("Failed to record audio")
                return False
            
            if not self._has_speech(audio_data):
                self.logger.warning("No speech detected in audio")
                return False
            
            # Save and transcribe
            temp_file = self._save_audio_to_file(audio_data)
            if temp_file:
                text = self._transcribe_audio(temp_file)
                
                # Clean up
                try:
                    temp_file.unlink()
                except:
                    pass
                
                if text:
                    self.logger.info(f"Microphone test successful! Whisper heard: '{text}'")
                    return True
                else:
                    self.logger.warning("Whisper could not transcribe audio")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Microphone test failed: {str(e)}")
            return False
    
    def get_voice_status(self) -> dict:
        """Get current voice command status"""
        return {
            "listening": self.listening,
            "whisper_available": WHISPER_AVAILABLE,
            "pyaudio_available": PYAUDIO_AVAILABLE,
            "simulation_mode": self.simulation_mode,
            "model_size": self.model_size,
            "language": self.language,
            "sample_rate": self.sample_rate,
            "capture_commands": self.capture_commands,
            "shutdown_commands": self.shutdown_commands,
            "model_loaded": self.whisper_model is not None,
            "audio_initialized": self.audio_interface is not None
        }
    
    def simulate_capture_command(self):
        """Simulate a capture voice command (for testing)"""
        self.logger.info("Simulating capture voice command")
        self._handle_capture_command()
    
    def simulate_shutdown_command(self):
        """Simulate a shutdown voice command (for testing)"""
        self.logger.info("Simulating shutdown voice command")
        self._handle_shutdown_command()
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        try:
            if self.temp_dir.exists():
                for file in self.temp_dir.glob("*.wav"):
                    try:
                        file.unlink()
                    except Exception as e:
                        self.logger.warning(f"Failed to delete temp file {file}: {e}")
                self.logger.info("Temporary audio files cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {str(e)}")
    
    def cleanup(self):
        """Clean up voice command resources"""
        self.logger.info("Cleaning up voice command manager...")
        
        # Stop listening
        self.stop_listening()
        
        # Clean up audio interface
        if self.audio_interface:
            try:
                self.audio_interface.terminate()
            except Exception as e:
                self.logger.error(f"Error terminating audio interface: {str(e)}")
        
        # Clean up temporary files
        self.cleanup_temp_files()
        
        self.logger.info("Voice command manager cleanup complete")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Test function for voice commands
def test_voice_commands():
    """Test function for Whisper voice command manager"""
    logging.basicConfig(level=logging.INFO)
    
    def on_capture():
        print("🎯 Capture command received!")
    
    def on_shutdown():
        print("🛑 Shutdown command received!")
    
    voice_manager = VoiceCommandManager(model_size="base")
    voice_manager.set_capture_callback(on_capture)
    voice_manager.set_shutdown_callback(on_shutdown)
    
    print("Whisper Voice Command Test")
    status = voice_manager.get_voice_status()
    print("Status:", status)
    
    # Test microphone
    if not voice_manager.simulation_mode:
        print("\n--- Microphone Test ---")
        if voice_manager.test_microphone():
            print("✓ Microphone test passed")
        else:
            print("✗ Microphone test failed")
    
    voice_manager.start_listening()
    
    try:
        if voice_manager.simulation_mode:
            print("Running in simulation mode. Testing voice commands...")
            time.sleep(2)
            voice_manager.simulate_capture_command()
            time.sleep(1)
            voice_manager.simulate_shutdown_command()
        else:
            print("Listening for voice commands with Whisper...")
            print("Available capture commands:", voice_manager.capture_commands)
            print("Available shutdown commands:", voice_manager.shutdown_commands)
            print("Speak now! (30 seconds)")
            time.sleep(30)  # Listen for 30 seconds
            
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        voice_manager.cleanup()

if __name__ == "__main__":
    test_voice_commands() 