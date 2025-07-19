"""
Voice Command Manager Module
Handles speech recognition for voice-activated commands in the assistive glasses system
"""

import logging
import threading
import time
from typing import Callable, Optional, List

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logging.warning("speech_recognition not available - using simulation mode")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logging.warning("pyaudio not available - microphone may not work")

class VoiceCommandManager:
    """Manages voice command recognition for the assistive glasses"""
    
    def __init__(self, language: str = "en-US", timeout: float = 1.0, phrase_timeout: float = 0.3):
        self.logger = logging.getLogger(__name__)
        self.language = language
        self.timeout = timeout
        self.phrase_timeout = phrase_timeout
        
        # Voice commands that trigger capture
        self.capture_commands = [
            "capture", "take picture", "analyze", "describe", "look", 
            "see", "what do you see", "take photo", "picture", "camera"
        ]
        
        # Voice commands that trigger shutdown
        self.shutdown_commands = [
            "shutdown", "quit", "exit", "stop", "goodbye", "turn off"
        ]
        
        # Callback functions
        self.capture_callback = None
        self.shutdown_callback = None
        
        # Recognition state
        self.listening = False
        self.recognition_thread = None
        self.recognizer = None
        self.microphone = None
        
        # Initialize speech recognition
        self.initialize_speech_recognition()
        
        # For simulation mode
        self.simulation_mode = not (SPEECH_RECOGNITION_AVAILABLE and PYAUDIO_AVAILABLE)
    
    def initialize_speech_recognition(self):
        """Initialize speech recognition components"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            self.logger.warning("Speech recognition not available - running in simulation mode")
            return
        
        if not PYAUDIO_AVAILABLE:
            self.logger.warning("PyAudio not available - microphone may not work")
            return
        
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            
            # Set recognition parameters
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            
            self.logger.info("Speech recognition initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize speech recognition: {str(e)}")
            self.simulation_mode = True
    
    def set_capture_callback(self, callback: Callable):
        """Set the callback function for capture commands"""
        self.capture_callback = callback
        self.logger.info("Capture callback set")
    
    def set_shutdown_callback(self, callback: Callable):
        """Set the callback function for shutdown commands"""
        self.shutdown_callback = callback
        self.logger.info("Shutdown callback set")
    
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
        
        if SPEECH_RECOGNITION_AVAILABLE and PYAUDIO_AVAILABLE and not self.simulation_mode:
            # Real speech recognition
            self.recognition_thread = threading.Thread(target=self._listen_for_commands, daemon=True)
            self.recognition_thread.start()
            self.logger.info("Started voice command recognition")
        else:
            # Simulation mode
            self.logger.info("Running in simulation mode - voice commands disabled")
    
    def stop_listening(self):
        """Stop listening for voice commands"""
        self.listening = False
        
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=2)
        
        self.logger.info("Voice command listening stopped")
    
    def _listen_for_commands(self):
        """Listen for voice commands (runs in separate thread)"""
        self.logger.info("Voice command listener started. Say 'capture' or 'analyze' to take a picture.")
        
        while self.listening:
            try:
                # Listen for audio
                with self.microphone as source:
                    # Listen for audio with timeout
                    audio = self.recognizer.listen(source, timeout=self.timeout, phrase_time_limit=5)
                
                # Recognize speech
                try:
                    # Use Google Speech Recognition (requires internet)
                    text = self.recognizer.recognize_google(audio, language=self.language).lower()
                    self.logger.info(f"Heard: '{text}'")
                    
                    # Check for commands
                    self._process_command(text)
                    
                except sr.UnknownValueError:
                    # Speech was unintelligible
                    pass
                except sr.RequestError as e:
                    self.logger.error(f"Speech recognition error: {e}")
                    time.sleep(1)  # Brief pause before retrying
                    
            except sr.WaitTimeoutError:
                # No speech detected within timeout - this is normal
                pass
            except Exception as e:
                self.logger.error(f"Error in voice command listener: {str(e)}")
                time.sleep(1)
    
    def _process_command(self, text: str):
        """Process recognized speech text for commands"""
        text_lower = text.lower().strip()
        
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
    
    def test_microphone(self) -> bool:
        """Test if microphone is working"""
        if not SPEECH_RECOGNITION_AVAILABLE or not PYAUDIO_AVAILABLE:
            self.logger.warning("Cannot test microphone - libraries not available")
            return False
        
        try:
            with self.microphone as source:
                self.logger.info("Testing microphone... Say something!")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
            text = self.recognizer.recognize_google(audio)
            self.logger.info(f"Microphone test successful! Heard: '{text}'")
            return True
            
        except sr.WaitTimeoutError:
            self.logger.warning("Microphone test timeout - no speech detected")
            return False
        except Exception as e:
            self.logger.error(f"Microphone test failed: {str(e)}")
            return False
    
    def get_voice_status(self) -> dict:
        """Get current voice command status"""
        return {
            "listening": self.listening,
            "speech_recognition_available": SPEECH_RECOGNITION_AVAILABLE,
            "pyaudio_available": PYAUDIO_AVAILABLE,
            "simulation_mode": self.simulation_mode,
            "language": self.language,
            "capture_commands": self.capture_commands,
            "shutdown_commands": self.shutdown_commands,
            "microphone_available": self.microphone is not None
        }
    
    def simulate_capture_command(self):
        """Simulate a capture voice command (for testing)"""
        self.logger.info("Simulating capture voice command")
        self._handle_capture_command()
    
    def simulate_shutdown_command(self):
        """Simulate a shutdown voice command (for testing)"""
        self.logger.info("Simulating shutdown voice command")
        self._handle_shutdown_command()
    
    def cleanup(self):
        """Clean up voice command resources"""
        self.logger.info("Cleaning up voice command manager...")
        
        # Stop listening
        self.stop_listening()
        
        self.logger.info("Voice command manager cleanup complete")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Test function for voice commands
def test_voice_commands():
    """Test function for voice command manager"""
    logging.basicConfig(level=logging.INFO)
    
    def on_capture():
        print("🎯 Capture command received!")
    
    def on_shutdown():
        print("🛑 Shutdown command received!")
    
    voice_manager = VoiceCommandManager()
    voice_manager.set_capture_callback(on_capture)
    voice_manager.set_shutdown_callback(on_shutdown)
    
    print("Voice Command Test")
    print("Status:", voice_manager.get_voice_status())
    
    # Test microphone
    if not voice_manager.simulation_mode:
        print("\n--- Microphone Test ---")
        voice_manager.test_microphone()
    
    voice_manager.start_listening()
    
    try:
        if voice_manager.simulation_mode:
            print("Running in simulation mode. Testing voice commands...")
            time.sleep(2)
            voice_manager.simulate_capture_command()
            time.sleep(1)
            voice_manager.simulate_shutdown_command()
        else:
            print("Listening for voice commands. Say 'capture' or 'shutdown'...")
            print("Available capture commands:", voice_manager.capture_commands)
            print("Available shutdown commands:", voice_manager.shutdown_commands)
            time.sleep(30)  # Listen for 30 seconds
            
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        voice_manager.cleanup()

if __name__ == "__main__":
    test_voice_commands() 