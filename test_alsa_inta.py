#!/usr/bin/env python3
"""
Test script for ALSA-optimized INTA AI with low-latency audio
Tests the new Raspberry Pi optimized implementation
"""

import sys
import time
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_config():
    """Load configuration from file"""
    config_file = Path("config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    
    # Return default config
    return {
        "openai": {"api_key": ""},
        "inta": {
            "sample_rate": 8000,
            "chunk_size": 512,
            "vad_aggressiveness": 2,
            "speech_frames_threshold": 3,
            "silence_frames_threshold": 10,
            "realtime_buffer_size": 4096,
            "max_audio_length": 10.0,
            "whisper_model": "tiny"
        }
    }

def test_alsa_availability():
    """Test ALSA availability and configuration"""
    print("=" * 60)
    print("🔧 ALSA Audio System Test")
    print("=" * 60)
    
    try:
        import alsaaudio
        print("✅ ALSA library available")
        
        # List available devices
        print("\n📋 Available ALSA devices:")
        devices = alsaaudio.pcms(alsaaudio.PCM_CAPTURE)
        for i, device in enumerate(devices):
            print(f"  {i}: {device}")
        
        # Test default device
        try:
            device = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK)
            print(f"\n✅ Default capture device: {device.cardname()}")
            
            # Test parameters
            device.setchannels(1)
            device.setrate(8000)
            device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
            device.setperiodsize(512)
            
            print("✅ ALSA parameters set successfully")
            print(f"  Channels: {device.channels()}")
            print(f"  Sample Rate: {device.rate()} Hz")
            print(f"  Format: {device.format()}")
            print(f"  Period Size: {device.periodsize()}")
            
            device.close()
            return True
            
        except Exception as e:
            print(f"❌ Error testing ALSA device: {e}")
            return False
            
    except ImportError:
        print("❌ ALSA library not available")
        print("Install with: sudo apt install python3-alsaaudio")
        return False

def test_vad_availability():
    """Test WebRTC VAD availability"""
    print("\n" + "=" * 60)
    print("🎤 Voice Activity Detection Test")
    print("=" * 60)
    
    try:
        import webrtcvad
        print("✅ WebRTC VAD available")
        
        # Test VAD initialization
        vad = webrtcvad.Vad(2)
        print("✅ VAD initialized with aggressiveness level 2")
        
        # Test with dummy audio
        import numpy as np
        dummy_audio = np.zeros(160, dtype=np.int16).tobytes()  # 10ms at 8kHz
        result = vad.is_speech(dummy_audio, 8000)
        print(f"✅ VAD test completed (dummy audio result: {result})")
        
        return True
        
    except ImportError:
        print("❌ WebRTC VAD not available")
        print("Install with: pip install webrtcvad")
        return False

def test_whisper_optimization():
    """Test Whisper model optimization for Raspberry Pi"""
    print("\n" + "=" * 60)
    print("🤖 Whisper Model Optimization Test")
    print("=" * 60)
    
    try:
        import whisper
        print("✅ Whisper available")
        
        # Test tiny model loading
        print("Loading tiny model (optimized for Raspberry Pi)...")
        start_time = time.time()
        model = whisper.load_model("tiny")
        load_time = time.time() - start_time
        
        print(f"✅ Tiny model loaded in {load_time:.2f} seconds")
        print(f"  Model size: {model.name}")
        
        # Test memory usage
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"  Memory usage: {memory_mb:.1f} MB")
        
        return True
        
    except ImportError:
        print("❌ Whisper not available")
        print("Install with: pip install openai-whisper")
        return False

