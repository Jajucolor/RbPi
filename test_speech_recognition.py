#!/usr/bin/env python3
"""
Test Speech Recognition Implementation
Tests the new speech_recognition library integration
"""

import time
import logging
import json
from modules.inta_ai_manager import IntaAIManager

def test_speech_recognition():
    """Test the new speech recognition implementation"""
    logging.basicConfig(level=logging.INFO)
    
    print("🎤 SPEECH RECOGNITION TEST")
    print("="*50)
    
    # Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found. Creating default config...")
        config = {
            "openai": {
                "api_key": "test-key",
                "model": "gpt-4o-mini",
                "max_tokens": 300,
                "temperature": 0.3
            },
            "inta": {
                "sample_rate": 16000,
                "chunk_size": 1024,
                "whisper_model": "tiny"
            }
        }
    
    # Initialize INTA AI Manager
    print("\n🔧 Initializing INTA AI Manager...")
    inta = IntaAIManager(config)
    
    # Test microphone detection
    print("\n🎤 Testing microphone detection...")
    status = inta.get_status()
    print(f"Speech Recognition Available: {status['speech_recognition_available']}")
    print(f"Microphone Info: {status['microphone_info']}")
    print(f"Whisper Available: {status['whisper_available']}")
    print(f"OpenAI Available: {status['openai_available']}")
    
    # Test listening
    print("\n🎧 Testing listening functionality...")
    if inta.start_listening():
        print("✅ Listening started successfully")
        
        print("\n🗣️  Please speak something (you have 10 seconds)...")
        print("Try saying: 'What time is it?' or 'Tell me a joke'")
        
        # Listen for 10 seconds
        time.sleep(10)
        
        print("\n⏹️  Stopping listening...")
        inta.stop_listening()
        print("✅ Listening stopped")
    else:
        print("❌ Failed to start listening")
    
    # Test command processing
    print("\n🧠 Testing command processing...")
    test_commands = [
        "What time is it?",
        "Tell me a joke",
        "What's the date today?",
        "System status",
        "Hello, how are you?"
    ]
    
    for command in test_commands:
        print(f"\nTesting: '{command}'")
        response = inta.process_command(command)
        print(f"Response: {response}")
        time.sleep(1)
    
    # Test function execution
    print("\n⚙️  Testing function execution...")
    functions = ["time", "date", "joke", "status", "help"]
    
    for func in functions:
        print(f"\nTesting function: {func}")
        response = inta.execute_function(func)
        print(f"Response: {response}")
        time.sleep(0.5)
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    inta.cleanup()
    print("✅ Test complete!")

def test_microphone_listing():
    """Test microphone listing functionality"""
    print("\n📋 MICROPHONE LISTING TEST")
    print("="*50)
    
    try:
        import speech_recognition as sr
        
        # List all available microphones
        print("Available microphones:")
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"  {index}: {name}")
        
        # Test default microphone
        print(f"\nDefault microphone index: {sr.Microphone().device_index}")
        
    except ImportError:
        print("❌ speech_recognition not available")
    except Exception as e:
        print(f"❌ Error listing microphones: {e}")

def test_ambient_noise_adjustment():
    """Test ambient noise adjustment"""
    print("\n🔊 AMBIENT NOISE ADJUSTMENT TEST")
    print("="*50)
    
    try:
        import speech_recognition as sr
        
        # Initialize recognizer and microphone
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        print("Adjusting for ambient noise...")
        print("Please stay quiet for 3 seconds...")
        
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=3)
        
        print(f"Energy threshold set to: {recognizer.energy_threshold}")
        print("✅ Ambient noise adjustment complete")
        
    except ImportError:
        print("❌ speech_recognition not available")
    except Exception as e:
        print(f"❌ Error adjusting ambient noise: {e}")

if __name__ == "__main__":
    print("🎯 Choose test:")
    print("1. Full speech recognition test")
    print("2. Microphone listing test")
    print("3. Ambient noise adjustment test")
    print("4. All tests")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_speech_recognition()
    elif choice == "2":
        test_microphone_listing()
    elif choice == "3":
        test_ambient_noise_adjustment()
    elif choice == "4":
        test_microphone_listing()
        test_ambient_noise_adjustment()
        test_speech_recognition()
    else:
        print("Invalid choice. Running full test...")
        test_speech_recognition() 