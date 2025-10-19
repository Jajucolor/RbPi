"""
Speech Manager Module
Provides offline text-to-speech capabilities for the assistive glasses system.
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
    logging.warning("pyttsx3 not available - using simulation mode for speech output")


class SpeechManager:
    """Manages text-to-speech functionality using an offline TTS engine."""

    def __init__(self, volume: float = 0.9, language: str = 'en', slow: bool = False):
        self.logger = logging.getLogger(__name__)
        self.volume = volume
        self.language = language
        self.slow = slow
        self.is_speaking = False
        self.speech_queue: "queue.Queue[tuple[str, int]]" = queue.Queue()
        self.speech_thread: Optional[threading.Thread] = None
        self.stop_speaking = False
        self.tts_engine: Optional["pyttsx3.Engine"] = None
        self.default_rate: Optional[int] = None

        self.initialize_engine()
        self.start_speech_worker()

    def initialize_engine(self):
        """Initialize the pyttsx3 engine with desired settings."""
        if not PYTTSX3_AVAILABLE:
            self.logger.warning("pyttsx3 engine is unavailable; speech will be simulated")
            return

        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('volume', float(self.volume))
            self.default_rate = self.tts_engine.getProperty('rate')

            if self.language:
                self._select_language_voice(self.language)

            self._apply_speed_setting(self.slow)

            self.logger.info("Offline TTS engine initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize pyttsx3 engine: {e}")
            self.tts_engine = None

    def _select_language_voice(self, language_code: str):
        if not self.tts_engine:
            return

        try:
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                languages = []
                if hasattr(voice, 'languages'):
                    languages = [lang.decode('utf-8') if isinstance(lang, bytes) else lang for lang in voice.languages]
                if any(language_code.lower() in lang.lower() for lang in languages):
                    self.tts_engine.setProperty('voice', voice.id)
                    self.logger.info(f"Selected voice '{voice.name}' for language '{language_code}'")
                    return

            if voices:
                self.tts_engine.setProperty('voice', voices[0].id)
                self.logger.warning(
                    "No voice matched language '%s'; using default voice '%s'",
                    language_code,
                    voices[0].name,
                )
        except Exception as e:
            self.logger.warning(f"Failed to set language '{language_code}' for pyttsx3: {e}")

    def _apply_speed_setting(self, slow: bool):
        if not self.tts_engine:
            return

        try:
            base_rate = self.default_rate or self.tts_engine.getProperty('rate')
            if slow:
                self.tts_engine.setProperty('rate', max(80, int(base_rate * 0.75)))
            else:
                self.tts_engine.setProperty('rate', base_rate)
        except Exception as e:
            self.logger.warning(f"Failed to adjust speech rate: {e}")

    def start_speech_worker(self):
        """Start the worker thread that processes queued speech."""
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
        self.logger.info("Speech worker thread started")

    def _speech_worker(self):
        """Continuously process items from the speech queue."""
        while not self.stop_speaking:
            try:
                speech_item = self.speech_queue.get(timeout=1)

                if speech_item is None:
                    break

                text, _priority = speech_item
                self._speak_text(text)
                self.speech_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in speech worker: {e}")

    def _speak_text(self, text: str):
        """Speak text using the offline TTS engine or simulation fallback."""
        if not text.strip():
            return

        self.is_speaking = True

        try:
            if self.tts_engine:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                self.logger.info(f"Speech completed: {text[:50]}...")
            else:
                self.logger.info(f"[SIMULATION] Speaking: {text}")
                time.sleep(max(1, len(text) * 0.08))

        except Exception as e:
            self.logger.error(f"Error during speech synthesis: {e}")

        finally:
            self.is_speaking = False

    def speak(self, text: str, priority: int = 0, interrupt: bool = False):
        """Queue text for speech output."""
        if not text.strip():
            return

        if interrupt:
            self.stop_current_speech()

        self.speech_queue.put((text, priority))
        self.logger.debug(f"Queued text for speech: {text[:50]}...")

    def speak_urgent(self, text: str):
        """Speak urgent text immediately."""
        self.speak(text, priority=2, interrupt=True)

    def stop_current_speech(self):
        """Stop any ongoing speech and clear the queue."""
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except Exception as e:
                self.logger.error(f"Error stopping speech: {e}")

        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break

        self.is_speaking = False
        self.logger.info("Speech stopped and queue cleared")

    def wait_for_speech_completion(self, timeout: float = 10.0):
        """Block until queued speech is finished or timeout occurs."""
        try:
            start_time = time.time()
            while (not self.speech_queue.empty() or self.is_speaking) and (time.time() - start_time < timeout):
                time.sleep(0.1)

            self.speech_queue.join()

        except Exception as e:
            self.logger.error(f"Error waiting for speech completion: {e}")

    def set_voice_properties(self, volume: Optional[float] = None, language: Optional[str] = None, slow: Optional[bool] = None):
        """Update runtime voice properties."""
        if volume is not None:
            self.volume = volume
            if self.tts_engine:
                try:
                    self.tts_engine.setProperty('volume', float(volume))
                except Exception as e:
                    self.logger.error(f"Failed to set volume: {e}")

        if language is not None:
            self.language = language
            self._select_language_voice(language)

        if slow is not None:
            self.slow = slow
            self._apply_speed_setting(slow)

        self.logger.info(
            "Voice properties updated: volume=%s, language=%s, slow=%s",
            self.volume,
            self.language,
            self.slow,
        )

    def get_speech_status(self) -> dict:
        """Return current speech system status."""
        return {
            "is_speaking": self.is_speaking,
            "queue_size": self.speech_queue.qsize(),
            "engine_available": self.tts_engine is not None,
            "volume": self.volume,
            "language": self.language,
            "slow_speech": self.slow,
        }

    def cleanup(self):
        """Release resources associated with the speech manager."""
        self.logger.info("Cleaning up speech manager")
        self.stop_speaking = True
        self.speech_queue.put(None)

        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=2)

        self.stop_current_speech()

        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except Exception:
                pass
            self.tts_engine = None

        self.logger.info("Speech manager cleanup complete")

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass


def test_speech_manager():
    """Simple smoke test for the speech manager."""
    logging.basicConfig(level=logging.INFO)
    speech = SpeechManager()

    try:
        print("Testing offline speech system...")
        speech.speak("This is a test of the offline speech system.")
        speech.wait_for_speech_completion()
        print("Status:", speech.get_speech_status())
    finally:
        speech.cleanup()


if __name__ == "__main__":
    test_speech_manager()
