#!/usr/bin/env python3
"""
EMERGENCY Microphone Fix Script
For critically low microphone amplitude (< 50)
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def print_section(title):
    """Print a clearly visible section header"""
    print(f"\n{'='*60}")
    print(f"🚨 {title}")
    print('='*60)

def run_cmd_verbose(cmd, description):
    """Run command with full output for debugging"""
    print(f"\n🔧 {description}")
    print(f"💻 Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        print(f"📤 Return code: {result.returncode}")
        if result.stdout:
            print(f"📄 Output:\n{result.stdout}")
        if result.stderr:
            print(f"⚠️  Errors:\n{result.stderr}")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False, "", str(e)

def emergency_audio_reset():
    """Complete audio system reset"""
    print_section("EMERGENCY AUDIO SYSTEM RESET")
    
    commands = [
        ("sudo fuser -v /dev/snd/*", "Check what's using audio devices"),
        ("sudo pkill -f pulseaudio", "Kill all PulseAudio processes"),
        ("sudo pkill -f pipewire", "Kill PipeWire processes (if present)"),
        ("sleep 3", "Wait for processes to stop"),
        ("sudo modprobe -r snd_usb_audio", "Unload USB audio driver"),
        ("sleep 2", "Wait for driver unload"),
        ("sudo modprobe snd_usb_audio", "Reload USB audio driver"),
        ("sleep 2", "Wait for driver reload"),
        ("pulseaudio --start", "Restart PulseAudio"),
    ]
    
    for cmd, desc in commands:
        success, stdout, stderr = run_cmd_verbose(cmd, desc)
        time.sleep(1)
    
    print("✅ Audio system reset complete")

def check_hardware_detection():
    """Check if microphone hardware is detected"""
    print_section("HARDWARE DETECTION CHECK")
    
    commands = [
        ("lsusb | grep -i audio", "Check USB audio devices"),
        ("cat /proc/asound/cards", "Check ALSA sound cards"),
        ("arecord -l", "List recording devices"),
        ("pacmd list-sources", "List PulseAudio sources"),
    ]
    
    devices_found = 0
    for cmd, desc in commands:
        success, stdout, stderr = run_cmd_verbose(cmd, desc)
        if success and stdout.strip():
            devices_found += 1
    
    if devices_found == 0:
        print("🚨 CRITICAL: No audio devices detected!")
        print("🔧 Try:")
        print("  • Unplug and reconnect USB microphone")
        print("  • Try different USB port")
        print("  • Check if microphone works on another computer")
        return False
    else:
        print(f"✅ Found {devices_found} audio interfaces")
        return True

def fix_all_audio_levels():
    """Set ALL possible audio controls to maximum"""
    print_section("MAXIMIZING ALL AUDIO LEVELS")
    
    # Get all mixer controls
    success, stdout, stderr = run_cmd_verbose("amixer controls", "List all mixer controls")
    
    if success:
        controls = []
        for line in stdout.split('\n'):
            if 'name=' in line.lower():
                # Extract control name
                start = line.find("name='") + 6
                end = line.find("'", start)
                if start > 5 and end > start:
                    control_name = line[start:end]
                    controls.append(control_name)
        
        print(f"📋 Found {len(controls)} mixer controls")
        
        # Try to set all relevant controls to maximum
        audio_controls = [
            'Master', 'PCM', 'Capture', 'Mic', 'Microphone', 'Mic Boost',
            'Internal Mic', 'Internal Mic Boost', 'Front Mic', 'Front Mic Boost',
            'Rear Mic', 'Rear Mic Boost', 'Input Source', 'Capture Source'
        ]
        
        for control in controls:
            for audio_control in audio_controls:
                if audio_control.lower() in control.lower():
                    # Try different commands
                    commands = [
                        f"amixer set '{control}' 100%",
                        f"amixer set '{control}' unmute",
                        f"amixer set '{control}' cap",
                    ]
                    
                    for cmd in commands:
                        success, stdout, stderr = run_cmd_verbose(cmd, f"Setting {control}")
                        if success:
                            break
    
    # Also try common direct commands
    direct_commands = [
        "amixer set Master 100%",
        "amixer set PCM 100%",
        "amixer set Capture 100%",
        "amixer set Capture unmute",
        "amixer set Capture cap",
        "amixer set 'Mic Boost' 100%",
        "amixer set Microphone 100%",
        "amixer set 'Auto-Mute Mode' Disabled",
    ]
    
    for cmd in direct_commands:
        run_cmd_verbose(cmd, f"Direct command: {cmd}")

def test_raw_audio_devices():
    """Test each audio device directly"""
    print_section("DIRECT DEVICE TESTING")
    
    try:
        import pyaudio
        import numpy as np
        
        pa = pyaudio.PyAudio()
        print(f"📋 Testing {pa.get_device_count()} audio devices:")
        
        best_device = None
        best_amplitude = 0
        
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"\n🎤 Device {i}: {info['name']}")
                print(f"   Channels: {info['maxInputChannels']}, Rate: {info['defaultSampleRate']}")
                
                try:
                    # Try to open stream
                    stream = pa.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        input_device_index=i,
                        frames_per_buffer=1024
                    )
                    
                    print("   🗣️  SPEAK NOW for 3 seconds!")
                    max_amp = 0
                    
                    for _ in range(int(16000/1024 * 3)):  # 3 seconds
                        try:
                            data = stream.read(1024, exception_on_overflow=False)
                            audio_data = np.frombuffer(data, dtype=np.int16)
                            amplitude = np.max(np.abs(audio_data))
                            max_amp = max(max_amp, amplitude)
                            print(".", end="", flush=True)
                        except:
                            break
                    
                    stream.stop_stream()
                    stream.close()
                    
                    print(f"\n   📊 Max amplitude: {max_amp}")
                    
                    if max_amp > best_amplitude:
                        best_amplitude = max_amp
                        best_device = i
                    
                    if max_amp > 100:
                        print(f"   ✅ WORKING - Device {i} has good signal!")
                    else:
                        print(f"   ❌ WEAK - Device {i} has poor signal")
                        
                except Exception as e:
                    print(f"   ❌ Failed to test device {i}: {e}")
        
        pa.terminate()
        
        if best_device is not None:
            print(f"\n🏆 BEST DEVICE: {best_device} with amplitude {best_amplitude}")
            return best_device, best_amplitude
        else:
            print("\n🚨 NO WORKING DEVICES FOUND!")
            return None, 0
            
    except ImportError:
        print("❌ PyAudio not available for device testing")
        return None, 0

def check_audio_processes():
    """Check for conflicting audio processes"""
    print_section("AUDIO PROCESS CHECK")
    
    commands = [
        ("ps aux | grep -E '(pulse|pipewire|jack|alsa)' | grep -v grep", "Audio processes"),
        ("lsof /dev/snd/*", "Processes using sound devices"),
        ("sudo fuser -v /dev/snd/*", "Detailed sound device usage"),
    ]
    
    for cmd, desc in commands:
        run_cmd_verbose(cmd, desc)

def create_test_config():
    """Create a test configuration with specific device"""
    print_section("CREATING TEST CONFIGURATION")
    
    best_device, amplitude = test_raw_audio_devices()
    
    if best_device is not None and amplitude > 50:
        config = {
            "voice_commands": {
                "model_size": "base",
                "language": "en", 
                "chunk_duration": 1.0,
                "silence_threshold": 0.001,  # Very sensitive
                "silence_duration": 0.5,
                "input_device_index": best_device  # Use best device
            }
        }
        
        # Save test config
        import json
        with open("config_test.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Created config_test.json with device {best_device}")
        print(f"📊 Expected amplitude: {amplitude}")
        return True
    else:
        print("❌ No suitable device found for configuration")
        return False

def main():
    """Emergency diagnostic main function"""
    print("🚨 EMERGENCY MICROPHONE DIAGNOSTIC")
    print("="*60)
    print("For CRITICALLY LOW amplitude (< 50)")
    print("This will perform aggressive system-level fixes")
    print()
    
    input("Press Enter to start emergency diagnosis... ")
    
    try:
        # Step 1: Check hardware detection
        hardware_ok = check_hardware_detection()
        
        if not hardware_ok:
            print("\n🚨 HARDWARE ISSUE DETECTED!")
            print("🔧 IMMEDIATE ACTIONS:")
            print("  1. Unplug USB microphone")
            print("  2. Wait 10 seconds") 
            print("  3. Plug into different USB port")
            print("  4. Run this script again")
            return
        
        # Step 2: Check for conflicting processes
        check_audio_processes()
        
        # Step 3: Emergency audio reset
        emergency_audio_reset()
        
        # Step 4: Fix all audio levels
        fix_all_audio_levels()
        
        # Step 5: Test all devices
        print("\n" + "="*60)
        print("🧪 TESTING ALL DEVICES AFTER FIXES")
        print("="*60)
        
        best_device, best_amplitude = test_raw_audio_devices()
        
        # Results
        print("\n" + "="*60)
        print("📊 EMERGENCY DIAGNOSTIC RESULTS")
        print("="*60)
        
        if best_amplitude > 500:
            print("🟢 SUCCESS! Microphone is now working")
            print(f"📈 Best amplitude: {best_amplitude}")
            print(f"🎤 Best device: {best_device}")
            create_test_config()
        elif best_amplitude > 100:
            print("🟡 IMPROVED but still weak")
            print(f"📈 Best amplitude: {best_amplitude}")
            print("🔧 Try different microphone or USB port")
        else:
            print("🔴 STILL CRITICAL - Hardware issue likely")
            print(f"📈 Best amplitude: {best_amplitude}")
            print()
            print("🚨 HARDWARE TROUBLESHOOTING:")
            print("  • Try a different microphone")
            print("  • Test microphone on another computer")
            print("  • Check USB cable integrity")
            print("  • Try powered USB hub")
            print("  • Consider built-in microphone if available")
        
        print("\n🚀 NEXT STEPS:")
        if best_amplitude > 100:
            print("  • Test: python3 test_continuous_microphone.py")
            print("  • If config_test.json was created, try: cp config_test.json config.json")
        print("  • Check hardware connections")
        print("  • Restart system if needed")
        
    except KeyboardInterrupt:
        print("\n🛑 Emergency diagnostic interrupted")
    except Exception as e:
        print(f"\n❌ Emergency diagnostic error: {e}")

if __name__ == "__main__":
    main() 