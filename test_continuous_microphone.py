#!/usr/bin/env python3
"""
Test script for INTA's continuously active microphone
Verifies that the microphone stream remains active and responsive
"""

import sys
import logging
import time
import threading
from modules.voice_command_manager import VoiceCommandManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_continuous_microphone():
    """Test the continuously active microphone functionality"""
    print("\n" + "="*70)
    print("🎙️ INTA Continuous Microphone Test")
    print("="*70)
    print("This test verifies that INTA's microphone remains constantly active")
    print("and responds to voice input without wake words.")
    print()
    
    # Create voice command manager
    voice_manager = VoiceCommandManager()
    
    print("📋 System Status:")
    status = voice_manager.get_microphone_status()
    for key, value in status.items():
        icon = "✅" if value else "❌"
        print(f"  {icon} {key}: {value}")
    
    if not status.get('audio_interface_available') or not status.get('whisper_model_loaded'):
        print("\n❌ Cannot run test - missing required components")
        return False
    
    # Test callbacks
    test_results = {
        'capture_detected': False,
        'conversation_detected': False,
        'shutdown_detected': False
    }
    
    def on_capture():
        print("🎯 CAPTURE command detected!")
        test_results['capture_detected'] = True
    
    def on_shutdown():
        print("🛑 SHUTDOWN command detected!")
        test_results['shutdown_detected'] = True
        voice_manager.stop_listening()
    
    def on_conversation(text):
        print(f"💬 CONVERSATION detected: '{text}'")
        test_results['conversation_detected'] = True
    
    # Set up callbacks
    voice_manager.set_capture_callback(on_capture)
    voice_manager.set_shutdown_callback(on_shutdown)
    voice_manager.set_conversation_callback(on_conversation)
    
    print("\n🎙️ Starting continuous microphone...")
    voice_manager.start_listening()
    
    # Wait for initialization
    time.sleep(2)
    
    print("\n" + "="*70)
    print("🎤 MICROPHONE IS NOW CONSTANTLY ACTIVE")
    print("="*70)
    print("The microphone is listening continuously. Try saying:")
    print()
    print("📷 For vision analysis:")
    print("  • 'Take a picture'")
    print("  • 'Capture image'") 
    print("  • 'Analyze surroundings'")
    print()
    print("💬 For natural conversation:")
    print("  • 'Hello, how are you?'")
    print("  • 'What can you help me with?'")
    print("  • 'I'm feeling nervous today'")
    print()
    print("🛑 To stop the test:")
    print("  • 'Shutdown'")
    print("  • 'Quit'")
    print("  • Press Ctrl+C")
    print()
    print("⏱️ Test will run for 60 seconds or until you say 'shutdown'")
    print("="*70)
    
    try:
        # Monitor for 60 seconds
        start_time = time.time()
        while voice_manager.listening and (time.time() - start_time) < 60:
            time.sleep(0.5)
            
            # Show periodic status
            if int(time.time() - start_time) % 10 == 0:
                elapsed = int(time.time() - start_time)
                remaining = 60 - elapsed
                print(f"⏰ {remaining} seconds remaining - microphone still active")
                time.sleep(1)  # Prevent multiple prints in same second
    
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    
    finally:
        print("\n🎙️ Stopping continuous microphone...")
        voice_manager.cleanup()
        
        # Results summary
        print("\n" + "="*70)
        print("📊 TEST RESULTS SUMMARY")
        print("="*70)
        
        if test_results['capture_detected']:
            print("✅ Capture commands: WORKING")
        else:
            print("❌ Capture commands: NOT DETECTED")
            
        if test_results['conversation_detected']:
            print("✅ Conversation input: WORKING")
        else:
            print("❌ Conversation input: NOT DETECTED")
            
        if test_results['shutdown_detected']:
            print("✅ Shutdown commands: WORKING")
        else:
            print("⚠️  Shutdown commands: NOT TESTED")
        
        overall_success = any(test_results.values())
        if overall_success:
            print("\n🎉 CONTINUOUS MICROPHONE TEST: SUCCESSFUL")
            print("INTA's always-active microphone is working properly!")
        else:
            print("\n❌ CONTINUOUS MICROPHONE TEST: FAILED")
            print("Check microphone connection and audio settings.")
        
        print("\n💡 Tips for better performance:")
        print("  • Use headphones to prevent audio feedback")
        print("  • Speak clearly within 2 feet of microphone")
        print("  • Ensure microphone has adequate USB power")
        print("  • Run in quiet environment for best recognition")
        
        return overall_success

def test_microphone_stream():
    """Test the raw microphone stream functionality"""
    print("\n" + "="*70)
    print("🎙️ Raw Microphone Stream Test") 
    print("="*70)
    
    try:
        import pyaudio
        import numpy as np
        
        # Initialize PyAudio
        pa = pyaudio.PyAudio()
        
        print("📋 Available audio devices:")
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  🎤 {i}: {info['name']} (inputs: {info['maxInputChannels']})")
        
        # Test continuous stream
        print("\n🎙️ Testing continuous audio stream...")
        
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        print("📡 Stream opened - recording for 5 seconds...")
        print("🗣️  Speak now to test audio input levels!")
        
        max_amplitude = 0
        for i in range(int(16000 / 1024 * 5)):  # 5 seconds
            data = stream.read(1024, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplitude = np.max(np.abs(audio_data))
            max_amplitude = max(max_amplitude, amplitude)
            
            # Visual amplitude indicator
            bar_length = int(amplitude / 32768 * 50)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            print(f"\r🎵 Audio Level: |{bar}| {amplitude:5d}", end="", flush=True)
            
        print(f"\n\n📊 Test Results:")
        print(f"  📈 Maximum amplitude: {max_amplitude}")
        
        if max_amplitude > 1000:
            print("  ✅ Audio input: STRONG SIGNAL")
        elif max_amplitude > 100:
            print("  ⚠️  Audio input: WEAK SIGNAL - speak louder or move closer")
        else:
            print("  ❌ Audio input: NO SIGNAL - check microphone connection")
        
        stream.stop_stream()
        stream.close()
        pa.terminate()
        
        return max_amplitude > 100
        
    except ImportError:
        print("❌ PyAudio not available - cannot test raw microphone stream")
        return False
    except Exception as e:
        print(f"❌ Microphone stream test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🤖 INTA Continuous Microphone Test Suite")
    print("Testing constantly active microphone functionality")
    print("="*70)
    
    tests = [
        ("Raw Microphone Stream", test_microphone_stream),
        ("Continuous Voice Recognition", test_continuous_microphone),
    ]
    
    results = {}
    
    try:
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 50)
            results[test_name] = test_func()
            
            if results[test_name]:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        
        # Final summary
        print("\n" + "="*70)
        print("🏁 FINAL TEST SUMMARY")
        print("="*70)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {test_name}: {status}")
        
        print(f"\n📊 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - INTA's continuous microphone is ready!")
            print("\n💡 You can now run: python3 main.py")
            print("INTA will start with constantly active microphone.")
        else:
            print("⚠️  SOME TESTS FAILED - check troubleshooting guide")
            print("\n🔧 Troubleshooting:")
            print("  • Ensure USB microphone is connected")
            print("  • Check audio permissions: sudo usermod -a -G audio $USER")
            print("  • Test with: arecord -d 3 test.wav && aplay test.wav")
            print("  • See SETUP.md troubleshooting section")
    
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted")
    except Exception as e:
        print(f"❌ Error in test suite: {e}")

if __name__ == "__main__":
    main() 