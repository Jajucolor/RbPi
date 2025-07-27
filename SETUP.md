# INTA AI Setup Guide

## 🚀 **Complete Installation Guide**

This guide provides step-by-step instructions for setting up the INTA AI system on different platforms.

---

## 📋 **System Requirements**

### **Hardware Requirements**
- **Raspberry Pi 4** (4GB RAM recommended) or compatible computer
- **Raspberry Pi Camera Module** v2 or v3 (for vision features)
- **Microphone** for voice input
- **Speakers/Headphones** for audio output
- **Push buttons** (2x) for hardware control
- **MicroSD card** (32GB+) for Raspberry Pi

### **Software Requirements**
- **Python 3.8+**
- **Raspberry Pi OS** (64-bit) or compatible Linux distribution
- **Windows 10/11** or **macOS 10.15+** (for development/testing)
- **Internet connection** for API access and model downloads

---

## 🔧 **Installation Methods**

### **Method 1: Automated Setup (Recommended)**

```bash
# Clone the repository
git clone <repository-url>
cd RbPi

# Run the automated setup script
python setup_inta.py
```

The setup script will automatically:
- ✅ Install Python dependencies
- ✅ Install system dependencies
- ✅ Configure audio settings
- ✅ Download Whisper models
- ✅ Create configuration file
- ✅ Test all components

### **Method 2: Manual Installation**

#### **Step 1: Clone Repository**
```bash
git clone <repository-url>
cd RbPi
```

#### **Step 2: Install Python Dependencies**
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install NumPy with BLAS support (for better performance)
pip install numpy>=1.21.0

# Install core requirements
pip install -r requirements.txt

# Install additional speech recognition dependencies
pip install speechrecognition>=3.10.0
```

#### **Step 3: Install System Dependencies**

**For Ubuntu/Debian/Raspberry Pi:**
```bash
sudo apt update
sudo apt install -y \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    flac \
    alsa-utils \
    libopenblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    gfortran \
    build-essential \
    pkg-config

# Add user to audio group
sudo usermod -a -G audio $USER
```

**For macOS:**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install portaudio ffmpeg flac openblas
```

**For Windows:**
```bash
# PyAudio should install automatically with pip
# If you encounter issues, install Visual C++ Build Tools:
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

#### **Step 4: Configure System**

**For Raspberry Pi (Audio Optimization):**
```bash
# Set real-time priority for audio processes
echo "@audio - rtprio 95" | sudo tee -a /etc/security/limits.conf
echo "@audio - memlock unlimited" | sudo tee -a /etc/security/limits.conf

# Set performance CPU governor
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Reboot for changes to take effect
sudo reboot
```

#### **Step 5: Create Configuration**
```bash
# Copy example configuration
cp config.example.json config.json

# Edit configuration with your API keys
nano config.json
```

#### **Step 6: Download Whisper Models**
```bash
# Download the recommended model
python -c "import whisper; whisper.load_model('tiny')"
```

---

## ⚙️ **Configuration Setup**

### **1. Basic Configuration**

Edit `config.json` with your settings:

```json
{
  "openai": {
    "api_key": "your-openai-api-key-here",
    "model": "gpt-4o-mini",
    "max_tokens": 300,
    "temperature": 0.3
  },
  "inta": {
    "sample_rate": 16000,
    "chunk_size": 1024,
    "energy_threshold": 300,
    "pause_threshold": 0.8,
    "phrase_threshold": 0.3,
    "dynamic_energy_threshold": true,
    "non_speaking_duration": 0.5,
    "phrase_time_limit": null,
    "whisper_model": "tiny"
  },
  "speech": {
    "realtime_enabled": true,
    "word_delay": 0.05,
    "sentence_delay": 0.2,
    "chunk_size": 2,
    "interrupt_on_capture": true,
    "allow_interrupt": true,
    "interrupt_threshold": 0.5
  },
  "camera": {
    "width": 1920,
    "height": 1080,
    "quality": 85,
    "auto_focus": true
  },
  "system": {
    "capture_interval": 3,
    "log_level": "INFO",
    "save_images": true,
    "save_analysis": true
  },
  "hardware": {
    "button_pin": 18,
    "led_pin": 24,
    "shutdown_pin": 3,
    "debounce_time": 0.2
  }
}
```

### **2. Platform-Specific Settings**

#### **For Raspberry Pi:**
```json
{
  "inta": {
    "sample_rate": 16000,
    "chunk_size": 1024,
    "energy_threshold": 300,
    "whisper_model": "tiny"
  },
  "speech": {
    "word_delay": 0.05,
    "chunk_size": 2
  }
}
```

#### **For Windows/Desktop:**
```json
{
  "inta": {
    "sample_rate": 16000,
    "chunk_size": 1024,
    "energy_threshold": 200,
    "whisper_model": "base"
  },
  "speech": {
    "word_delay": 0.03,
    "chunk_size": 1
  }
}
```

#### **For High Accuracy:**
```json
{
  "inta": {
    "whisper_model": "base",
    "energy_threshold": 250,
    "pause_threshold": 1.0
  },
  "speech": {
    "word_delay": 0.1,
    "chunk_size": 3
  }
}
```

#### **For Fast Response:**
```json
{
  "inta": {
    "whisper_model": "tiny",
    "energy_threshold": 200,
    "pause_threshold": 0.5
  },
  "speech": {
    "word_delay": 0.02,
    "chunk_size": 1
  }
}
```

---

## 🧪 **Testing Installation**

### **1. Test Individual Components**

#### **Test Speech Recognition:**
```bash
# Test microphone detection
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"

