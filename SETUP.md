# Assistive Glasses System Setup Guide

This comprehensive guide will help you set up the assistive glasses system with INTA AI assistant on your Raspberry Pi or other platforms.

## 📋 Hardware Requirements

### Essential Components
- Raspberry Pi 4 (4GB RAM recommended)
- Raspberry Pi Camera Module v2 or v3
- MicroSD card (32GB or larger, Class 10)
- Power supply (5V, 3A)
- Speakers or headphones with 3.5mm jack
- **Microphone** for voice input (USB or 3.5mm)
- Push buttons (2x momentary push buttons)
- Breadboard and jumper wires
- Resistors (2x 10kΩ pull-up resistors)

### Optional Components
- Portable battery pack for mobile use
- Small amplifier for better audio output
- LED indicators for system status
- Enclosure/case for protection
- USB microphone for better voice quality

## 🖥️ Software Installation

### Step 1: Prepare Raspberry Pi OS

1. **Install Raspberry Pi OS**
   ```bash
   # Use Raspberry Pi Imager to install Raspberry Pi OS (64-bit recommended)
   # Enable SSH, I2C, and Camera in raspi-config
   sudo raspi-config
   ```

2. **Update system packages**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

3. **Install system dependencies**
   ```bash
   sudo apt install -y python3-pip python3-venv git
   sudo apt install -y python3-pygame alsa-utils
   sudo apt install -y mpg321 mpg123
   sudo apt install -y portaudio19-dev python3-pyaudio ffmpeg
   ```

### Step 2: Install Camera and GPIO Libraries

1. **Install picamera2**
   ```bash
   sudo apt install -y python3-picamera2
   ```

2. **Install RPi.GPIO**
   ```bash
   pip3 install RPi.GPIO
   ```

### Step 3: Clone and Setup Project

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd assistive-glasses
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv glasses_env
   source glasses_env/bin/activate
   ```
   
   **Alternative setup for system packages:**
   ```bash
   # 1. Deactivate and delete old venv
   deactivate
   rm -r ~/RbPi/glasses_env
   
   # 2. Recreate with --system-site-packages
   cd ~/RbPi
   python3 -m venv glasses_env --system-site-packages
   
   # 3. Activate
   source glasses_env/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Step 4: Quick Setup with INTA AI

For automated setup and configuration:

```bash
# Run the automated setup script
python setup_inta.py
```

This script will:
- Check Python version compatibility
- Install all dependencies
- Configure system settings
- Download Whisper models
- Test the installation
- Create configuration files

## 🔌 Hardware Connections

### Button Connections
- **Capture Button**: Connect to GPIO pin 18
  - One terminal to GPIO 18
  - Other terminal to Ground (GND)
  - Optional: Add 10kΩ pull-up resistor between GPIO 18 and 3.3V

- **Shutdown Button**: Connect to GPIO pin 3
  - One terminal to GPIO 3
  - Other terminal to Ground (GND)
  - Optional: Add 10kΩ pull-up resistor between GPIO 3 and 3.3V

### Camera Connection
- Connect the Raspberry Pi Camera Module to the camera connector
- Ensure the camera is enabled in raspi-config

### Audio Connection
- Connect speakers or headphones to the 3.5mm audio jack
- Connect microphone for voice input
- Or use USB audio device if preferred

## ⚙️ Configuration

### Step 1: Create Configuration File
```bash
cp config.example.json config.json
```

