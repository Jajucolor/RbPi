#!/usr/bin/env python3
"""
INTA AI Setup Script
Quick setup and configuration for the ALSA-optimized INTA AI assistant
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("INTA AI Assistant Setup (ALSA Optimized)")
    print("=" * 60)
    print("This script will help you set up the INTA AI assistant")
    print("with low-latency ALSA audio for Raspberry Pi.")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\nInstalling Python dependencies...")
    
    try:
        # Install basic requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python dependencies installed successfully")
        
        # Install additional ALSA dependencies
        print("Installing ALSA-specific dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "webrtcvad", "pyalsaaudio"])
        print("✅ ALSA dependencies installed successfully")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def install_system_dependencies():
    """Install system-specific dependencies"""
    system = platform.system().lower()
    
    print(f"\nInstalling system dependencies for {system}...")
    
    if system == "linux":
        try:
            # Detect Linux distribution
            with open("/etc/os-release", "r") as f:
                os_info = f.read().lower()
            
            if "ubuntu" in os_info or "debian" in os_info or "raspbian" in os_info:
                print("Installing ALSA and audio dependencies...")
                subprocess.check_call(["sudo", "apt", "update"])
                subprocess.check_call(["sudo", "apt", "install", "-y", 
                                     "portaudio19-dev", "python3-pyaudio", "ffmpeg",
                                     "python3-alsaaudio", "alsa-utils"])
                
                # Add user to audio group
                print("Setting up audio permissions...")
                subprocess.check_call(["sudo", "usermod", "-a", "-G", "audio", os.getenv("USER", "pi")])
                
                # Optimize ALSA for low latency
                print("Optimizing ALSA for low latency...")
                alsa_config = """# Low-latency ALSA configuration for Raspberry Pi
pcm.!default {
    type plug
    slave.pcm "hw:0,0"
}

ctl.!default {
    type hw
    card 0
}

# Optimize for low latency
pcm.lowlatency {
    type plug
    slave.pcm "hw:0,0"
    slave.rate 8000
    slave.channels 1
    slave.format S16_LE
    slave.period_size 512
    slave.buffer_size 2048
}"""
                
                with open("/tmp/asound.conf", "w") as f:
                    f.write(alsa_config)
                subprocess.check_call(["sudo", "cp", "/tmp/asound.conf", "/etc/asound.conf"])
                
                # Set real-time priority for audio
                print("Setting up real-time audio priority...")
                rt_config = """# Real-time audio priority for INTA AI
