"""
Speech Manager Module
Handles offline text-to-speech functionality for the assistive glasses system
"""

import logging
import threading
import queue
import time
import tempfile
from typing import Optional
from pathlib import Path

try:
    from TTS.api import TTS as CoquiTTS
    COQUI_TTS_AVAILABLE = True
except ImportError:
    COQUI_TTS_AVAILABLE = False
    logging.warning("Coqui TTS not available - using simulation mode")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logging.warning("pygame not available - audio playback may be limited")

class SpeechManager:
    """Manages offline text-to-speech functionality using Coqui TTS"""
    
    def __init__(self, volume: float = 0.9, language: str = 'en', slow: bool = False):
        self.logger = logging.getLogger(__name__)
        self.volume = volume
        self.language = language
        self.slow = slow
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.speech_thread = None
        self.stop_speaking = False
        self.temp_dir = Path(tempfile.gettempdir()) / "glasses_tts"
        self.tts_engine = None
        self.model_name = "tts_models/en/vctk/vits"
        
        # Create temp directory for audio files
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize audio mixer
        self.initialize_audio()

        # Initialize TTS engine
        self.initialize_tts()
        
        # Start speech worker thread
        self.start_speech_worker()
    
    def initialize_audio(self):
        """Initialize the audio mixer for playback"""
        if not PYGAME_AVAILABLE:
            self.logger.warning("Running in simulation mode - audio not available")
            return
        
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=4096)
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
            self.logger.info("Audio mixer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio mixer: {str(e)}")
    
    def start_speech_worker(self):
        """Start the speech worker thread"""
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
        self.logger.info("Speech worker thread started")
    
    def _speech_worker(self):
        """Worker thread for processing speech queue"""
        while not self.stop_speaking:
            try:
                # Get next speech item from queue (with timeout)
                speech_item = self.speech_queue.get(timeout=1)
                
                if speech_item is None:  # Shutdown signal
                    break
                
                text, priority = speech_item
                
                # Process the speech
                self._speak_text(text)
                
                # Mark task as done
                self.speech_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in speech worker: {str(e)}")
    
    def initialize_tts(self, model_name: Optional[str] = None):
        """Initialize the offline TTS engine"""
        if not COQUI_TTS_AVAILABLE:
            self.logger.warning("Coqui TTS library not available - running in simulation mode")
            return

        model_to_use = model_name or self.model_name
        try:
            self.tts_engine = CoquiTTS(model_to_use)
            self.model_name = model_to_use
            self.logger.info(f"Coqui TTS engine initialized with model '{model_to_use}'")
        except Exception as e:
            self.tts_engine = None
            self.logger.error(f"Failed to initialize Coqui TTS engine: {e}")

    def _speak_text(self, text: str):
        """Internal method to speak text using Coqui TTS"""
        if not text.strip():
            return

        self.is_speaking = True

        try:
            if self.tts_engine and PYGAME_AVAILABLE:
                temp_file = self.temp_dir / f"speech_{int(time.time() * 1000)}.wav"

                # Generate speech with Coqui TTS
                self.tts_engine.tts_to_file(text=text, file_path=str(temp_file))

                # Play audio file
                pygame.mixer.music.load(str(temp_file))
                pygame.mixer.music.play()

                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                # Clean up temporary file with retry mechanism
                self._cleanup_temp_file(temp_file)
                
                self.logger.info(f"Speech completed: {text[:50]}...")

            else:
                # Simulation mode
                self.logger.info(f"[SIMULATION] Speaking: {text}")
                # Simulate speaking time based on text length
                speaking_time = len(text) * 0.08  # Approximate speaking time per character
                time.sleep(max(1, speaking_time))
                
        except Exception as e:
            self.logger.error(f"Error speaking text: {str(e)}")
        
        finally:
            self.is_speaking = False
    
    def speak(self, text: str, priority: int = 0, interrupt: bool = False):
        """
        Add text to speech queue
        
        Args:
            text: Text to speak
            priority: Priority level (0 = normal, 1 = high, 2 = urgent)
            interrupt: Whether to interrupt current speech
        """
        if not text.strip():
            return
        
        if interrupt:
            self.stop_current_speech()
        
        # Add to queue
        self.speech_queue.put((text, priority))
        self.logger.debug(f"Added to speech queue: {text}")
    
    def speak_urgent(self, text: str):
        """Speak urgent message with high priority and interrupt current speech"""
        self.speak(text, priority=2, interrupt=True)
    
    def stop_current_speech(self):
        """Stop current speech and clear queue"""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except Exception as e:
                self.logger.error(f"Error stopping speech: {str(e)}")
        
        # Clear the queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
        
        self.is_speaking = False
        self.logger.info("Speech stopped and queue cleared")
    
    def wait_for_speech_completion(self, timeout: float = 10.0):
        """Wait for all queued speech to complete"""
        try:
            # Wait for queue to be empty
            start_time = time.time()
            while not self.speech_queue.empty() or self.is_speaking:
                if time.time() - start_time > timeout:
                    self.logger.warning("Speech completion timeout reached")
                    break
                time.sleep(0.1)
            
            # Wait for queue to be fully processed
            self.speech_queue.join()
            
        except Exception as e:
            self.logger.error(f"Error waiting for speech completion: {str(e)}")
    
    def set_voice_properties(self, volume: Optional[float] = None, language: Optional[str] = None, slow: Optional[bool] = None):
        """
        Update voice properties
        
        Args:
            volume: Volume level (0.0 to 1.0)
            language: Language code (e.g., 'en', 'es', 'fr')
            slow: Whether to speak slowly
        """
        if volume is not None:
            self.volume = volume
            if PYGAME_AVAILABLE:
                try:
                    pygame.mixer.music.set_volume(volume)
                except Exception as e:
                    self.logger.error(f"Error setting volume: {str(e)}")
        
        if language is not None:
            self.language = language
        
        if slow is not None:
            self.slow = slow
        
        self.logger.info(f"Voice properties updated: volume={self.volume}, language={self.language}, slow={self.slow}")
    
    def get_available_languages(self) -> list:
        """Get list of available voices/models for the offline TTS engine"""
        if not self.tts_engine:
            return []

        # Coqui models are language-specific; expose the currently loaded model
        return [{
            "code": self.model_name,
            "name": f"Coqui TTS model ({self.model_name})"
        }]
    
    def test_speech(self, test_text: str = "Hello, this is a test of the speech system."):
        """Test the speech system with a sample text"""
        self.logger.info("Testing speech system...")
        self.speak(test_text)
    
    def get_speech_status(self) -> dict:
        """Get current speech status"""
        return {
            "is_speaking": self.is_speaking,
            "queue_size": self.speech_queue.qsize(),
            "coqui_available": COQUI_TTS_AVAILABLE,
            "pygame_available": PYGAME_AVAILABLE,
            "volume": self.volume,
            "language": self.language,
            "slow_speech": self.slow,
            "temp_dir": str(self.temp_dir),
            "tts_model": self.model_name,
            "engine_initialized": self.tts_engine is not None
        }
    
    def _cleanup_temp_file(self, temp_file: Path, max_retries: int = 5):
        """Clean up temporary file with retry mechanism for Windows compatibility"""
        for attempt in range(max_retries):
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    self.logger.debug(f"Successfully deleted temp file: {temp_file.name}")
                    return
            except PermissionError as e:
                if attempt < max_retries - 1:
                    # Wait a bit longer between retries
                    wait_time = (attempt + 1) * 0.5
                    self.logger.debug(f"File {temp_file.name} still in use, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    self.logger.warning(f"Failed to delete temp file after {max_retries} attempts: {temp_file.name} - {e}")
            except Exception as e:
                self.logger.warning(f"Failed to delete temp file: {temp_file.name} - {e}")
                break
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files with Windows compatibility"""
        try:
            if self.temp_dir.exists():
                files_cleaned = 0
                files_failed = 0
                
                for file in self.temp_dir.glob("*.wav"):
                    try:
                        # Use the improved cleanup method
                        self._cleanup_temp_file(file, max_retries=3)
                        files_cleaned += 1
                    except Exception as e:
                        files_failed += 1
                        self.logger.warning(f"Failed to delete temp file {file.name}: {e}")
                
                if files_cleaned > 0:
                    self.logger.info(f"Cleaned up {files_cleaned} temporary files")
                if files_failed > 0:
                    self.logger.warning(f"Failed to clean up {files_failed} temporary files")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {str(e)}")
    
    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up speech manager...")
        
        # Stop speech worker
        self.stop_speaking = True
        self.speech_queue.put(None)  # Signal shutdown
        
        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=2)
        
        # Stop any current speech
        self.stop_current_speech()
        
        # Clean up audio mixer
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.quit()
            except Exception as e:
                self.logger.error(f"Error stopping audio mixer: {str(e)}")
        
        # Clean up temporary files
        self.cleanup_temp_files()
        
        self.logger.info("Speech manager cleanup complete")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Test function for the speech manager
def test_speech_manager():
    """Test function for speech manager"""
    logging.basicConfig(level=logging.INFO)
    
    speech = SpeechManager()
    
    try:
        print("Testing offline speech system...")
        speech.test_speech()
        
        print("Status:", speech.get_speech_status())
        
        # Wait for speech to complete
        speech.wait_for_speech_completion()
        
        print("Available languages:", len(speech.get_available_languages()))
        
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        speech.cleanup()

if __name__ == "__main__":
    test_speech_manager()
