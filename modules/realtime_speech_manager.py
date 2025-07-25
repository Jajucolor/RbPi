"""
Real-Time Speech Manager Module
Handles real-time text-to-speech with word-by-word generation
"""

import logging
import threading
import queue
import time
import os
import tempfile
import re
from typing import Optional, Callable
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

class RealtimeSpeechManager:
    """Real-time speech manager that speaks words as they're generated"""
    
    def __init__(self, volume: float = 0.9, language: str = 'en', slow: bool = False):
        self.logger = logging.getLogger(__name__)
        self.volume = volume
        self.language = language
        self.slow = slow
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.speech_thread = None
        self.stop_speaking = False
        self.temp_dir = Path(tempfile.gettempdir()) / "glasses_realtime_tts"
        
        # Real-time settings
        self.word_delay = 0.1  # Delay between words (seconds)
        self.sentence_delay = 0.3  # Delay between sentences (seconds)
        self.chunk_size = 3  # Number of words to speak at once
        
        # Callback for real-time generation
        self.on_word_spoken = None
        self.on_sentence_complete = None
        
        # Create temp directory for audio files
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize audio mixer
        self.initialize_audio()
        
        # Start speech worker thread
        self.start_speech_worker()
        
        self.logger.info("Real-time speech manager initialized")
    
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
        self.logger.info("Real-time speech worker thread started")
    
    def _speech_worker(self):
        """Worker thread for processing real-time speech"""
        while not self.stop_speaking:
            try:
                # Get next speech item from queue (with timeout)
                speech_item = self.speech_queue.get(timeout=1)
                
                if speech_item is None:  # Shutdown signal
                    break
                
                text, priority, is_realtime = speech_item
                
                # Process the speech
                if is_realtime:
                    self._speak_realtime(text)
                else:
                    self._speak_text(text)
                
                # Mark task as done
                self.speech_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in speech worker: {str(e)}")
    
    def _speak_realtime(self, text: str):
        """Speak text in real-time, word by word"""
        if not text.strip():
            return
        
        self.is_speaking = True
        
        try:
            # Split text into sentences and words
            sentences = self._split_into_sentences(text)
            
            for sentence in sentences:
                if self.stop_speaking:
                    break
                
                # Split sentence into word chunks
                words = sentence.split()
                word_chunks = [words[i:i + self.chunk_size] for i in range(0, len(words), self.chunk_size)]
                
                for chunk in word_chunks:
                    if self.stop_speaking:
                        break
                    
                    chunk_text = " ".join(chunk)
                    if chunk_text.strip():
                        # Speak this chunk
                        self._speak_chunk(chunk_text)
                        
                        # Callback for word spoken
                        if self.on_word_spoken:
                            self.on_word_spoken(chunk_text)
                        
                        # Delay between chunks
                        time.sleep(self.word_delay)
                
                # Callback for sentence complete
                if self.on_sentence_complete:
                    self.on_sentence_complete(sentence)
                
                # Delay between sentences
                time.sleep(self.sentence_delay)
                
        except Exception as e:
            self.logger.error(f"Error in real-time speech: {str(e)}")
        
        finally:
            self.is_speaking = False
    
    def _speak_chunk(self, chunk_text: str):
        """Speak a small chunk of text"""
        if not GTTS_AVAILABLE or not PYGAME_AVAILABLE:
            # Simulation mode
            self.logger.info(f"[SIMULATION] Speaking chunk: {chunk_text}")
            return
        
        try:
            # Generate speech for this chunk
            tts = gTTS(text=chunk_text, lang=self.language, slow=self.slow)
            
            # Create temporary file
            temp_file = self.temp_dir / f"realtime_{int(time.time() * 1000)}.mp3"
            
            # Save audio to temporary file
            tts.save(str(temp_file))
            
            # Play audio file
            pygame.mixer.music.load(str(temp_file))
            pygame.mixer.music.play()
            
            # Wait for playback to complete (with timeout)
            start_time = time.time()
            while pygame.mixer.music.get_busy() and (time.time() - start_time) < 5.0:
                time.sleep(0.1)
            
            # Clean up temporary file
            self._cleanup_temp_file(temp_file)
            
        except Exception as e:
            self.logger.error(f"Error speaking chunk '{chunk_text}': {str(e)}")
    
    def _split_into_sentences(self, text: str) -> list:
        """Split text into sentences for better real-time processing"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _speak_text(self, text: str):
        """Speak complete text (fallback method)"""
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
                self._cleanup_temp_file(temp_file)
                
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
    
    def speak_realtime(self, text: str, priority: int = 0, interrupt: bool = False):
        """
        Speak text in real-time, word by word
        
        Args:
            text: Text to speak
            priority: Priority level (0 = normal, 1 = high, 2 = urgent)
            interrupt: Whether to interrupt current speech
        """
        if not text.strip():
            return
        
        if interrupt:
            self.stop_current_speech()
        
        # Add to queue as real-time speech
        self.speech_queue.put((text, priority, True))
        self.logger.debug(f"Added real-time speech to queue: {text[:50]}...")
    
    def speak(self, text: str, priority: int = 0, interrupt: bool = False):
        """
        Speak complete text (traditional method)
        
        Args:
            text: Text to speak
            priority: Priority level (0 = normal, 1 = high, 2 = urgent)
            interrupt: Whether to interrupt current speech
        """
        if not text.strip():
            return
        
        if interrupt:
            self.stop_current_speech()
        
        # Add to queue as complete speech
        self.speech_queue.put((text, priority, False))
        self.logger.debug(f"Added complete speech to queue: {text}")
    
    def speak_urgent(self, text: str):
        """Speak urgent message with high priority and interrupt current speech"""
        self.speak_realtime(text, priority=2, interrupt=True)
    
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
    
    def set_realtime_settings(self, word_delay: float = None, sentence_delay: float = None, chunk_size: int = None):
        """Set real-time speech settings"""
        if word_delay is not None:
            self.word_delay = word_delay
        if sentence_delay is not None:
            self.sentence_delay = sentence_delay
        if chunk_size is not None:
            self.chunk_size = chunk_size
        
        self.logger.info(f"Real-time settings updated: word_delay={self.word_delay}s, sentence_delay={self.sentence_delay}s, chunk_size={self.chunk_size}")
    
    def set_callbacks(self, on_word_spoken: Callable = None, on_sentence_complete: Callable = None):
        """Set callbacks for real-time speech events"""
        self.on_word_spoken = on_word_spoken
        self.on_sentence_complete = on_sentence_complete
        self.logger.info("Real-time speech callbacks set")
    
    def _cleanup_temp_file(self, temp_file: Path, max_retries: int = 3):
        """Clean up temporary file with retry mechanism"""
        for attempt in range(max_retries):
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    return
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                else:
                    self.logger.warning(f"Failed to delete temp file after {max_retries} attempts: {temp_file.name}")
            except Exception as e:
                self.logger.warning(f"Failed to delete temp file: {temp_file.name} - {e}")
                break
    
    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up real-time speech manager...")
        
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
        
        self.logger.info("Real-time speech manager cleanup complete")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Test function
def test_realtime_speech():
    """Test real-time speech functionality"""
    logging.basicConfig(level=logging.INFO)
    
    speech = RealtimeSpeechManager()
    
    try:
        print("Testing real-time speech system...")
        
        # Test real-time speech
        test_text = "Hello! This is a test of the real-time speech system. I will speak each word as it is generated, making the conversation much more natural and responsive."
        
        print("Speaking in real-time...")
        speech.speak_realtime(test_text)
        
        # Wait for completion
        time.sleep(10)
        
        print("Test complete!")
        
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        speech.cleanup()

if __name__ == "__main__":
    test_realtime_speech() 