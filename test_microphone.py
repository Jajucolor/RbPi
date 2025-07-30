#!/usr/bin/env python3
"""
Test script for improved microphone detection and STT functionality
Based on the reference code provided
"""

import logging
import speech_recognition as sr
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_microphone_detection():
    """Test microphone detection and list available devices"""
    try:
        # List all available microphones
        mics = sr.Microphone.list_microphone_names()
        logger.info(f"Available microphones: {mics}")
        
        # Try default microphone
        logger.info("Testing default microphone...")
        try:
            mic = sr.Microphone()
            logger.info(f"Default microphone: {mic}")
            return mic
        except Exception as e:
            logger.error(f"Default microphone failed: {e}")
        
        # Try different device configurations
        for device_index in range(min(5, len(mics))):
            try:
                logger.info(f"Testing microphone device {device_index}...")
                mic = sr.Microphone(device_index=device_index)
                logger.info(f"Microphone {device_index} working: {mic}")
                return mic
            except Exception as e:
                logger.warning(f"Microphone {device_index} failed: {e}")
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"Error in microphone detection: {e}")
        return None

def test_speech_recognition(microphone):
    """Test speech recognition with the given microphone"""
    if not microphone:
        logger.error("No microphone available for testing")
        return False
    
    try:
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Configure recognizer settings
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        recognizer.non_speaking_duration = 0.5
        recognizer.phrase_threshold = 0.3
        
        # Adjust for ambient noise
        logger.info("Adjusting for ambient noise... Please stay quiet for 2 seconds.")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=2)
        
        # Test listening
        logger.info("Please say something... (5 second timeout)")
        with microphone as source:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                logger.info("Audio captured successfully")
                
                # Try to recognize speech
                try:
                    text = recognizer.recognize_google(audio)
                    logger.info(f"Recognized speech: '{text}'")
                    return True
                except sr.UnknownValueError:
                    logger.warning("Google Speech Recognition could not understand audio")
                    return False
                except sr.RequestError as e:
                    logger.error(f"Google Speech Recognition service error: {e}")
                    return False
                    
            except sr.WaitTimeoutError:
                logger.warning("No speech detected within timeout")
                return False
                
    except Exception as e:
        logger.error(f"Error in speech recognition test: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting microphone and STT test...")
    
    # Test microphone detection
    microphone = test_microphone_detection()
    
    if microphone:
        logger.info("Microphone detection successful!")
        
        # Test speech recognition
        if test_speech_recognition(microphone):
            logger.info("Speech recognition test successful!")
        else:
            logger.error("Speech recognition test failed!")
    else:
        logger.error("Microphone detection failed!")

if __name__ == "__main__":
    main() 