# Test Whisper model
python -c "import whisper; model = whisper.load_model('tiny'); print('Whisper OK')"
```

#### **Test Audio System:**
```bash
# Test PyAudio
python -c "import pyaudio; p = pyaudio.PyAudio(); p.terminate(); print('PyAudio OK')"

# Test gTTS
python -c "from gtts import gTTS; print('gTTS OK')"
```

#### **Test OpenAI Integration:**
```bash
# Test OpenAI client
python -c "import openai; print('OpenAI OK')"
```

### **2. Test System Integration**

#### **Test Microphone Access:**
```python
import speech_recognition as sr

# List available microphones
mics = sr.Microphone.list_microphone_names()
print(f"Found {len(mics)} microphones:")
for i, mic in enumerate(mics):
    print(f"  {i}: {mic}")

# Test default microphone
mic = sr.Microphone()
print(f"Default microphone: {mics[mic.device_index]}")
```

#### **Test Speech Recognition:**
```python
import speech_recognition as sr

# Initialize recognizer and microphone
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Test ambient noise adjustment
with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
print(f"Energy threshold set to: {recognizer.energy_threshold}")
```

#### **Test Real-time Speech:**
```python
from modules.speech_manager import SpeechManager

# Test speech synthesis
speech = SpeechManager()
speech.speak("Hello, this is a test of the speech system.")
```

---

## 🔧 **Hardware Setup (Raspberry Pi)**

### **1. Camera Connection**
```bash
# Enable camera in raspi-config
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable

# Test camera
vcgencmd get_camera
# Should return: supported=1 detected=1
```

### **2. Button Wiring**
```
Capture Button:
- GPIO 18 → Button → Ground

Shutdown Button:
- GPIO 3 → Button → Ground

Status LED (optional):
- GPIO 24 → LED → Resistor → Ground
```

### **3. Audio Setup**
```bash
# Check audio devices
aplay -l
arecord -l

# Test microphone
arecord -d 5 test.wav
aplay test.wav

# Adjust microphone levels
alsamixer
```

---

## 🚨 **Troubleshooting**

### **Common Installation Issues**

#### **1. PyAudio Installation Fails**
```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev python3-pyaudio

# macOS
brew install portaudio
pip install pyaudio

# Windows
pip install pipwin
pipwin install pyaudio
```

#### **2. NumPy Installation Issues**
```bash
# Install BLAS libraries first
sudo apt install libopenblas-dev liblapack-dev gfortran

# Then install NumPy
pip install numpy --no-build-isolation
```

#### **3. Whisper Model Download Issues**
```bash
# Manual download
python -c "import whisper; whisper.load_model('tiny')"

# Check available models
python -c "import whisper; print(whisper.available_models())"
```

#### **4. Microphone Not Detected**
```bash
# Check available devices
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"

