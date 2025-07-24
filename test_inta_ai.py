#!/usr/bin/env python3
"""
INTA AI Test Script
Test script for the INTA AI assistant with speech recognition and conversation
"""

import time
import json
import logging
import sys
from pathlib import Path

# Import the INTA AI manager
from modules.inta_ai_manager import IntaAIManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('inta_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_config():
    """Load configuration from config.json"""
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        # Default configuration for testing
        return {
            "openai": {
                "api_key": "your-openai-api-key-here",
                "model": "gpt-4o-mini",
                "max_tokens": 150,
                "temperature": 0.7
            },
            "jaison": {
                "url": "http://localhost:8000",
                "api_key": ""
            },
            "inta": {
                "sample_rate": 16000,
                "chunk_size": 1024,
                "record_seconds": 5,
                "silence_threshold": 0.01,
                "silence_duration": 1.0
            }
        }

def test_inta_ai():
    """Test the INTA AI assistant"""
    logger = logging.getLogger(__name__)
    
    print("=" * 60)
    print("INTA AI Assistant Test")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    
    # Initialize INTA AI
    print("Initializing INTA AI...")
    inta = IntaAIManager(config)
    
    # Check status
    status = inta.get_status()
    print("\nINTA AI Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    if not status["whisper_available"]:
        print("\n⚠️  Warning: Whisper not available. Speech recognition will be disabled.")
        print("   Install with: pip install openai-whisper")
    
    if not status["audio_available"]:
        print("\n⚠️  Warning: PyAudio not available. Audio recording will be disabled.")
        print("   Install with: pip install pyaudio")
    
    if not status["jaison_configured"] and not status["openai_configured"]:
        print("\n⚠️  Warning: No AI backend configured.")
        print("   Configure OpenAI API key or JAISON server in config.json")
    
    print("\n" + "=" * 60)
    print("Test Options:")
    print("1. Start continuous listening (voice commands)")
    print("2. Test text-based conversation")
    print("3. Test specific functions")
    print("4. Exit")
    print("=" * 60)
    
    while True:
        try:
            choice = input("\nSelect test option (1-4): ").strip()
            
            if choice == "1":
                test_voice_listening(inta)
            elif choice == "2":
                test_text_conversation(inta)
            elif choice == "3":
                test_functions(inta)
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please select 1-4.")
                
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user.")
            break
        except Exception as e:
            logger.error(f"Test error: {str(e)}")
            print(f"Error: {str(e)}")
    
    # Cleanup
    inta.cleanup()
    print("\nTest completed. Goodbye!")

def test_voice_listening(inta):
    """Test voice listening functionality"""
    print("\n🎤 Voice Listening Test")
    print("Speak clearly into your microphone.")
    print("Say 'stop listening' to end the test.")
    
    try:
        # Start listening
        if inta.start_listening():
            print("✅ Started listening for voice commands...")
            
            # Keep listening until user says stop
            while inta.listening:
                time.sleep(1)
                
                # Check if user wants to stop
                if input("\nPress Enter to stop listening, or just wait... ").strip().lower() in ['stop', 'quit', 'exit']:
                    break
            
            inta.stop_listening()
            print("✅ Stopped listening.")
        else:
            print("❌ Failed to start listening. Check your audio setup.")
            
    except Exception as e:
        print(f"❌ Error during voice test: {str(e)}")

def test_text_conversation(inta):
    """Test text-based conversation"""
    print("\n💬 Text Conversation Test")
    print("Type your messages and press Enter.")
    print("Type 'quit' to end the conversation.")
    
    try:
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Ending conversation...")
                break
            
            if user_input:
                print("Processing...")
                response = inta.process_command(user_input)
                print(f"INTA: {response}")
            else:
                print("Please enter a message.")
                
    except KeyboardInterrupt:
        print("\nConversation interrupted.")
    except Exception as e:
        print(f"❌ Error during conversation: {str(e)}")

def test_functions(inta):
    """Test specific INTA functions"""
    print("\n🔧 Function Test")
    print("Testing INTA's ability to execute specific functions...")
    
    test_functions = [
        "capture_image",
        "describe_surroundings", 
        "navigate",
        "read_text",
        "identify_objects"
    ]
    
    for func_name in test_functions:
        print(f"\nTesting function: {func_name}")
        response = inta.execute_function(func_name)
        print(f"Response: {response}")
        time.sleep(1)

def test_whisper_only():
    """Test Whisper speech recognition only"""
    print("\n🎤 Whisper Speech Recognition Test")
    
    try:
        import whisper
        
        # Load model
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        print("✅ Whisper model loaded successfully")
        
        # Test with a sample audio file if available
        test_audio_path = "test_audio.wav"
        if Path(test_audio_path).exists():
            print(f"Testing with {test_audio_path}...")
            result = model.transcribe(test_audio_path)
            print(f"Transcription: {result['text']}")
        else:
            print("No test audio file found. Create 'test_audio.wav' to test transcription.")
            
    except ImportError:
        print("❌ Whisper not installed. Install with: pip install openai-whisper")
    except Exception as e:
        print(f"❌ Error testing Whisper: {str(e)}")

def main():
    """Main entry point"""
    print("INTA AI Assistant Test Suite")
    print("This script tests the INTA AI assistant functionality.")
    
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--whisper-only":
        test_whisper_only()
        return
    
    # Run main test
    test_inta_ai()

if __name__ == "__main__":
    main() 