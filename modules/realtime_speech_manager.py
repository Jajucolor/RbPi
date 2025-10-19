"""
Real-Time Speech Manager Module
Provides real-time, offline text-to-speech functionality with chunked delivery.
"""

import logging
import threading
import queue
import time
import re
from typing import Optional, Callable

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available - using simulation mode for real-time speech")


class RealtimeSpeechManager:
    """Real-time speech manager that speaks chunks of text as they are generated."""

    def __init__(self, volume: float = 0.9, language: str = 'en', slow: bool = False):
        self.logger = logging.getLogger(__name__)
        self.volume = volume
        self.language = language
        self.slow = slow
        self.is_speaking = False
        self.speech_queue: "queue.Queue[tuple[str, int, bool]]" = queue.Queue()
        self.speech_thread: Optional[threading.Thread] = None
        self.stop_speaking = False
        self.tts_engine: Optional["pyttsx3.Engine"] = None
        self.default_rate: Optional[int] = None

        self.word_delay = 0.1
        self.sentence_delay = 0.3
        self.chunk_size = 3

        self.on_word_spoken: Optional[Callable[[str], None]] = None
        self.on_sentence_complete: Optional[Callable[[str], None]] = None

        self.initialize_engine()
        self.start_speech_worker()

        self.logger.info("Real-time speech manager initialized")

    def initialize_engine(self):
        if not PYTTSX3_AVAILABLE:
            self.logger.warning("pyttsx3 engine is unavailable; speech will be simulated")
            return

        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('volume', float(self.volume))
            self.default_rate = self.tts_engine.getProperty('rate')

            self._select_language_voice(self.language)
            self._apply_speed_setting(self.slow)

            self.logger.info("Offline TTS engine (real-time) initialized")

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
                    return
            if voices:
                self.tts_engine.setProperty('voice', voices[0].id)
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
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
        self.logger.info("Real-time speech worker thread started")

    def _speech_worker(self):
        while not self.stop_speaking:
            try:
                speech_item = self.speech_queue.get(timeout=1)

                if speech_item is None:
                    break

                text, _priority, is_realtime = speech_item
                if is_realtime:
                    self._speak_realtime(text)
                else:
                    self._speak_text(text)

                self.speech_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in real-time speech worker: {e}")

    def _speak_realtime(self, text: str):
        if not text.strip():
            return

        self.is_speaking = True

        try:
            sentences = self._split_into_sentences(text)
            for sentence in sentences:
                if self.stop_speaking:
                    break

                words = sentence.split()
                word_chunks = [words[i:i + self.chunk_size] for i in range(0, len(words), self.chunk_size)]

                for chunk in word_chunks:
                    if self.stop_speaking:
                        break

                    chunk_text = " ".join(chunk)
                    if chunk_text.strip():
                        self._speak_chunk(chunk_text)
                        if self.on_word_spoken:
                            self.on_word_spoken(chunk_text)
                        time.sleep(self.word_delay)

                if self.on_sentence_complete:
                    self.on_sentence_complete(sentence)

                time.sleep(self.sentence_delay)

        except Exception as e:
            self.logger.error(f"Error in real-time speech: {e}")

        finally:
            self.is_speaking = False

    def _speak_chunk(self, chunk_text: str):
        try:
            if self.tts_engine:
                self.tts_engine.say(chunk_text)
                self.tts_engine.runAndWait()
            else:
                self.logger.info(f"[SIMULATION] Speaking chunk: {chunk_text}")
                time.sleep(max(0.5, len(chunk_text) * 0.05))
        except Exception as e:
            self.logger.error(f"Error speaking chunk '{chunk_text}': {e}")

    def _split_into_sentences(self, text: str) -> list[str]:
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _speak_text(self, text: str):
        if not text.strip():
            return

        self.is_speaking = True

        try:
            if self.tts_engine:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            else:
                self.logger.info(f"[SIMULATION] Speaking: {text}")
                time.sleep(max(1, len(text) * 0.08))

        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")

        finally:
            self.is_speaking = False

    def speak(self, text: str, priority: int = 0, interrupt: bool = False, realtime: bool = False):
        if not text.strip():
            return

        if interrupt:
            self.stop_current_speech()

        self.speech_queue.put((text, priority, realtime))
        self.logger.debug(f"Queued text for {'realtime' if realtime else 'standard'} speech: {text[:50]}...")

    def speak_realtime(self, text: str, priority: int = 0, interrupt: bool = False):
        self.speak(text, priority=priority, interrupt=interrupt, realtime=True)

    def speak_urgent(self, text: str):
        self.speak(text, priority=2, interrupt=True, realtime=False)

    def stop_current_speech(self):
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
        self.logger.info("Real-time speech stopped and queue cleared")

    def wait_for_speech_completion(self, timeout: float = 10.0):
        try:
            start_time = time.time()
            while (not self.speech_queue.empty() or self.is_speaking) and (time.time() - start_time < timeout):
                time.sleep(0.1)

            self.speech_queue.join()

        except Exception as e:
            self.logger.error(f"Error waiting for real-time speech completion: {e}")

    def set_voice_properties(self, volume: Optional[float] = None, language: Optional[str] = None, slow: Optional[bool] = None):
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
            "Real-time voice properties updated: volume=%s, language=%s, slow=%s",
            self.volume,
            self.language,
            self.slow,
        )

    def get_speech_status(self) -> dict:
        return {
            "is_speaking": self.is_speaking,
            "queue_size": self.speech_queue.qsize(),
            "engine_available": self.tts_engine is not None,
            "volume": self.volume,
            "language": self.language,
            "slow_speech": self.slow,
        }

    def cleanup(self):
        self.logger.info("Cleaning up real-time speech manager")
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

        self.logger.info("Real-time speech manager cleanup complete")

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass


def test_realtime_speech_manager():
    logging.basicConfig(level=logging.INFO)
    speech = RealtimeSpeechManager()

    try:
        print("Testing real-time offline speech system...")
        speech.speak_realtime("This is a real time speech test that speaks in small chunks.")
        speech.wait_for_speech_completion()
        print("Status:", speech.get_speech_status())
    finally:
        speech.cleanup()


if __name__ == "__main__":
    test_realtime_speech_manager()
