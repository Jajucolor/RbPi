"""
Speech Manager Module
Handles text-to-speech functionality using gTTS for the assistive glasses system
"""

import logging
import threading
import queue
import time
import os
import tempfile
from typing import Optional
from pathlib import Path

try:
    from gtts import gTTS
    import io
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logging.warning("gTTS not available - using simulation mode")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logging.warning("pygame not available - audio playback may be limited")

class SpeechManager:
    """Manages text-to-speech functionality using gTTS for the assistive glasses"""
    
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
        
        # Create temp directory for audio files
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize audio mixer
        self.initialize_audio()
        
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
    
    def _speak_text(self, text: str):
        """Internal method to speak text using gTTS"""
        if not text.strip():
            return
        
        self.is_speaking = True
        
        try:
            if GTTS_AVAILABLE and PYGAME_AVAILABLE:
                # Generate speech with gTTS
                tts = gTTS(text=text, lang=self.language, slow=self.slow)
                
                # Create temporary file
                temp_file = self.temp_dir / f"speech_{int(time.time() * 1000)}.mp3"
                
                # Save audio to temporary file
                tts.save(str(temp_file))
                
                # Play audio file
                pygame.mixer.music.load(str(temp_file))
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                # Clean up temporary file
                try:
                    temp_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Failed to delete temp file: {e}")
                
                self.logger.info(f"Speech completed: {text[:50]}...")
                
            else:
                # Simulation mode
                self.logger.info(f"[SIMULATION] Speaking: {text}")
                # Simulate speaking time based on text length
                speaking_time = len(text) * 0.08  # ~80ms per character for gTTS
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
        """Get list of available languages for gTTS"""
        if not GTTS_AVAILABLE:
            return []
        
        try:
            from gtts.lang import tts_langs
            langs = tts_langs()
            return [{"code": code, "name": name} for code, name in langs.items()]
        except Exception as e:
            self.logger.error(f"Error getting available languages: {str(e)}")
            return []
    
    def test_speech(self, test_text: str = "Hello, this is a test of the speech system."):
        """Test the speech system with a sample text"""
        self.logger.info("Testing speech system...")
        self.speak(test_text)
    
    def get_speech_status(self) -> dict:
        """Get current speech status"""
        return {
            "is_speaking": self.is_speaking,
            "queue_size": self.speech_queue.qsize(),
            "gtts_available": GTTS_AVAILABLE,
            "pygame_available": PYGAME_AVAILABLE,
            "volume": self.volume,
            "language": self.language,
            "slow_speech": self.slow,
            "temp_dir": str(self.temp_dir)
        }
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        try:
            if self.temp_dir.exists():
                for file in self.temp_dir.glob("*.mp3"):
                    try:
                        file.unlink()
                    except Exception as e:
                        self.logger.warning(f"Failed to delete temp file {file}: {e}")
                self.logger.info("Temporary files cleaned up")
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
        print("Testing gTTS speech system...")
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