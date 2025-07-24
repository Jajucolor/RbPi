#!/usr/bin/env python3
"""
Comprehensive Microphone Debugging Tool
Diagnoses and fixes microphone sensitivity issues for INTA
"""

import sys
import os
import subprocess
import json
import time
import threading
from pathlib import Path

try:
    import pyaudio
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

def check_system_audio():
    """Check system-level audio configuration"""
    print("🔧 SYSTEM AUDIO DIAGNOSIS")
    print("="*50)
    
    # Test arecord (ALSA)
    print("📡 Testing ALSA audio recording...")
    try:
        result = subprocess.run(['arecord', '--list-devices'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ ALSA is working")
            print("Available recording devices:")
            for line in result.stdout.split('\n'):
                if 'card' in line.lower() or 'device' in line.lower():
                    print(f"  🎤 {line.strip()}")
        else:
            print("⚠️  ALSA may have issues")
    except Exception as e:
        print(f"❌ ALSA test failed: {e}")
    
    # Test microphone with arecord
    print("\n🎙️ Testing microphone with arecord...")
    print("This will record 3 seconds of audio - speak loudly!")
    print("Press Enter when ready...")
    input()
    
    try:
        # Record test audio
        subprocess.run([
            'arecord', '-d', '3', '-f', 'cd', '-t', 'wav', 'mic_test.wav'
        ], timeout=10)
        
        # Analyze the recorded file
        if os.path.exists('mic_test.wav'):
            print("✅ Recording successful!")
            
            # Try to play it back
            try:
                print("🔊 Playing back recording...")
                subprocess.run(['aplay', 'mic_test.wav'], timeout=10)
                print("Did you hear your voice clearly? (y/n):")
                playback_ok = input().lower().strip() == 'y'
                
                if playback_ok:
                    print("✅ System audio is working - issue is in Python/PyAudio config")
                else:
                    print("⚠️  System audio needs adjustment")
                    
            except Exception as e:
                print(f"⚠️  Playback failed: {e}")
            
            # Clean up
            os.remove('mic_test.wav')
            return playback_ok
        else:
            print("❌ Recording failed - no file created")
            return False
            
    except Exception as e:
        print(f"❌ arecord test failed: {e}")
        return False

def check_microphone_levels():
    """Check and adjust microphone input levels"""
    print("\n🎚️ MICROPHONE LEVEL DIAGNOSIS")
    print("="*50)
    
    # Check ALSA mixer settings
    print("📊 Checking ALSA mixer levels...")
    try:
        result = subprocess.run(['amixer'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            output = result.stdout.lower()
            
            # Look for microphone controls
            if 'capture' in output:
                print("✅ Found capture controls")
                if '[0%]' in output or 'capture 0' in output:
                    print("⚠️  Microphone level is at 0% - needs adjustment!")
                    print("🔧 Try running: amixer set Capture 80%")
                elif '[100%]' in output:
                    print("✅ Microphone level at maximum")
                else:
                    print("ℹ️  Microphone level set to some value")
            else:
                print("⚠️  No capture controls found")
                
            # Look for microphone boost
            if 'mic boost' in output or 'microphone boost' in output:
                print("✅ Found microphone boost control")
            else:
                print("ℹ️  No microphone boost control found")
                
        else:
            print("⚠️  Could not check mixer levels")
            
    except Exception as e:
        print(f"❌ Mixer check failed: {e}")
    
    # Suggest mixer adjustments
    print("\n🔧 SUGGESTED FIXES:")
    print("Try these commands to boost microphone:")
    print("  amixer set Capture 100%")
    print("  amixer set 'Mic Boost' 100%")
    print("  amixer set 'Microphone' 100%")
    print("  amixer set 'Internal Mic Boost' 100%")

def test_pyaudio_devices():
    """Test PyAudio device selection and configuration"""
    if not AUDIO_AVAILABLE:
        print("❌ PyAudio not available - install with: pip install PyAudio")
        return None
    
    print("\n🐍 PYAUDIO DEVICE DIAGNOSIS")
    print("="*50)
    
    pa = pyaudio.PyAudio()
    
    print("📋 Available PyAudio devices:")
    input_devices = []
    
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            input_devices.append((i, info))
            default = " (DEFAULT)" if i == pa.get_default_input_device_info()['index'] else ""
            print(f"  🎤 {i}: {info['name']}{default}")
            print(f"      Channels: {info['maxInputChannels']}, Rate: {info['defaultSampleRate']}")
    
    if not input_devices:
        print("❌ No input devices found!")
        pa.terminate()
        return None
    
    # Test each device
    print(f"\n🧪 Testing {len(input_devices)} input devices...")
    device_results = {}
    
    for device_id, device_info in input_devices:
        print(f"\n🎤 Testing device {device_id}: {device_info['name']}")
        
        try:
            # Test with different configurations
            configs = [
                (16000, 1024),  # Whisper standard
                (44100, 1024),  # CD quality
                (48000, 1024),  # High quality
            ]
            
            for rate, chunk in configs:
                try:
                    stream = pa.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=rate,
                        input=True,
                        input_device_index=device_id,
                        frames_per_buffer=chunk
                    )
                    
                    print(f"  ✅ {rate}Hz/{chunk} frames: OK")
                    
                    # Quick amplitude test
                    data = stream.read(1024, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    amplitude = np.max(np.abs(audio_data))
                    
                    stream.stop_stream()
                    stream.close()
                    
                    device_results[device_id] = {
                        'name': device_info['name'],
                        'amplitude': amplitude,
                        'working_rate': rate
                    }
                    
                    print(f"    📊 Silent amplitude: {amplitude}")
                    break
                    
                except Exception as e:
                    print(f"  ❌ {rate}Hz: {str(e)[:50]}")
                    continue
                    
        except Exception as e:
            print(f"  ❌ Device failed: {e}")
            continue
    
    pa.terminate()
    return device_results

def test_microphone_sensitivity(device_id=None):
    """Test microphone sensitivity with live audio"""
    if not AUDIO_AVAILABLE:
        print("❌ PyAudio not available")
        return False
    
    print("\n🎙️ LIVE MICROPHONE SENSITIVITY TEST")
    print("="*50)
    
    pa = pyaudio.PyAudio()
    
    try:
        # Use specific device or default
        kwargs = {
            'format': pyaudio.paInt16,
            'channels': 1,
            'rate': 16000,
            'input': True,
            'frames_per_buffer': 1024
        }
        
        if device_id is not None:
            kwargs['input_device_index'] = device_id
            device_info = pa.get_device_info_by_index(device_id)
            print(f"🎤 Using device: {device_info['name']}")
        else:
            print("🎤 Using default input device")
        
        stream = pa.open(**kwargs)
        
        print("\n🗣️  SPEAK LOUDLY INTO THE MICROPHONE!")
        print("Test will run for 10 seconds...")
        print()
        
        max_amplitude = 0
        start_time = time.time()
        
        while time.time() - start_time < 10:
            data = stream.read(1024, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplitude = np.max(np.abs(audio_data))
            max_amplitude = max(max_amplitude, amplitude)
            
            # Visual amplitude bar
            bar_length = int(amplitude / 32768 * 50)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            
            # Color coding
            if amplitude > 1000:
                status = "🟢 GOOD"
            elif amplitude > 100:
                status = "🟡 WEAK"
            else:
                status = "🔴 BAD "
            
            remaining = int(10 - (time.time() - start_time))
            print(f"\r{status} |{bar}| {amplitude:5d} [{remaining}s]", end="", flush=True)
            
        print(f"\n\n📊 FINAL RESULTS:")
        print(f"  📈 Maximum amplitude: {max_amplitude}")
        
        if max_amplitude > 2000:
            print("  🟢 EXCELLENT - Microphone working perfectly!")
            result = "excellent"
        elif max_amplitude > 1000:
            print("  🟢 GOOD - Microphone working well")
            result = "good"
        elif max_amplitude > 100:
            print("  🟡 WEAK - Microphone needs volume boost")
            result = "weak"
        else:
            print("  🔴 FAILED - Microphone not working properly")
            result = "failed"
        
        stream.stop_stream()
        stream.close()
        pa.terminate()
        
        return result
        
    except Exception as e:
        print(f"❌ Sensitivity test failed: {e}")
        pa.terminate()
        return "error"

def fix_configuration():
    """Update configuration files with better audio settings"""
    print("\n⚙️ CONFIGURATION FIXES")
    print("="*50)
    
    config_path = Path("config.json")
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update voice command settings for better sensitivity
            if 'voice_commands' not in config:
                config['voice_commands'] = {}
            
            # More sensitive settings
            config['voice_commands'].update({
                "silence_threshold": 0.005,  # More sensitive (was 0.01)
                "chunk_duration": 1.5,      # Shorter chunks for faster response
                "silence_duration": 0.8,    # Less silence required
            })
            
            # Backup and save
            backup_path = Path("config.json.backup")
            if not backup_path.exists():
                config_path.rename(backup_path)
                print(f"✅ Backed up config to {backup_path}")
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Updated configuration with more sensitive audio settings")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update config: {e}")
            return False
    else:
        print("⚠️  config.json not found - copy from config.example.json")
        return False

def main():
    """Main diagnostic function"""
    print("🎙️ INTA MICROPHONE DIAGNOSTIC TOOL")
    print("="*60)
    print("This tool will help fix microphone sensitivity issues")
    print()
    
    if not AUDIO_AVAILABLE:
        print("❌ PyAudio not installed!")
        print("Install with: pip install PyAudio")
        print("On Raspberry Pi: sudo apt install portaudio19-dev python3-pyaudio")
        return
    
    try:
        # Step 1: System audio check
        system_ok = check_system_audio()
        
        # Step 2: Check mixer levels
        check_microphone_levels()
        
        # Step 3: Test PyAudio devices
        device_results = test_pyaudio_devices()
        
        # Step 4: Interactive device testing
        if device_results:
            print(f"\n🎯 Found {len(device_results)} working devices")
            
            # Test default device first
            print("\n1️⃣ Testing DEFAULT device:")
            default_result = test_microphone_sensitivity()
            
            if default_result in ['excellent', 'good']:
                print("✅ Default device works well!")
            else:
                print("⚠️  Default device has issues, testing others...")
                
                # Test other devices
                for device_id, info in device_results.items():
                    print(f"\n🧪 Testing device {device_id}: {info['name']}")
                    result = test_microphone_sensitivity(device_id)
                    
                    if result in ['excellent', 'good']:
                        print(f"✅ Device {device_id} works well!")
                        print(f"💡 Consider setting this as default:")
                        print(f"   Add 'input_device_index': {device_id} to config")
                        break
        
        # Step 5: Fix configuration
        print("\n5️⃣ Updating configuration...")
        fix_configuration()
        
        # Final recommendations
        print("\n" + "="*60)
        print("🎯 FINAL RECOMMENDATIONS")
        print("="*60)
        print("If microphone is still too quiet:")
        print()
        print("🔧 SYSTEM LEVEL:")
        print("  • Run: amixer set Capture 100%")
        print("  • Run: amixer set 'Mic Boost' 100%")
        print("  • Check USB power (try different ports)")
        print("  • Use a USB hub with external power")
        print()
        print("🐍 SOFTWARE LEVEL:")
        print("  • Updated config.json with better settings")
        print("  • Consider different microphone if hardware is faulty")
        print("  • Use headset microphone for better results")
        print()
        print("🧪 TEST AGAIN:")
        print("  • Run: python3 test_continuous_microphone.py")
        print("  • Look for amplitude > 500 when speaking")
        
    except KeyboardInterrupt:
        print("\n🛑 Diagnostic interrupted")
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")

if __name__ == "__main__":
    main() 