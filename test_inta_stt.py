#!/usr/bin/env python3
"""
Test script for INTA AI Manager STT functionality
Tests the improved microphone detection and speech recognition
"""

import logging
import sys
import os

# Add the modules directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_inta_stt():
    """Test the INTA AI Manager STT functionality"""
    try:
        # Import the inta_ai_manager
        from modules.inta_ai_manager import IntaAIManager
        
        # Create a simple config for testing
        config = {
            'inta': {
                'wake_word': 'inta',
                'wake_word_confidence': 0.7,
                'wake_word_timeout': 5.0,
                'contextual_mode': True,
                'confirmation_required': False,
                'confirmation_timeout': 10.0,
                'sample_rate': 16000,
                'chunk_size': 1024,
                'vad_aggressiveness': 2,
                'speech_frames_threshold': 3,
                'silence_frames_threshold': 10,
                'realtime_buffer_size': 4096,
                'max_audio_length': 10.0,
                'whisper_model': 'tiny'
            },
            'openai': {
                'api_key': 'test_key'  # This won't be used for basic testing
            }
        }
        
        logger.info("Initializing INTA AI Manager...")
        
        # Initialize the manager
        inta_manager = IntaAIManager(config)
        
        # Check if speech recognition was initialized successfully
        if inta_manager.recognizer and inta_manager.microphone:
            logger.info("✅ Speech recognition initialized successfully!")
            logger.info(f"Microphone info: {inta_manager._get_microphone_info()}")
            
            # Test the speech recognition
            logger.info("Testing speech recognition...")
            logger.info("Please say something when prompted...")
            
            # Start listening for a short time
            if inta_manager.start_listening():
                logger.info("✅ Started listening successfully!")
                
                # Listen for 10 seconds
                import time
                time.sleep(10)
                
                # Stop listening
                inta_manager.stop_listening()
                logger.info("✅ Stopped listening successfully!")
                
                # Clean up
                inta_manager.cleanup()
                logger.info("✅ Cleanup completed successfully!")
                
            else:
                logger.error("❌ Failed to start listening!")
                
        else:
            logger.error("❌ Speech recognition initialization failed!")
            logger.error(f"Recognizer: {inta_manager.recognizer}")
            logger.error(f"Microphone: {inta_manager.microphone}")
            
    except Exception as e:
        logger.error(f"❌ Error testing INTA STT: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    logger.info("Starting INTA AI Manager STT test...")
    test_inta_stt()
    logger.info("Test completed!")

if __name__ == "__main__":
    main() 