def test_inta_alsa_integration():
    """Test the complete ALSA-optimized INTA integration"""
    print("\n" + "=" * 60)
    print("🚀 ALSA-Optimized INTA Integration Test")
    print("=" * 60)
    
    try:
        from modules.inta_ai_manager import IntaAIManager
        
        # Load config
        config = load_config()
        
        # Initialize INTA
        print("Initializing ALSA-optimized INTA...")
        inta = IntaAIManager(config)
        
        # Get status
        status = inta.get_status()
        print("\n📊 INTA Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # Test audio initialization
        if status['audio_available']:
            print("\n✅ ALSA audio system ready")
        else:
            print("\n❌ ALSA audio system not available")
            return False
        
        # Test VAD
        if status.get('vad_available', False):
            print("✅ Voice Activity Detection ready")
        else:
            print("⚠️  Voice Activity Detection not available (using fallback)")
        
        # Test Whisper
        if status['whisper_available']:
            print("✅ Whisper speech recognition ready")
        else:
            print("❌ Whisper not available")
            return False
        
        # Test AI backend
        if status['openai_configured']:
            print("✅ OpenAI configured")
        else:
            print("⚠️  OpenAI not configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing INTA integration: {e}")
        return False

def test_low_latency_performance():
    """Test low-latency performance characteristics"""
    print("\n" + "=" * 60)
    print("⚡ Low-Latency Performance Test")
    print("=" * 60)
    
    try:
        from modules.inta_ai_manager import IntaAIManager
        
        config = load_config()
        inta = IntaAIManager(config)
        
        # Test audio buffer processing
        print("Testing audio buffer processing...")
        
        import numpy as np
        
        # Create test audio buffer (1 second of silence)
        test_audio = np.zeros(8000, dtype=np.int16)  # 1 second at 8kHz
        audio_data = test_audio.tobytes()
        
        # Test processing time
        start_time = time.time()
        inta._process_audio_async(audio_data)
        processing_time = time.time() - start_time
        
        print(f"✅ Audio processing test completed in {processing_time:.3f} seconds")
        
        # Test VAD performance
        print("\nTesting VAD performance...")
        vad_times = []
        
        for i in range(10):
            # Create random audio chunks
            test_chunk = np.random.randint(-1000, 1000, 512, dtype=np.int16)
            
            start_time = time.time()
            is_speech = inta._is_speech(test_chunk)
            vad_time = time.time() - start_time
            vad_times.append(vad_time)
        
        avg_vad_time = sum(vad_times) / len(vad_times)
        max_vad_time = max(vad_times)
        
        print(f"✅ VAD performance:")
        print(f"  Average time: {avg_vad_time*1000:.2f} ms")
        print(f"  Maximum time: {max_vad_time*1000:.2f} ms")
        
        # Performance recommendations
        if avg_vad_time < 0.001:  # Less than 1ms
            print("  🟢 Excellent performance - suitable for real-time use")
        elif avg_vad_time < 0.005:  # Less than 5ms
            print("  🟡 Good performance - acceptable for real-time use")
        else:
            print("  🔴 Performance may be too slow for real-time use")
        
        inta.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Error testing performance: {e}")
        return False

def main():
    """Main test function"""
    print("ALSA-Optimized INTA AI Test Suite")
    print("Testing low-latency audio implementation for Raspberry Pi")
    print()
    
    # Run all tests
    tests = [
        ("ALSA Availability", test_alsa_availability),
        ("VAD Availability", test_vad_availability),
        ("Whisper Optimization", test_whisper_optimization),
        ("INTA Integration", test_inta_alsa_integration),
        ("Performance Test", test_low_latency_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! ALSA-optimized INTA is ready to use.")
    elif passed >= total - 1:
        print("⚠️  Most tests passed. Some features may be limited.")
    else:
        print("❌ Multiple tests failed. Please check your installation.")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if not any(name == "ALSA Availability" and result for name, result in results):
        print("  • Install ALSA: sudo apt install python3-alsaaudio")
    if not any(name == "VAD Availability" and result for name, result in results):
        print("  • Install WebRTC VAD: pip install webrtcvad")
    if not any(name == "Whisper Optimization" and result for name, result in results):
        print("  • Install Whisper: pip install openai-whisper")
    
    print("\n🚀 To start using ALSA-optimized INTA:")
    print("  python main.py")

if __name__ == "__main__":
    main() 