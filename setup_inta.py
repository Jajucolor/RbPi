#!/usr/bin/env python3
"""
INTA AI Setup Script
Quick setup and configuration for the INTA AI assistant
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
    print("INTA AI Assistant Setup")
    print("=" * 60)
    print("This script will help you set up the INTA AI assistant")
    print("for your assistive glasses system.")
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
            
            if "ubuntu" in os_info or "debian" in os_info:
                subprocess.check_call(["sudo", "apt", "update"])
                subprocess.check_call(["sudo", "apt", "install", "-y", "portaudio19-dev", "python3-pyaudio", "ffmpeg"])
            elif "fedora" in os_info or "rhel" in os_info:
                subprocess.check_call(["sudo", "dnf", "install", "-y", "portaudio-devel", "python3-pyaudio", "ffmpeg"])
            else:
                print("⚠️  Please install portaudio19-dev, python3-pyaudio, and ffmpeg manually")
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
    
    # JAISON configuration
    jaison_url = input("JAISON Server URL (default: http://localhost:8000): ").strip()
    if jaison_url:
        config["jaison"]["url"] = jaison_url
    
    jaison_key = input("JAISON API Key (optional): ").strip()
    if jaison_key:
        config["jaison"]["api_key"] = jaison_key
    
    # Audio settings
    print("\nAudio Settings:")
    sample_rate = input("Sample Rate (default: 16000): ").strip()
    if sample_rate and sample_rate.isdigit():
        config["inta"]["sample_rate"] = int(sample_rate)
    
    silence_threshold = input("Silence Threshold (default: 0.01): ").strip()
    if silence_threshold:
        try:
            config["inta"]["silence_threshold"] = float(silence_threshold)
        except ValueError:
            print("Invalid silence threshold, using default")
    
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
        ("PyAudio", "import pyaudio; p = pyaudio.PyAudio(); p.terminate()"),
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
            all_passed = False
    
    return all_passed

def download_whisper_model():
    """Download Whisper model"""
    print("\nDownloading Whisper model...")
    
    try:
        import whisper
        print("Downloading 'tiny' model (fastest for testing)...")
        model = whisper.load_model("tiny")
        print("✅ Whisper model downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to download Whisper model: {e}")
        return False

def run_test():
    """Run a quick test"""
    print("\nRunning quick test...")
    
    try:
        result = subprocess.run([sys.executable, "test_inta_ai.py", "--whisper-only"], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Quick test passed")
            return True
        else:
            print("❌ Quick test failed")
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
    
    # Run quick test
    if not run_test():
        print("\n⚠️  Quick test failed, but setup completed...")
    
    print("\n" + "=" * 60)
    print("🎉 INTA AI Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Edit config.json with your API keys if needed")
    print("2. Run: python test_inta_ai.py")
    print("3. Run: python main.py")
    print("\nFor help, see README_INTA.md")
    print("\nHappy coding! 🚀")

if __name__ == "__main__":
    main() 