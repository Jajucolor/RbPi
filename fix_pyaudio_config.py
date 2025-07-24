#!/usr/bin/env python3
"""
PyAudio Configuration Fix Script
For when system audio works (arecord) but PyAudio doesn't
"""

import subprocess
import sys
import json
import time
from pathlib import Path

def test_system_audio():
    """Test system-level audio recording"""
    print("🔧 TESTING SYSTEM AUDIO")
    print("="*50)
    
    print("🎤 Testing with arecord (system audio)...")
    print("🗣️  Speak for 3 seconds when recording starts...")
    
    try:
        # Record test
        result = subprocess.run([
            'arecord', '-d', '3', '-f', 'cd', '-t', 'wav', 'system_test.wav'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and Path('system_test.wav').exists():
            print("✅ System recording successful!")
            
            # Play back
            print("🔊 Playing back system recording...")
            subprocess.run(['aplay', 'system_test.wav'], timeout=10)
            
            print("Did you hear your voice clearly? (y/n):")
            response = input().lower().strip()
            
            # Clean up
            Path('system_test.wav').unlink(missing_ok=True)
            
            return response == 'y'
        else:
            print("❌ System recording failed")
            return False
            
    except Exception as e:
        print(f"❌ System audio test failed: {e}")
        return False

def check_pyaudio_installation():
    """Check PyAudio installation and dependencies"""
    print("\n🐍 CHECKING PYAUDIO INSTALLATION")
    print("="*50)
    
    try:
        import pyaudio
        print("✅ PyAudio is installed")
        
        # Check version
        print(f"📦 PyAudio version: {pyaudio.__version__}")
        
        # Test basic functionality
        pa = pyaudio.PyAudio()
        device_count = pa.get_device_count()
        print(f"📋 Found {device_count} audio devices")
        
        # Check default devices
        try:
            default_input = pa.get_default_input_device_info()
            print(f"🎤 Default input: {default_input['name']}")
        except Exception as e:
            print(f"⚠️  No default input device: {e}")
        
        pa.terminate()
        return True
        
    except ImportError:
        print("❌ PyAudio not installed!")
        print("🔧 Install with: pip install PyAudio")
        return False
    except Exception as e:
        print(f"❌ PyAudio error: {e}")
        return False

def check_audio_backend():
    """Check which audio backend PyAudio is using"""
    print("\n🔊 CHECKING AUDIO BACKEND")
    print("="*50)
    
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        
        # Get backend info
        print("📋 PyAudio backend information:")
        print(f"  Host API: {pa.get_host_api_count()} APIs available")
        
        for i in range(pa.get_host_api_count()):
            api_info = pa.get_host_api_info_by_index(i)
            print(f"  {i}: {api_info['name']} (default: {api_info['type'] == pa.get_default_host_api_info()['type']})")
        
        # Check which backend is being used
        default_api = pa.get_default_host_api_info()
        print(f"🎯 Using backend: {default_api['name']}")
        
        pa.terminate()
        return True
        
    except Exception as e:
        print(f"❌ Backend check failed: {e}")
        return False

def test_pyaudio_devices_individually():
    """Test each PyAudio device with different configurations"""
    print("\n🧪 TESTING PYAUDIO DEVICES")
    print("="*50)
    
    try:
        import pyaudio
        import numpy as np
        
        pa = pyaudio.PyAudio()
        
        working_devices = []
        
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"\n🎤 Device {i}: {info['name']}")
                print(f"   Channels: {info['maxInputChannels']}, Rate: {info['defaultSampleRate']}")
                
                # Test different configurations
                configs = [
                    (16000, 1024, "Whisper standard"),
                    (44100, 1024, "CD quality"),
                    (48000, 1024, "High quality"),
                    (8000, 512, "Low quality"),
                ]
                
                device_working = False
                
                for rate, chunk, desc in configs:
                    try:
                        print(f"   Testing {desc} ({rate}Hz)...")
                        
                        stream = pa.open(
                            format=pyaudio.paInt16,
                            channels=1,
                            rate=rate,
                            input=True,
                            input_device_index=i,
                            frames_per_buffer=chunk
                        )
                        
                        # Quick test
                        data = stream.read(1024, exception_on_overflow=False)
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        amplitude = np.max(np.abs(audio_data))
                        
                        stream.stop_stream()
                        stream.close()
                        
                        print(f"     📊 Amplitude: {amplitude}")
                        
                        if amplitude > 50:
                            print(f"     ✅ WORKING - {desc} configuration works!")
                            working_devices.append({
                                'device_id': i,
                                'name': info['name'],
                                'rate': rate,
                                'chunk': chunk,
                                'amplitude': amplitude
                            })
                            device_working = True
                            break
                        else:
                            print(f"     ❌ Weak signal")
                            
                    except Exception as e:
                        print(f"     ❌ Failed: {str(e)[:50]}")
                        continue
                
                if not device_working:
                    print(f"   ❌ Device {i} failed all configurations")
        
        pa.terminate()
        return working_devices
        
    except Exception as e:
        print(f"❌ Device testing failed: {e}")
        return []

def fix_pyaudio_configuration():
    """Fix PyAudio configuration issues"""
    print("\n⚙️ FIXING PYAUDIO CONFIGURATION")
    print("="*50)
    
    # Test system audio first
    if not test_system_audio():
        print("❌ System audio not working - this script won't help")
        return False
    
    # Check PyAudio installation
    if not check_pyaudio_installation():
        print("❌ PyAudio not properly installed")
        return False
    
    # Check audio backend
    check_audio_backend()
    
    # Test all devices
    working_devices = test_pyaudio_devices_individually()
    
    if working_devices:
        print(f"\n✅ Found {len(working_devices)} working PyAudio configurations!")
        
        # Find best device
        best_device = max(working_devices, key=lambda x: x['amplitude'])
        
        print(f"\n🏆 BEST CONFIGURATION:")
        print(f"  🎤 Device: {best_device['device_id']} - {best_device['name']}")
        print(f"  📊 Amplitude: {best_device['amplitude']}")
        print(f"  🎵 Rate: {best_device['rate']}Hz")
        print(f"  📦 Chunk: {best_device['chunk']}")
        
        # Create optimized config
        create_optimized_config(best_device)
        
        return True
    else:
        print("\n❌ No working PyAudio configurations found")
        print("\n🔧 TROUBLESHOOTING STEPS:")
        print("1. Reinstall PyAudio:")
        print("   pip uninstall PyAudio")
        print("   pip install PyAudio")
        print("2. Install system dependencies:")
        print("   sudo apt install portaudio19-dev python3-pyaudio")
        print("3. Try different audio backend:")
        print("   export PULSEAUDIO=1  # or try ALSA")
        print("4. Check audio permissions:")
        print("   sudo usermod -a -G audio $USER")
        
        return False

def create_optimized_config(best_device):
    """Create optimized configuration file"""
    print("\n📄 CREATING OPTIMIZED CONFIGURATION")
    print("="*50)
    
    config = {
        "voice_commands": {
            "model_size": "base",
            "language": "en",
            "chunk_duration": 1.5,
            "silence_threshold": 0.005,
            "silence_duration": 0.8,
            "input_device_index": best_device['device_id'],
            "sample_rate": best_device['rate'],
            "chunk_size": best_device['chunk']
        }
    }
    
    # Save as test config
    with open("config_pyaudio_fixed.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("✅ Created config_pyaudio_fixed.json")
    print("📋 Configuration:")
    for key, value in config['voice_commands'].items():
        print(f"  {key}: {value}")
    
    print(f"\n🚀 TO USE THIS CONFIG:")
    print("  cp config_pyaudio_fixed.json config.json")
    print("  python3 test_continuous_microphone.py")

def test_fixed_configuration():
    """Test the fixed configuration"""
    print("\n🧪 TESTING FIXED CONFIGURATION")
    print("="*50)
    
    config_path = Path("config_pyaudio_fixed.json")
    if not config_path.exists():
        print("❌ Fixed configuration not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        voice_config = config.get('voice_commands', {})
        device_id = voice_config.get('input_device_index')
        
        if device_id is None:
            print("❌ No device ID in configuration")
            return False
        
        # Test the specific device
        import pyaudio
        import numpy as np
        
        pa = pyaudio.PyAudio()
        
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=voice_config.get('sample_rate', 16000),
                input=True,
                input_device_index=device_id,
                frames_per_buffer=voice_config.get('chunk_size', 1024)
            )
            
            print("🎤 Testing fixed configuration...")
            print("🗣️  Speak for 3 seconds!")
            
            max_amplitude = 0
            for i in range(30):  # 3 seconds
                data = stream.read(1024, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                amplitude = np.max(np.abs(audio_data))
                max_amplitude = max(max_amplitude, amplitude)
                
                # Progress bar
                bar = "█" * (i // 3) + "░" * (10 - i // 3)
                print(f"\r[{bar}] {amplitude:5d}", end="", flush=True)
            
            print(f"\n\n📊 Final amplitude: {max_amplitude}")
            
            if max_amplitude > 500:
                print("🟢 EXCELLENT - Configuration fixed!")
                return True
            elif max_amplitude > 100:
                print("🟡 GOOD - Much better than before")
                return True
            else:
                print("🔴 Still weak - may need hardware check")
                return False
            
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main function"""
    print("🔧 PYAUDIO CONFIGURATION FIX")
    print("="*60)
    print("For when system audio works but PyAudio doesn't")
    print()
    
    try:
        # Step 1: Verify system audio works
        print("1️⃣ Verifying system audio...")
        if not test_system_audio():
            print("❌ System audio not working - this is a different problem")
            return
        
        # Step 2: Fix PyAudio configuration
        print("\n2️⃣ Fixing PyAudio configuration...")
        if fix_pyaudio_configuration():
            print("\n✅ PyAudio configuration fixed!")
            
            # Step 3: Test the fix
            print("\n3️⃣ Testing fixed configuration...")
            if test_fixed_configuration():
                print("\n🎉 SUCCESS! PyAudio is now working properly")
                print("\n🚀 Next steps:")
                print("  • cp config_pyaudio_fixed.json config.json")
                print("  • python3 test_continuous_microphone.py")
                print("  • python3 main.py")
            else:
                print("\n⚠️  Configuration created but may need adjustment")
        else:
            print("\n❌ Could not fix PyAudio configuration")
            print("🔧 Try reinstalling PyAudio and system dependencies")
        
    except KeyboardInterrupt:
        print("\n🛑 Fix interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 