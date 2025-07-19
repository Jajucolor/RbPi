#!/usr/bin/env python3
"""
Test script for voice command functionality
Simple test to verify speech recognition is working correctly
"""

import sys
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_speech_recognition_import():
    """Test if SpeechRecognition can be imported"""
    try:
        import speech_recognition as sr
        print("✓ SpeechRecognition imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import SpeechRecognition: {e}")
        return False

def test_pyaudio_import():
    """Test if PyAudio can be imported"""
    try:
        import pyaudio
        print("✓ PyAudio imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import PyAudio: {e}")
        return False

def test_microphone_detection():
    """Test microphone detection"""
    try:
        import speech_recognition as sr
        import pyaudio
        
        # List available microphones
        print("Available microphones:")
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"  {index}: {name}")
        
        # Test default microphone
        mic = sr.Microphone()
        print(f"✓ Default microphone initialized: {mic}")
        return True
        
    except Exception as e:
        print(f"✗ Microphone detection failed: {e}")
        return False

def test_speech_recognition_basic():
    """Test basic speech recognition functionality"""
    try:
        import speech_recognition as sr
        
        r = sr.Recognizer()
        mic = sr.Microphone()
        
        print("Testing speech recognition...")
        print("Say something when prompted (you have 5 seconds)")
        
        with mic as source:
            print("Adjusting for ambient noise... Please wait.")
            r.adjust_for_ambient_noise(source, duration=2)
            print(f"Ambient noise level: {r.energy_threshold}")
        
        print("Now speak into the microphone:")
        with mic as source:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("Got audio, processing...")
        
        # Try to recognize speech
        text = r.recognize_google(audio)
        print(f"✓ Speech recognition successful! You said: '{text}'")
        return True
        
    except sr.WaitTimeoutError:
        print("✗ No speech detected within timeout")
        return False
    except sr.UnknownValueError:
        print("✗ Could not understand audio")
        return False
    except sr.RequestError as e:
        print(f"✗ Speech recognition service error: {e}")
        return False
    except Exception as e:
        print(f"✗ Speech recognition test failed: {e}")
        return False

def test_voice_command_manager():
    """Test the VoiceCommandManager class"""
    try:
        from modules.voice_command_manager import VoiceCommandManager
        
        # Create voice manager
        voice_manager = VoiceCommandManager()
        print("✓ VoiceCommandManager created successfully")
        
        # Check status
        status = voice_manager.get_voice_status()
        print(f"✓ Voice command status: {status}")
        
        # Test simulation if real hardware not available
        if status['simulation_mode']:
            print("Running in simulation mode...")
            
            def test_callback():
                print("🎯 Test callback triggered!")
            
            voice_manager.set_capture_callback(test_callback)
            voice_manager.simulate_capture_command()
            print("✓ Simulation test completed")
        
        # Cleanup
        voice_manager.cleanup()
        return True
        
    except Exception as e:
        print(f"✗ VoiceCommandManager test failed: {e}")
        return False

def test_voice_commands_interactive():
    """Interactive test for voice commands"""
    try:
        from modules.voice_command_manager import VoiceCommandManager
        
        print("\n--- Interactive Voice Command Test ---")
        
        # Create callbacks
        capture_count = [0]  # Use list for closure
        
        def on_capture():
            capture_count[0] += 1
            print(f"🎯 Capture command #{capture_count[0]} received!")
        
        def on_shutdown():
            print("🛑 Shutdown command received!")
        
        # Setup voice manager
        voice_manager = VoiceCommandManager()
        voice_manager.set_capture_callback(on_capture)
        voice_manager.set_shutdown_callback(on_shutdown)
        
        status = voice_manager.get_voice_status()
        if status['simulation_mode']:
            print("❌ Cannot run interactive test - hardware not available")
            return False
        
        print(f"Available capture commands: {status['capture_commands']}")
        print(f"Available shutdown commands: {status['shutdown_commands']}")
        
        voice_manager.start_listening()
        
        print("\n🎤 Listening for voice commands...")
        print("Try saying: 'capture', 'analyze', 'take picture', or 'shutdown'")
        print("Press Ctrl+C to stop")
        
        try:
            time.sleep(30)  # Listen for 30 seconds
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        
        voice_manager.cleanup()
        
        print(f"Test completed! Captured {capture_count[0]} voice commands.")
        return True
        
    except Exception as e:
        print(f"✗ Interactive test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Testing voice command integration for assistive glasses...\n")
    
    tests = [
        ("SpeechRecognition Import", test_speech_recognition_import),
        ("PyAudio Import", test_pyaudio_import),
        ("Microphone Detection", test_microphone_detection),
        ("Basic Speech Recognition", test_speech_recognition_basic),
        ("Voice Command Manager", test_voice_command_manager),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- Testing {test_name} ---")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n--- Test Summary ---")
    print(f"Passed: {passed}/{total}")
    
    # Run interactive test if basic tests pass
    if passed >= 4:  # Most tests passed
        print("\n--- Optional Interactive Test ---")
        response = input("Run interactive voice command test? (y/n): ").lower()
        if response == 'y':
            test_voice_commands_interactive()
    
    if passed >= 4:
        print("🎉 Voice commands are working! You can now use voice activation.")
        print("\nAvailable voice commands:")
        print("  Capture: 'capture', 'analyze', 'take picture', 'describe', 'look'")
        print("  Shutdown: 'shutdown', 'quit', 'exit', 'stop'")
        return 0
    else:
        print("❌ Some tests failed. Voice commands may not work properly.")
        print("\nTo install dependencies on Raspberry Pi:")
        print("pip install SpeechRecognition PyAudio")
        print("sudo apt install -y portaudio19-dev python3-pyaudio")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 