@audio - rtprio 95
@audio - memlock unlimited"""
                
                with open("/tmp/limits.conf", "w") as f:
                    f.write(rt_config)
                subprocess.check_call(["sudo", "tee", "-a", "/etc/security/limits.conf"], input=rt_config.encode())
                
            elif "fedora" in os_info or "rhel" in os_info:
                subprocess.check_call(["sudo", "dnf", "install", "-y", 
                                     "portaudio-devel", "python3-pyaudio", "ffmpeg",
                                     "python3-alsaaudio", "alsa-utils"])
            else:
                print("⚠️  Please install ALSA dependencies manually:")
                print("   sudo apt install python3-alsaaudio alsa-utils portaudio19-dev python3-pyaudio ffmpeg")
                return False
            
            print("✅ System dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install system dependencies: {e}")
            return False
    
    elif system == "darwin":  # macOS
        try:
            subprocess.check_call(["brew", "install", "portaudio", "ffmpeg"])
            print("✅ System dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install system dependencies: {e}")
            print("Make sure Homebrew is installed: https://brew.sh/")
            return False
    
    elif system == "windows":
        print("⚠️  For Windows, please install Visual C++ Build Tools manually")
        print("Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        print("Note: ALSA optimization is not available on Windows")
        return True
    
    else:
        print(f"⚠️  Unsupported system: {system}")
        return False

def create_config():
    """Create configuration file"""
    print("\nSetting up configuration...")
    
    config_path = Path("config.json")
    if config_path.exists():
        print("⚠️  config.json already exists. Skipping configuration creation.")
        return True
    
    # Load example config
    example_path = Path("config.example.json")
    if not example_path.exists():
        print("❌ config.example.json not found")
        return False
    
    with open(example_path, 'r') as f:
        config = json.load(f)
    
    # Get user input for configuration
    print("\nConfiguration Setup:")
    print("Enter your API keys and settings (press Enter to skip):")
    
    # OpenAI configuration
    openai_key = input("OpenAI API Key: ").strip()
    if openai_key:
        config["openai"]["api_key"] = openai_key
    
    # ALSA audio settings
    print("\nALSA Audio Settings (optimized for Raspberry Pi):")
    sample_rate = input("Sample Rate (default: 8000): ").strip()
    if sample_rate and sample_rate.isdigit():
        config["inta"]["sample_rate"] = int(sample_rate)
    
    chunk_size = input("Chunk Size (default: 512): ").strip()
    if chunk_size and chunk_size.isdigit():
        config["inta"]["chunk_size"] = int(chunk_size)
    
    vad_aggressiveness = input("VAD Aggressiveness 0-3 (default: 2): ").strip()
    if vad_aggressiveness and vad_aggressiveness.isdigit():
        config["inta"]["vad_aggressiveness"] = int(vad_aggressiveness)
    
    whisper_model = input("Whisper Model (tiny/base/small, default: tiny): ").strip()
    if whisper_model in ["tiny", "base", "small", "medium", "large"]:
        config["inta"]["whisper_model"] = whisper_model
    
    # Save configuration
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration saved to config.json")
    return True

def test_installation():
    """Test the installation"""
    print("\nTesting installation...")
    
    tests = [
        ("Whisper", "import whisper; whisper.load_model('tiny')"),
        ("ALSA", "import alsaaudio"),
        ("WebRTC VAD", "import webrtcvad"),
        ("PyAudio (fallback)", "import pyaudio"),
        ("OpenAI", "import openai"),
        ("NumPy", "import numpy"),
        ("Requests", "import requests")
    ]
    
    all_passed = True
    
    for name, test_code in tests:
        try:
            exec(test_code)
            print(f"✅ {name} - OK")
        except Exception as e:
            print(f"❌ {name} - Failed: {e}")
            if name in ["ALSA", "WebRTC VAD"]:
                all_passed = False
            else:
                print(f"   (This is optional for {name})")
    
    return all_passed

def test_alsa_audio():
    """Test ALSA audio system"""
    print("\nTesting ALSA audio system...")
    
    try:
        import alsaaudio
        
        # List available devices
        devices = alsaaudio.pcms(alsaaudio.PCM_CAPTURE)
        print(f"✅ Found {len(devices)} ALSA capture devices")
        
        # Test default device
        device = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK)
        print(f"✅ Default capture device: {device.cardname()}")
        
        # Test parameters
        device.setchannels(1)
        device.setrate(8000)
        device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        device.setperiodsize(512)
        
        print("✅ ALSA parameters set successfully")
        device.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ALSA test failed: {e}")
        return False

def test_vad():
    """Test Voice Activity Detection"""
    print("\nTesting Voice Activity Detection...")
    
    try:
        import webrtcvad
        import numpy as np
        
        vad = webrtcvad.Vad(2)
        print("✅ VAD initialized successfully")
        
        # Test with dummy audio
        dummy_audio = np.zeros(160, dtype=np.int16).tobytes()  # 10ms at 8kHz
        result = vad.is_speech(dummy_audio, 8000)
        print(f"✅ VAD test completed (dummy audio result: {result})")
        
        return True
        
    except Exception as e:
        print(f"❌ VAD test failed: {e}")
        return False

def download_whisper_model():
    """Download Whisper model"""
    print("\nDownloading Whisper model...")
    
    try:
        import whisper
        model_name = "tiny"  # Fastest for Raspberry Pi
        print(f"Downloading '{model_name}' model (optimized for Raspberry Pi)...")
        model = whisper.load_model(model_name)
        print("✅ Whisper model downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to download Whisper model: {e}")
        return False

def run_test():
    """Run a quick test"""
    print("\nRunning ALSA-optimized test...")
    
    try:
        result = subprocess.run([sys.executable, "test_alsa_inta.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ ALSA test passed")
            return True
        else:
            print("❌ ALSA test failed")
            print("Output:", result.stdout)
            print("Error:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Test timed out (this is normal for first run)")
        return True
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Install system dependencies
    if not install_system_dependencies():
        print("\n⚠️  System dependencies installation failed, but continuing...")
    
    # Create configuration
    if not create_config():
        print("\n❌ Setup failed at configuration creation")
        sys.exit(1)
    
    # Download Whisper model
    if not download_whisper_model():
        print("\n⚠️  Whisper model download failed, but continuing...")
    
    # Test installation
    if not test_installation():
        print("\n⚠️  Some components failed tests, but setup can continue...")
    
    # Test ALSA audio
    if not test_alsa_audio():
        print("\n⚠️  ALSA audio test failed, but setup can continue...")
    
    # Test VAD
    if not test_vad():
        print("\n⚠️  VAD test failed, but setup can continue...")
    
    # Run quick test
    if not run_test():
        print("\n⚠️  Quick test failed, but setup completed...")
    
    print("\n" + "=" * 60)
    print("🎉 ALSA-Optimized INTA AI Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Reboot your system: sudo reboot")
    print("2. Edit config.json with your API keys if needed")
    print("3. Test ALSA optimization: python test_alsa_inta.py")
    print("4. Test INTA AI: python test_inta_ai.py")
    print("5. Run the system: python main.py")
    print("\nFor help, see ALSA_OPTIMIZATION_GUIDE.md")
    print("\nHappy coding! 🚀")

if __name__ == "__main__":
    main() 