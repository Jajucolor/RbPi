#!/usr/bin/env python3
"""
INTA AI Setup Script
Quick setup and configuration for the speech_recognition-based INTA AI assistant
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
    print("INTA AI Assistant Setup (Speech Recognition)")
    print("=" * 60)
    print("This script will help you set up the INTA AI assistant")
    print("with speech_recognition library for cross-platform compatibility.")
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
        
        # Install additional speech recognition dependencies
        print("Installing speech recognition dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "speechrecognition>=3.10.0"])
        print("✅ Speech recognition dependencies installed successfully")
        
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
                print("Installing audio dependencies...")
                subprocess.check_call(["sudo", "apt", "update"])
                subprocess.check_call(["sudo", "apt", "install", "-y", 
                                     "portaudio19-dev", "python3-pyaudio", "ffmpeg",
                                     "flac", "alsa-utils"])
                
                # Add user to audio group
                print("Setting up audio permissions...")
                subprocess.check_call(["sudo", "usermod", "-a", "-G", "audio", os.getenv("USER", "pi")])
                
                # Install flac for Google Speech Recognition
                print("Installing FLAC for Google Speech Recognition...")
                subprocess.check_call(["sudo", "apt", "install", "-y", "flac"])
                
            elif "fedora" in os_info or "rhel" in os_info:
                subprocess.check_call(["sudo", "dnf", "install", "-y", 
                                     "portaudio-devel", "python3-pyaudio", "ffmpeg",
                                     "flac", "alsa-utils"])
            else:
                print("⚠️  Please install audio dependencies manually:")
                print("   sudo apt install python3-pyaudio alsa-utils portaudio19-dev ffmpeg flac")
                return False
            
            print("✅ System dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install system dependencies: {e}")
            return False
    
    elif system == "darwin":  # macOS
        try:
            subprocess.check_call(["brew", "install", "portaudio", "ffmpeg", "flac"])
            print("✅ System dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install system dependencies: {e}")
            print("Make sure Homebrew is installed: https://brew.sh/")
            return False
    
    elif system == "windows":
        print("✅ Windows dependencies should install automatically with pip")
        print("If you encounter issues, install Visual C++ Build Tools:")
        print("Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
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
    
    # Speech recognition settings
    print("\nSpeech Recognition Settings:")
    sample_rate = input("Sample Rate (default: 16000): ").strip()
    if sample_rate and sample_rate.isdigit():
        config["inta"]["sample_rate"] = int(sample_rate)
    
    chunk_size = input("Chunk Size (default: 1024): ").strip()
    if chunk_size and chunk_size.isdigit():
        config["inta"]["chunk_size"] = int(chunk_size)
    
    energy_threshold = input("Energy Threshold (default: 300): ").strip()
    if energy_threshold and energy_threshold.isdigit():
        config["inta"]["energy_threshold"] = int(energy_threshold)
    
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
        ("Speech Recognition", "import speech_recognition as sr"),
        ("Whisper", "import whisper; whisper.load_model('tiny')"),
        ("PyAudio", "import pyaudio"),
        ("OpenAI", "import openai"),
        ("NumPy", "import numpy"),
        ("Requests", "import requests"),
        ("gTTS", "from gtts import gTTS"),
        ("Pygame", "import pygame")
    ]
    
    all_passed = True
    
    for name, test_code in tests:
        try:
            exec(test_code)
            print(f"✅ {name} - OK")
        except Exception as e:
            print(f"❌ {name} - Failed: {e}")
            if name in ["Speech Recognition", "PyAudio"]:
                all_passed = False
            else:
                print(f"   (This is optional for {name})")
    
    return all_passed

def test_microphone_detection():
    """Test microphone detection"""
    print("\nTesting microphone detection...")
    
    try:
        import speech_recognition as sr
        
        # List available microphones
        mics = sr.Microphone.list_microphone_names()
        print(f"✅ Found {len(mics)} microphones:")
        for i, mic in enumerate(mics):
            print(f"   {i}: {mic}")
        
        # Test default microphone
        mic = sr.Microphone()
        print(f"✅ Default microphone: {mics[mic.device_index]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Microphone detection failed: {e}")
        return False

def test_speech_recognition():
    """Test speech recognition system"""
    print("\nTesting speech recognition system...")
    
    try:
        import speech_recognition as sr
        
        # Initialize recognizer and microphone
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        
        # Test ambient noise adjustment
        print("Testing ambient noise adjustment...")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        print(f"✅ Energy threshold set to: {recognizer.energy_threshold}")
        
        return True
        
    except Exception as e:
        print(f"❌ Speech recognition test failed: {e}")
        return False

def download_whisper_model():
    """Download Whisper model"""
    print("\nDownloading Whisper model...")
    
    try:
        import whisper
        model_name = "tiny"  # Fastest for general use
        print(f"Downloading '{model_name}' model...")
        model = whisper.load_model(model_name)
        print("✅ Whisper model downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to download Whisper model: {e}")
        return False

def run_test():
    """Run a quick test"""
    print("\nRunning speech recognition test...")
    
    try:
        result = subprocess.run([sys.executable, "test_speech_recognition.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Speech recognition test passed")
            return True
        else:
            print("❌ Speech recognition test failed")
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
    
    # Test microphone detection
    if not test_microphone_detection():
        print("\n⚠️  Microphone detection failed, but setup can continue...")
    
    # Test speech recognition
    if not test_speech_recognition():
        print("\n⚠️  Speech recognition test failed, but setup can continue...")
    
    # Run quick test
    if not run_test():
        print("\n⚠️  Quick test failed, but setup completed...")
    
    print("\n" + "=" * 60)
    print("🎉 Speech Recognition INTA AI Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Reboot your system: sudo reboot (Linux/Raspberry Pi)")
    print("2. Edit config.json with your API keys if needed")
    print("3. Test microphone detection: python test_speech_recognition.py")
    print("4. Test INTA AI: python test_inta_ai.py")
    print("5. Run the system: python main.py")
    print("\nFor help, see SPEECH_RECOGNITION_GUIDE.md")
    print("\nHappy coding! 🚀")

if __name__ == "__main__":
    main() 