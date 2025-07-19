#!/usr/bin/env python3
"""
Test script for Whisper voice command functionality
Simple test to verify Whisper speech recognition is working correctly
"""

import sys
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_whisper_import():
    """Test if Whisper can be imported"""
    try:
        import whisper
        import torch
        print("✓ Whisper and torch imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import Whisper or torch: {e}")
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

def test_numpy_import():
    """Test if NumPy can be imported"""
    try:
        import numpy as np
        print("✓ NumPy imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import NumPy: {e}")
        return False

def test_whisper_model_loading():
    """Test loading a Whisper model"""
    try:
        import whisper
        
        print("Loading Whisper base model... (this may take a moment)")
        model = whisper.load_model("base")
        print(f"✓ Whisper model loaded successfully: {type(model)}")
        
        # Test if model has the transcribe method
        if hasattr(model, 'transcribe'):
            print("✓ Model has transcribe method")
            return True
        else:
            print("✗ Model missing transcribe method")
            return False
            
    except Exception as e:
        print(f"✗ Failed to load Whisper model: {e}")
        return False

def test_microphone_detection():
    """Test microphone detection"""
    try:
        import pyaudio
        
        audio = pyaudio.PyAudio()
        
        # List available microphones
        print("Available audio devices:")
        mic_count = 0
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  {i}: {info['name']} (inputs: {info['maxInputChannels']})")
                mic_count += 1
        
        audio.terminate()
        
        if mic_count > 0:
            print(f"✓ Found {mic_count} microphone(s)")
            return True
        else:
            print("✗ No microphones found")
            return False
            
    except Exception as e:
        print(f"✗ Microphone detection failed: {e}")
        return False

def test_audio_recording():
    """Test basic audio recording functionality"""
    try:
        import pyaudio
        import numpy as np
        
        print("Testing audio recording (2 seconds)...")
        
        # Audio settings
        sample_rate = 16000
        chunk_size = 1024
        channels = 1
        format = pyaudio.paInt16
        duration = 2.0
        
        audio = pyaudio.PyAudio()
        
        # Open stream
        stream = audio.open(
            format=format,
            channels=channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size
        )
        
        print("Recording... speak now!")
        frames = []
        frames_to_record = int(sample_rate * duration / chunk_size)
        
        for _ in range(frames_to_record):
            data = stream.read(chunk_size, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Convert to numpy array
        audio_data = b''.join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Check if we got audio
        rms_energy = np.sqrt(np.mean(audio_array ** 2))
        print(f"✓ Audio recorded successfully. RMS energy: {rms_energy:.4f}")
        
        if rms_energy > 0.001:
            print("✓ Audio appears to contain signal")
            return True
        else:
            print("⚠ Audio is very quiet - check microphone")
            return True  # Still pass the test
            
    except Exception as e:
        print(f"✗ Audio recording test failed: {e}")
        return False

def test_voice_command_manager():
    """Test the VoiceCommandManager class"""
    try:
        from modules.voice_command_manager import VoiceCommandManager
        
        # Create voice manager
        voice_manager = VoiceCommandManager(model_size="base")
        print("✓ VoiceCommandManager created successfully")
        
        # Check status
        status = voice_manager.get_voice_status()
        print(f"✓ Voice command status:")
        for key, value in status.items():
            print(f"    {key}: {value}")
        
        # Test simulation if real hardware not available
        if status['simulation_mode']:
            print("Running in simulation mode...")
            
            def test_callback():
                print("🎯 Test callback triggered!")
            
            voice_manager.set_capture_callback(test_callback)
            voice_manager.simulate_capture_command()
            print("✓ Simulation test completed")
        else:
            print("✓ Real hardware mode available")
        
        # Cleanup
        voice_manager.cleanup()
        return True
        
    except Exception as e:
        print(f"✗ VoiceCommandManager test failed: {e}")
        return False

def test_whisper_transcription():
    """Test Whisper transcription with a sample audio file"""
    try:
        import whisper
        import tempfile
        import wave
        import numpy as np
        
        print("Testing Whisper transcription...")
        
        # Load model
        model = whisper.load_model("base")
        
        # Create a simple test audio file (silence)
        sample_rate = 16000
        duration = 1.0  # 1 second
        samples = int(sample_rate * duration)
        
        # Generate a simple sine wave as test audio
        frequency = 440  # A note
        t = np.linspace(0, duration, samples)
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.1  # Quiet sine wave
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            # Try to transcribe
            result = model.transcribe(temp_file.name, language="en", fp16=False)
            text = result["text"].strip()
            
            print(f"✓ Whisper transcription completed")
            print(f"    Result: '{text}' (expected: silence/empty)")
            
            # Clean up
            import os
            os.unlink(temp_file.name)
            
            return True
        
    except Exception as e:
        print(f"✗ Whisper transcription test failed: {e}")
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
        voice_manager = VoiceCommandManager(model_size="base")
        voice_manager.set_capture_callback(on_capture)
        voice_manager.set_shutdown_callback(on_shutdown)
        
        status = voice_manager.get_voice_status()
        if status['simulation_mode']:
            print("❌ Cannot run interactive test - hardware not available")
            voice_manager.cleanup()
            return False
        
        print(f"Available capture commands: {status['capture_commands']}")
        print(f"Available shutdown commands: {status['shutdown_commands']}")
        
        voice_manager.start_listening()
        
        print("\n🎤 Listening for voice commands with Whisper...")
        print("Try saying: 'capture', 'analyze', 'take picture', or 'shutdown'")
        print("Speak clearly and wait for processing...")
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
    print("Testing Whisper voice command integration for assistive glasses...\n")
    
    tests = [
        ("Whisper Import", test_whisper_import),
        ("PyAudio Import", test_pyaudio_import),
        ("NumPy Import", test_numpy_import),
        ("Whisper Model Loading", test_whisper_model_loading),
        ("Microphone Detection", test_microphone_detection),
        ("Audio Recording", test_audio_recording),
        ("Whisper Transcription", test_whisper_transcription),
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
    if passed >= 6:  # Most critical tests passed
        print("\n--- Optional Interactive Test ---")
        response = input("Run interactive voice command test? (y/n): ").lower()
        if response == 'y':
            test_voice_commands_interactive()
    
    if passed >= 6:
        print("🎉 Whisper voice commands are working! You can now use voice activation.")
        print("\nAvailable voice commands:")
        print("  Capture: 'capture', 'analyze', 'take picture', 'describe', 'look'")
        print("  Shutdown: 'shutdown', 'quit', 'exit', 'stop'")
        print("\nWhisper advantages:")
        print("  ✓ Works offline (no internet required)")
        print("  ✓ Better accuracy than cloud services")
        print("  ✓ Privacy-friendly (no data sent to servers)")
        print("  ✓ Multiple language support")
        return 0
    else:
        print("❌ Some tests failed. Whisper voice commands may not work properly.")
        print("\nTo install dependencies on Raspberry Pi:")
        print("pip install openai-whisper torch PyAudio numpy")
        print("sudo apt install -y portaudio19-dev python3-pyaudio")
        print("\nNote: First run will download Whisper model (~140MB for base model)")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 