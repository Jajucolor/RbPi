#!/usr/bin/env python3
"""
Quick Microphone Fix Script
Automatically applies common fixes for low microphone sensitivity
"""

import subprocess
import sys
import json
from pathlib import Path

def run_command(cmd, description):
    """Run a system command and report results"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"  ✅ Success")
            if result.stdout.strip():
                print(f"  📄 Output: {result.stdout.strip()}")
            return True
        else:
            print(f"  ⚠️  Warning: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def fix_alsa_levels():
    """Fix ALSA mixer levels for better microphone sensitivity"""
    print("\n🎚️ FIXING ALSA MICROPHONE LEVELS")
    print("="*50)
    
    commands = [
        ("amixer set Capture 100%", "Setting capture volume to 100%"),
        ("amixer set 'Mic Boost' 100%", "Setting microphone boost to 100%"),
        ("amixer set 'Microphone' 100%", "Setting microphone volume to 100%"),
        ("amixer set 'Internal Mic Boost' 100%", "Setting internal mic boost to 100%"),
        ("amixer set 'Front Mic Boost' 100%", "Setting front mic boost to 100%"),
        ("amixer set 'Rear Mic Boost' 100%", "Setting rear mic boost to 100%"),
    ]
    
    success_count = 0
    for cmd, desc in commands:
        if run_command(cmd, desc):
            success_count += 1
    
    print(f"\n📊 Applied {success_count}/{len(commands)} mixer fixes")
    return success_count > 0

def check_audio_permissions():
    """Check and fix audio group permissions"""
    print("\n👥 CHECKING AUDIO PERMISSIONS")
    print("="*50)
    
    # Check if user is in audio group
    result = subprocess.run("groups", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        groups = result.stdout.strip()
        if 'audio' in groups:
            print("✅ User is in audio group")
            return True
        else:
            print("⚠️  User not in audio group")
            print("🔧 Adding user to audio group...")
            
            # Try to add user to audio group
            username = subprocess.run("whoami", shell=True, capture_output=True, text=True).stdout.strip()
            cmd = f"sudo usermod -a -G audio {username}"
            
            if run_command(cmd, "Adding user to audio group"):
                print("✅ User added to audio group")
                print("⚠️  You may need to logout and login again for changes to take effect")
                return True
            else:
                print("❌ Failed to add user to audio group")
                return False
    else:
        print("❌ Could not check user groups")
        return False

def fix_pulseaudio():
    """Restart PulseAudio to refresh audio settings"""
    print("\n🔊 FIXING PULSEAUDIO")
    print("="*50)
    
    commands = [
        ("pulseaudio --kill", "Stopping PulseAudio"),
        ("sleep 2", "Waiting for PulseAudio to stop"),
        ("pulseaudio --start", "Starting PulseAudio"),
    ]
    
    success_count = 0
    for cmd, desc in commands:
        if run_command(cmd, desc):
            success_count += 1
    
    return success_count >= 2  # At least stop and start worked

def update_config_sensitivity():
    """Update config.json with more sensitive microphone settings"""
    print("\n⚙️ UPDATING CONFIGURATION")
    print("="*50)
    
    config_path = Path("config.json")
    example_path = Path("config.example.json")
    
    # Create config if it doesn't exist
    if not config_path.exists() and example_path.exists():
        print("📄 Creating config.json from example...")
        import shutil
        shutil.copy(example_path, config_path)
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update voice command settings
            if 'voice_commands' not in config:
                config['voice_commands'] = {}
            
            # More sensitive microphone settings
            old_settings = config['voice_commands'].copy()
            config['voice_commands'].update({
                "model_size": "base",        # Faster processing
                "language": "en",
                "chunk_duration": 1.5,      # Shorter chunks = faster response
                "silence_threshold": 0.005,  # More sensitive (was 0.01)
                "silence_duration": 0.8,    # Less silence required (was 1.0)
            })
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Updated voice command settings:")
            for key, value in config['voice_commands'].items():
                old_val = old_settings.get(key, "not set")
                if old_val != value:
                    print(f"  📝 {key}: {old_val} → {value}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update config: {e}")
            return False
    else:
        print("❌ config.json not found and could not create from example")
        return False

def test_microphone_quickly():
    """Quick microphone test to verify fixes"""
    print("\n🧪 QUICK MICROPHONE TEST")
    print("="*50)
    
    try:
        import pyaudio
        import numpy as np
        
        print("🎤 Testing microphone for 3 seconds...")
        print("🗣️  SPEAK NOW!")
        
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        max_amplitude = 0
        for i in range(int(16000 / 1024 * 3)):  # 3 seconds
            data = stream.read(1024, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplitude = np.max(np.abs(audio_data))
            max_amplitude = max(max_amplitude, amplitude)
            
            # Simple progress indicator
            print(".", end="", flush=True)
        
        stream.stop_stream()
        stream.close()
        pa.terminate()
        
        print(f"\n📊 Maximum amplitude: {max_amplitude}")
        
        if max_amplitude > 1000:
            print("🟢 EXCELLENT - Microphone is working well!")
            return "excellent"
        elif max_amplitude > 500:
            print("🟢 GOOD - Microphone is working")
            return "good"
        elif max_amplitude > 100:
            print("🟡 IMPROVED - Better than before but still weak")
            return "improved"
        else:
            print("🔴 STILL WEAK - May need hardware check")
            return "weak"
            
    except ImportError:
        print("⚠️  PyAudio not available - cannot test")
        return "no_test"
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return "error"

def main():
    """Main fix function"""
    print("🚀 QUICK MICROPHONE FIX TOOL")
    print("="*60)
    print("Automatically applying common microphone sensitivity fixes...")
    print()
    
    # Record initial state
    print("📋 Testing current microphone state...")
    initial_state = test_microphone_quickly()
    
    if initial_state == "excellent":
        print("✅ Microphone is already working perfectly!")
        return
    
    # Apply fixes
    fixes_applied = []
    
    print(f"\n🔧 APPLYING FIXES...")
    print("="*40)
    
    # Fix 1: ALSA levels
    if fix_alsa_levels():
        fixes_applied.append("ALSA mixer levels")
    
    # Fix 2: Audio permissions
    if check_audio_permissions():
        fixes_applied.append("Audio permissions")
    
    # Fix 3: PulseAudio restart
    if fix_pulseaudio():
        fixes_applied.append("PulseAudio restart")
    
    # Fix 4: Configuration
    if update_config_sensitivity():
        fixes_applied.append("Configuration update")
    
    # Test again
    print(f"\n🧪 TESTING AFTER FIXES...")
    print("="*40)
    final_state = test_microphone_quickly()
    
    # Results
    print(f"\n📊 RESULTS SUMMARY")
    print("="*40)
    print(f"  📈 Before fixes: {initial_state}")
    print(f"  📈 After fixes:  {final_state}")
    print(f"  🔧 Fixes applied: {len(fixes_applied)}")
    
    for fix in fixes_applied:
        print(f"    ✅ {fix}")
    
    # Final recommendations
    improvement = ["weak", "improved", "good", "excellent"].index(final_state) - ["weak", "improved", "good", "excellent"].index(initial_state) if final_state in ["weak", "improved", "good", "excellent"] and initial_state in ["weak", "improved", "good", "excellent"] else 0
    
    if improvement > 0:
        print(f"\n🎉 IMPROVEMENT DETECTED!")
        print("✅ Microphone sensitivity has been improved")
    elif final_state in ["good", "excellent"]:
        print(f"\n✅ SUCCESS!")
        print("🎙️ Microphone is now working properly")
    else:
        print(f"\n⚠️  ADDITIONAL STEPS NEEDED")
        print("🔧 Try these manual fixes:")
        print("  • Check USB connection and try different ports")
        print("  • Try a different microphone or headset")
        print("  • Run: python3 debug_microphone.py for detailed diagnosis")
        print("  • Restart the system to apply all changes")
    
    print(f"\n🚀 NEXT STEPS:")
    print("  • Test with: python3 test_continuous_microphone.py")
    print("  • Run INTA: python3 main.py")
    print("  • Look for amplitude > 500 when speaking")

if __name__ == "__main__":
    main() 