# Test microphone access
python -c "import speech_recognition as sr; mic = sr.Microphone(); print('Microphone OK')"
```

### **Performance Issues**

#### **System Too Slow:**
```json
{
  "inta": {
    "whisper_model": "tiny",
    "chunk_size": 512
  },
  "speech": {
    "word_delay": 0.02,
    "chunk_size": 1
  }
}
```

#### **High CPU Usage:**
- Use smaller Whisper model
- Reduce sample rate
- Close unnecessary applications
- Check for background processes

#### **Audio Quality Issues:**
```json
{
  "inta": {
    "sample_rate": 22050,
    "energy_threshold": 400
  },
  "speech": {
    "word_delay": 0.1,
    "chunk_size": 3
  }
}
```

### **Speech Recognition Issues**

#### **Low Recognition Accuracy:**
```json
{
  "inta": {
    "energy_threshold": 150,
    "pause_threshold": 1.0,
    "whisper_model": "base"
  }
}
```

#### **Background Noise Issues:**
```python
# Increase ambient noise adjustment duration
recognizer.adjust_for_ambient_noise(source, duration=3)
```

---

## 📊 **Performance Optimization**

### **Raspberry Pi Optimizations**

#### **1. System Optimizations**
```bash
# Set performance CPU governor
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-powersave

# Increase GPU memory
# Add to /boot/config.txt:
gpu_mem=128
```

#### **2. Audio Optimizations**
```bash
# Real-time priority for audio
echo "@audio - rtprio 95" | sudo tee -a /etc/security/limits.conf
echo "@audio - memlock unlimited" | sudo tee -a /etc/security/limits.conf

# Optimize ALSA settings
# Add to /etc/asound.conf:
pcm.lowlatency {
    type plug
    slave.pcm "hw:0,0"
    slave.rate 8000
    slave.channels 1
    slave.format S16_LE
    slave.period_size 512
    slave.buffer_size 2048
}
```

#### **3. Memory Optimizations**
```bash
# Increase swap space
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### **Cross-Platform Optimizations**

#### **Windows Optimizations:**
- Disable unnecessary startup programs
- Set Python process priority to high
- Use SSD for better I/O performance

#### **macOS Optimizations:**
- Disable unnecessary background processes
- Use external microphone for better quality
- Ensure adequate cooling

---

## 🔒 **Security Considerations**

### **API Key Security**
```bash
# Store API keys securely
export OPENAI_API_KEY="your-key-here"

# Or use environment variables in config
{
  "openai": {
    "api_key": "${OPENAI_API_KEY}"
  }
}
```

### **Network Security**
- Use HTTPS for all API communications
- Consider VPN for additional security
- Monitor API usage and costs

### **Data Privacy**
- Images are processed by OpenAI's API
- No images are stored permanently by default
- Review OpenAI's privacy policy
- Consider local processing for sensitive use cases

---

## 📱 **Mobile/Remote Setup**

### **SSH Access (Raspberry Pi)**
```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Connect remotely
ssh pi@raspberry-pi-ip
```

### **Remote Development**
```bash
# Use VS Code Remote Development
# Install Remote-SSH extension
# Connect to Raspberry Pi via SSH
```

### **Headless Operation**
```bash
# Run system as service
sudo nano /etc/systemd/system/inta-ai.service

[Unit]
Description=INTA AI Assistant
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RbPi
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable inta-ai
sudo systemctl start inta-ai
```

---

## 🎯 **Quick Start Checklist**

- [ ] **Repository cloned** and dependencies installed
- [ ] **OpenAI API key** configured in `config.json`
- [ ] **Microphone** detected and working
- [ ] **Whisper model** downloaded successfully
- [ ] **Audio output** tested and working
- [ ] **Camera** connected and enabled (Raspberry Pi)
- [ ] **Buttons** wired correctly (optional)
- [ ] **System optimized** for performance
- [ ] **Test run** completed successfully

---

## 🚀 **Next Steps**

### **1. First Run**
```bash
# Start the system
python main.py

# Test voice commands:
# - "Hello INTA"
# - "What time is it?"
# - "Take a picture"
```

### **2. Customization**
- Add custom commands in `modules/inta_ai_manager.py`
- Adjust speech settings in `config.json`
- Configure hardware pins for your setup

### **3. Integration**
- Connect to smart home systems
- Integrate with navigation apps
- Add emergency contact features

---

## 📞 **Support**

### **Getting Help**
1. Check the troubleshooting section above
2. Review log files for error messages
3. Test individual components separately
4. Verify hardware connections

### **Useful Commands**
```bash
# Check system status
python -c "import sys; print(f'Python {sys.version}')"

# Check available packages
pip list | grep -E "(openai|speech|whisper|pyaudio)"

# Monitor system resources
htop
iostat 1

# Check audio devices
aplay -l
arecord -l
```

---

**Your INTA AI system is now ready for intelligent assistive glasses applications!** 🎉✨ 
