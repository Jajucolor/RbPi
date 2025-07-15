"""
Speech Manager Module
Handles text-to-speech functionality for the assistive glasses system
"""

import logging
import threading
import queue
import time
from typing import Optional

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available - using simulation mode")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logging.warning("pygame not available - audio playback may be limited")

class SpeechManager:
    """Manages text-to-speech functionality for the assistive glasses"""
    
    def __init__(self, voice_rate: int = 150, volume: float = 0.9):
        self.logger = logging.getLogger(__name__)
        self.voice_rate = voice_rate
        self.volume = volume
        self.engine = None
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.speech_thread = None
        self.stop_speaking = False
        
        # Initialize TTS engine
        self.initialize_tts()
        
        # Start speech worker thread
        self.start_speech_worker()
    
    def initialize_tts(self):
        """Initialize the text-to-speech engine"""
        if not PYTTSX3_AVAILABLE:
            self.logger.warning("Running in simulation mode - TTS not available")
            return
        
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice properties
            self.engine.setProperty('rate', self.voice_rate)
            self.engine.setProperty('volume', self.volume)
            
            # Try to set a better voice if available
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer female voices for better clarity
                for voice in voices:
                    if hasattr(voice, 'name') and ('female' in voice.name.lower() or 'woman' in voice.name.lower()):
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use the first available voice
                    if len(voices) > 0:
                        self.engine.setProperty('voice', voices[0].id)
            
            self.logger.info("Text-to-speech engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {str(e)}")
            self.engine = None
    
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
        """Internal method to speak text"""
        if not text.strip():
            return
        
        self.is_speaking = True
        
        try:
            if PYTTSX3_AVAILABLE and self.engine:
                self.logger.info(f"Speaking: {text}")
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                # Simulation mode
                self.logger.info(f"[SIMULATION] Speaking: {text}")
                # Simulate speaking time based on text length
                speaking_time = len(text) * 0.05  # ~50ms per character
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
        if PYTTSX3_AVAILABLE and self.engine:
            try:
                self.engine.stop()
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
    
    def set_voice_properties(self, rate: Optional[int] = None, volume: Optional[float] = None):
        """
        Update voice properties
        
        Args:
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
        """
        if not PYTTSX3_AVAILABLE or not self.engine:
            self.logger.warning("Cannot set voice properties - TTS not available")
            return
        
        try:
            if rate is not None:
                self.voice_rate = rate
                self.engine.setProperty('rate', rate)
            
            if volume is not None:
                self.volume = volume
                self.engine.setProperty('volume', volume)
            
            self.logger.info(f"Voice properties updated: rate={self.voice_rate}, volume={self.volume}")
            
        except Exception as e:
            self.logger.error(f"Error setting voice properties: {str(e)}")
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        if not PYTTSX3_AVAILABLE or not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            voice_list = []
            
            for voice in voices:
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'language': getattr(voice, 'language', 'unknown'),
                    'gender': getattr(voice, 'gender', 'unknown')
                }
                voice_list.append(voice_info)
            
            return voice_list
            
        except Exception as e:
            self.logger.error(f"Error getting available voices: {str(e)}")
            return []
    
    def set_voice(self, voice_id: str):
        """Set the voice to use"""
        if not PYTTSX3_AVAILABLE or not self.engine:
            self.logger.warning("Cannot set voice - TTS not available")
            return
        
        try:
            self.engine.setProperty('voice', voice_id)
            self.logger.info(f"Voice set to: {voice_id}")
            
        except Exception as e:
            self.logger.error(f"Error setting voice: {str(e)}")
    
    def get_speech_status(self) -> dict:
        """Get current speech status"""
        return {
            "is_speaking": self.is_speaking,
            "queue_size": self.speech_queue.qsize(),
            "tts_available": PYTTSX3_AVAILABLE and self.engine is not None,
            "voice_rate": self.voice_rate,
            "volume": self.volume
        }
    
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
        
        # Clean up TTS engine
        if self.engine:
            try:
                self.engine.stop()
            except Exception as e:
                self.logger.error(f"Error stopping TTS engine: {str(e)}")
        
        self.logger.info("Speech manager cleanup complete")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup() 