### Step 2: Edit Configuration
```json
{
  "openai": {
    "api_key": "your-openai-api-key-here",
    "model": "gpt-4o-mini",
    "max_tokens": 300,
    "temperature": 0.3
  },
  "jaison": {
    "url": "http://localhost:8000",
    "api_key": "your-jaison-api-key-here"
  },
  "inta": {
    "sample_rate": 16000,
    "chunk_size": 1024,
    "record_seconds": 5,
    "silence_threshold": 0.01,
    "silence_duration": 1.0,
    "whisper_model": "base"
  },
  "camera": {
    "width": 1920,
    "height": 1080,
    "quality": 85,
    "auto_focus": true
  },
  "speech": {
    "rate": 150,
    "volume": 0.9,
    "voice_id": "",
    "interrupt_on_capture": false
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

### Step 3: Set up API Keys

#### OpenAI API Key
- Get your API key from [OpenAI Platform](https://platform.openai.com/)
- Add it to the config file, or
- Set environment variable: `export OPENAI_API_KEY="your-key"`
- Or create a `.openai_key` file with your key

#### JAISON Setup (Optional)
For enhanced AI capabilities:

1. **Clone JAISON Core:**
```bash
git clone https://github.com/limitcantcode/jaison-core.git
cd jaison-core
```

2. **Follow JAISON installation instructions:**
```bash
conda create -n jaison-core python=3.12 pip=24.0 -y
conda activate jaison-core
pip install .
```

3. **Start JAISON server:**
```bash
python ./src/main.py --config=example
```

## 🧪 Testing the System

### Step 1: Test Individual Components

1. **Test camera**
   ```bash
   python3 -c "from modules.camera_manager import CameraManager; cm = CameraManager(); print(cm.get_camera_info())"
   ```

2. **Test speech**
   ```bash
   python3 test_gtts.py
   ```

3. **Test buttons**
   ```bash
   python3 modules/button_manager.py
   ```

### Step 2: Test INTA AI Components

1. **Test audio system**
   ```bash
   python test_audio.py
   ```

2. **Test OpenAI integration**
   ```bash
   python test_openai_integration.py
   ```

3. **Test INTA AI**
   ```bash
   python test_inta_ai.py
   ```

4. **Interactive demo**
   ```bash
   python demo_inta.py
   ```

### Step 3: Test Complete System
```bash
python3 main.py
```

## 🚀 Running the System

### Basic Usage

1. **Start the system**
   ```bash
   python3 main.py
   ```

2. **Use voice commands**
   - "Hello INTA, how are you?"
   - "Take a picture of my surroundings"
   - "What do you see in front of me?"
   - "Help me navigate safely"

3. **Use the buttons**
   - **Capture Button**: Press to capture and analyze surroundings
   - **Shutdown Button**: Press to safely shutdown the system

### Auto-start on Boot

1. **Create systemd service**
   ```bash
   sudo nano /etc/systemd/system/assistive-glasses.service
   ```

2. **Add service configuration**
   ```ini
   [Unit]
   Description=Assistive Glasses System with INTA AI
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/assistive-glasses
   ExecStart=/home/pi/assistive-glasses/glasses_env/bin/python3 main.py
   Restart=always
   RestartSec=5
   Environment=PYTHONPATH=/home/pi/assistive-glasses

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable assistive-glasses.service
   sudo systemctl start assistive-glasses.service
   ```

## 🔧 Configuration Options

### INTA Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `sample_rate` | 16000 | Audio sampling rate (Hz) |
| `chunk_size` | 1024 | Audio processing chunk size |
| `record_seconds` | 5 | Maximum recording duration |
| `silence_threshold` | 0.01 | Silence detection threshold |
| `silence_duration` | 1.0 | Silence duration to stop recording |
| `whisper_model` | "base" | Whisper model size |

### Audio Settings

Adjust these for your microphone and environment:

```json
"inta": {
  "sample_rate": 16000,
  "silence_threshold": 0.01,
  "silence_duration": 1.0
}
```

**Troubleshooting Audio:**
- **Low sensitivity**: Increase `silence_threshold` (e.g., 0.05)
- **Too sensitive**: Decrease `silence_threshold` (e.g., 0.005)
- **Short recordings**: Increase `silence_duration` (e.g., 2.0)
- **Long recordings**: Decrease `silence_duration` (e.g., 0.5)

### Performance Optimization

**For Raspberry Pi:**
```json
"inta": {
  "whisper_model": "tiny",
  "sample_rate": 8000,
  "chunk_size": 512
}
```

**For High-End Systems:**
```json
"inta": {
  "whisper_model": "medium",
  "sample_rate": 16000,
  "chunk_size": 2048
}
```

## 🔧 Troubleshooting

### Common Issues

1. **Camera not working**
   - Check if camera is enabled: `sudo raspi-config`
   - Verify connection: `libcamera-still -t 2000 -o test.jpg`
   - Check for other processes using camera

2. **Audio not working**
   - Check audio output: `aplay /usr/share/sounds/alsa/Front_Left.wav`
   - Set audio output: `sudo raspi-config` > Advanced Options > Audio
   - Test speech: `python3 test_gtts.py`

3. **Button not responding**
   - Check GPIO connections
   - Verify pin numbers in config
   - Test with multimeter

4. **OpenAI API errors**
   - Verify API key is correct
   - Check internet connection
   - Monitor API usage/limits

5. **PyAudio Installation Fails**
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

6. **Whisper Model Download Issues**
   ```bash
   # Manual download
   python -c "import whisper; whisper.load_model('base')"
   ```

7. **Microphone Not Detected**
   ```bash
   # Test microphone
   python -c "import pyaudio; p = pyaudio.PyAudio(); print(p.get_device_count())"
   ```

8. **Audio Processing Issues**
   ```bash
   # Test audio system
   python test_audio.py
   ```

9. **OpenAI API Compatibility Issues**
   ```bash
   # Test OpenAI integration
   python test_openai_integration.py
   ```

10. **JAISON Connection Issues**
    - Verify JAISON server is running: `curl http://localhost:8000/health`
    - Check API key configuration
    - Ensure network connectivity

### Debug Mode

Run with debug logging:
```bash
python3 main.py --debug
```

### Log Files

- System logs: `glasses_system.log`
- INTA AI logs: `inta_test.log`
- Analysis history: `analysis_log.txt`
- Configuration: `config.json`

## 🔒 Safety and Accessibility

### Important Notes
- Always test thoroughly before relying on the system
- Have backup navigation methods available
- Regular system updates and maintenance
- Consider user-specific customizations

### Customization
- Adjust speech rate and volume for user preference
- Modify prompts for specific use cases
- Add custom voice commands
- Implement different analysis modes

## 🚀 Optimization Tips

### Performance
- Use lower camera resolution for faster processing
- Adjust speech rate for better comprehension
- Implement local caching for common responses
- Use appropriate Whisper model size for your hardware

### Power Management
- Use efficient power supply
- Implement sleep modes between captures
- Consider battery optimization settings

### Audio Quality
- Use external USB audio device for better quality
- Adjust volume levels in configuration
- Consider using Bluetooth audio
- Position microphone for optimal voice capture

## 🔄 Maintenance

### Regular Tasks
- Update system packages: `sudo apt update && sudo apt upgrade`
- Clean up log files: `rm -f *.log`
- Check disk space: `df -h`
- Monitor system resources: `htop`

### Updates
- Pull latest code: `git pull origin main`
- Update dependencies: `pip install -r requirements.txt --upgrade`
- Test system after updates

## 📚 Additional Resources

### Documentation
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Project J.A.I.son Documentation](https://github.com/limitcantcode/jaison-core)
- [Whisper Documentation](https://github.com/openai/whisper)

### Community Support
- Check GitHub issues for known problems
- Join Raspberry Pi forums
- Participate in accessibility technology communities

## 🆘 Getting Help

### Before Asking for Help
1. Check log files for error messages
2. Review this setup guide thoroughly
3. Test individual components separately
4. Verify hardware connections
5. Check internet connectivity

### Support Channels
- GitHub Issues: Report bugs and request features
- Documentation: Review setup and troubleshooting guides
- Community Forums: Ask questions and share experiences

## 📄 Legal and Privacy

### Important Considerations
- Images are processed by OpenAI's servers
- Review OpenAI's privacy policy
- Consider data retention policies
- Implement local processing if privacy is critical

### Compliance
- Check local regulations for assistive devices
- Consider accessibility standards
- Review data protection requirements
- Ensure compliance with medical device regulations if applicable

---

**Setup Status**: ✅ Complete and Tested  
**INTA AI Status**: ✅ Fully Integrated  
**Documentation Status**: ✅ Comprehensive  
**Support Status**: ✅ Available  

The assistive glasses system with INTA AI is now ready for use! 
