# Assistive Glasses System Setup Guide

This guide will help you set up the voice-activated assistive glasses system on your Raspberry Pi using OpenAI Whisper for offline voice recognition and gTTS for high-quality speech output.

## Hardware Requirements

### Essential Components
- **Raspberry Pi 4** (4GB RAM recommended, 8GB ideal for larger Whisper models)
- **Raspberry Pi Camera Module v2 or v3**
- **MicroSD card** (32GB or larger, Class 10, fast read/write speeds recommended)
- **Power supply** (5V, 3A - stable power important for AI processing)
- **USB microphone or USB headset** (primary input method)
- **Speakers or headphones** with 3.5mm jack or USB audio
- **Internet connection** (for OpenAI vision API and initial Whisper model download)

### Optional Components (Backup/Enhanced Features)
- Push buttons (2x momentary push buttons) - Physical backup controls
- Breadboard and jumper wires - For button connections
- Resistors (2x 10kΩ pull-up resistors) - For button circuits
- Portable battery pack for mobile use
- External USB sound card for better audio quality
- LED indicators for system status
- Enclosure/case for protection and portability

## Software Installation

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
   sudo apt install -y mpg321 mpg123 ffmpeg
   sudo apt install -y portaudio19-dev python3-pyaudio
   sudo apt install -y build-essential python3-dev
   ```

### Step 2: Install Camera and Hardware Libraries

1. **Install picamera2 (Raspberry Pi camera interface)**
   ```bash
   sudo apt install -y python3-picamera2
   ```

2. **Install RPi.GPIO (for optional button controls)**
   ```bash
   pip3 install RPi.GPIO
   ```

3. **Test camera**
   ```bash
   # Enable camera in raspi-config if not already done
   libcamera-hello --list-cameras
   libcamera-still -t 2000 -o camera_test.jpg
   ```

### Step 3: Clone and Setup Project

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RbPi  # or your project directory name
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv glasses_env
   source glasses_env/bin/activate
   ```

3. **Upgrade pip and install basic tools**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

### Step 4: Install AI/ML Dependencies

1. **Install PyTorch (CPU version for Raspberry Pi)**
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

2. **Install OpenAI Whisper**
   ```bash
   pip install openai-whisper
   # Note: Model will download on first use (~74MB for base model)
   ```

3. **Install other core dependencies**
   ```bash
   pip install openai gTTS pygame PyAudio numpy Pillow requests
   ```

4. **Install all requirements**
   ```bash
   pip install -r requirements.txt
   ```

### Step 5: Hardware Connections

#### Essential Connections

##### Camera Connection
- Connect the Raspberry Pi Camera Module to the camera connector
- Ensure the camera is enabled in raspi-config
- Test with: `libcamera-still -t 2000 -o test.jpg`

##### Microphone Connection (Primary Input)
- **Connect USB microphone** to any USB port
- **Or use USB headset** with built-in microphone
- Test microphone detection: `arecord -l` (should list your microphone)
- Test recording: `arecord -d 3 test.wav` (records 3 seconds)

##### Audio Output Connection
- Connect speakers or headphones to the 3.5mm audio jack
- **Or use USB audio device** (often better quality)
- **Or use USB headset** (microphone + headphones combined)
- Test audio: `aplay /usr/share/sounds/alsa/Front_Left.wav`

#### Optional Connections (Physical Backup Controls)

##### Button Connections (Backup Controls)
- **Capture Button**: Connect to GPIO pin 18
  - One terminal to GPIO 18
  - Other terminal to Ground (GND)
  - Optional: Add 10kΩ pull-up resistor between GPIO 18 and 3.3V

- **Shutdown Button**: Connect to GPIO pin 3
  - One terminal to GPIO 3
  - Other terminal to Ground (GND)
  - Optional: Add 10kΩ pull-up resistor between GPIO 3 and 3.3V

### Step 6: Configuration

1. **Create configuration file**
   ```bash
   cp config.example.json config.json
   ```

2. **Edit configuration**
   ```json
   {
     "openai": {
       "api_key": "your-openai-api-key-here",
       "model": "gpt-4o-mini",
       "max_tokens": 300,
       "temperature": 0.3
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
     "voice_commands": {
       "model_size": "base",
       "language": "en",
       "chunk_duration": 2.0,
       "silence_threshold": 0.01,
       "silence_duration": 1.0
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

3. **Set up OpenAI API key**
   - Get your API key from OpenAI
   - Add it to the config file, or
   - Set environment variable: `export OPENAI_API_KEY="your-key"`
   - Or create a `.openai_key` file with your key

### Step 7: Test the System

**Important**: First run will download the Whisper model (~74MB for base model). Ensure you have internet connection.

1. **Test basic imports and setup**
   ```bash
   python3 -c "import torch; import whisper; import openai; print('✓ All AI libraries imported successfully')"
   ```

2. **Test camera**
   ```bash
   python3 -c "from modules.camera_manager import CameraManager; cm = CameraManager(); print(cm.get_camera_info())"
   ```

3. **Test gTTS speech synthesis**
   ```bash
   python3 test_gtts.py
   ```

4. **Test Whisper voice recognition (IMPORTANT)**
   ```bash
   python3 test_voice_commands.py
   # This will:
   # - Download Whisper model on first run (~74MB)
   # - Test microphone detection
   # - Test voice recognition accuracy
   # - Verify all voice command functionality
   ```

5. **Test physical buttons (if connected)**
   ```bash
   python3 modules/button_manager.py
   ```

6. **Test complete system**
   ```bash
   python3 main.py
   # System will start with voice activation ready
   # Say "capture" or "analyze" to test image analysis
   # Say "shutdown" or use Ctrl+C to exit
   ```

## Running the System

### Basic Usage

1. **Start the system**
   ```bash
   source glasses_env/bin/activate  # Activate virtual environment
   python3 main.py
   ```
   
   The system will announce: *"Assistive glasses system starting. Say 'capture' or 'analyze' to take a picture and analyze your surroundings."*

2. **Primary Interface: Voice Commands**
   - **"capture"** / **"analyze"** / **"take picture"** → Capture and analyze surroundings
   - **"describe"** / **"look"** / **"see"** → Same as capture
   - **"what do you see"** → Same as capture
   - **"shutdown"** / **"quit"** / **"exit"** → Safely shutdown system
   - **"stop"** / **"goodbye"** → Same as shutdown

3. **Backup Interface: Physical Buttons** (if connected)
   - **Capture Button** (GPIO 18): Press to capture and analyze surroundings  
   - **Shutdown Button** (GPIO 3): Press to safely shutdown the system

4. **System Workflow**
   - Voice activation is **always listening** in the background
   - Say any capture command → System responds: *"Voice command received. Capturing image now."*
   - Image analysis takes 5-15 seconds → System speaks detailed description
   - Ready for next command immediately

### Auto-start on Boot

1. **Create systemd service**
   ```bash
   sudo nano /etc/systemd/system/assistive-glasses.service
   ```

2. **Add service configuration**
   ```ini
   [Unit]
   Description=Assistive Glasses System
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/assistive-glasses
   ExecStart=/home/pi/assistive-glasses/glasses_env/bin/python3 main.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable assistive-glasses.service
   sudo systemctl start assistive-glasses.service
   ```

## Troubleshooting

### Common Issues

1. **Whisper voice recognition not working**
   - **Check microphone**: `arecord -l` (should list your microphone)
   - **Test recording**: `arecord -d 3 test.wav && aplay test.wav`
   - **Check model download**: Look for error messages during first run
   - **Memory issues**: Try smaller model size ("tiny" instead of "base")
   - **Run voice test**: `python3 test_voice_commands.py`

2. **gTTS speech not working**  
   - **Check audio output**: `aplay /usr/share/sounds/alsa/Front_Left.wav`
   - **Set audio output**: `sudo raspi-config` > Advanced Options > Audio
   - **Test gTTS**: `python3 test_gtts.py`
   - **Check internet**: gTTS requires internet connection

3. **Camera not working**
   - **Enable camera**: `sudo raspi-config` > Interface Options > Camera > Enable
   - **Test camera**: `libcamera-still -t 2000 -o test.jpg`
   - **Check connection**: Ensure ribbon cable is properly connected
   - **Check processes**: `sudo lsof /dev/video*` (kill conflicting processes)

4. **High CPU usage / Slow performance**
   - **Use smaller Whisper model**: Change config "model_size" to "tiny"
   - **Check temperature**: `vcgencmd measure_temp`
   - **Increase swap space**: `sudo dphys-swapfile swapoff && sudo nano /etc/dphys-swapfile` (set CONF_SWAPSIZE=1024)
   - **Close unnecessary services**: `sudo systemctl disable [service-name]`

5. **OpenAI API errors**
   - **Verify API key**: Check config.json and environment variables
   - **Check internet**: `ping api.openai.com`
   - **Monitor usage**: Check OpenAI dashboard for rate limits
   - **Test connection**: `curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models`

6. **Physical buttons not responding (if used)**
   - **Check GPIO connections**: Verify pins 18 and 3
   - **Test with multimeter**: Check continuity
   - **Check configuration**: Verify pin numbers in config.json
   - **Test buttons**: `python3 modules/button_manager.py`

7. **Permission errors**
   - **Audio permissions**: Add user to audio group: `sudo usermod -a -G audio $USER`
   - **GPIO permissions**: Add user to gpio group: `sudo usermod -a -G gpio $USER`
   - **Reboot after changes**: `sudo reboot`

8. **Dependencies installation issues**
   - **PyTorch installation**: Use CPU-only version for Raspberry Pi
   - **PyAudio issues**: `sudo apt install portaudio19-dev python3-pyaudio`
   - **Whisper dependencies**: `pip install openai-whisper[full]`
   - **Virtual environment**: Recreate if corrupted: `rm -rf glasses_env && python3 -m venv glasses_env`

### Debug Mode

Run with debug logging:
```bash
python3 main.py --debug
```

### Log Files

- System logs: `glasses_system.log`
- Analysis history: `analysis_log.txt`
- Configuration: `config.json`

## Optimization Tips

### Whisper Performance Optimization
- **Model selection**: Use "tiny" or "base" models for faster response
- **Memory management**: Increase swap space to 1-2GB for larger models
- **Temperature monitoring**: Ensure adequate cooling for continuous operation
- **Background processes**: Disable unnecessary services to free up resources

### Audio Quality Optimization
- **Use external USB sound card** for better audio quality than 3.5mm jack
- **Position microphone** close to user (6-12 inches) for better voice detection
- **Noise environment**: Test voice commands in typical usage environment
- **USB headset**: Often provides best combined microphone and speaker quality

### Power and Performance Management
- **Efficient power supply**: Use official Raspberry Pi power supply (5V, 3A)
- **CPU scaling**: Configure conservative CPU governor for consistent performance
- **Memory split**: Allocate appropriate GPU memory: `sudo raspi-config` > Advanced > Memory Split (128MB)
- **Overclock cautiously**: Only if needed and with adequate cooling

### Camera and Vision Processing
- **Camera resolution**: Balance between quality and processing speed
- **Image compression**: Adjust JPEG quality in config (85 is good balance)
- **Lighting conditions**: Ensure adequate lighting for better AI analysis

### Network and API Optimization  
- **Stable internet**: Ensure reliable connection for OpenAI API calls
- **API rate limits**: Implement proper rate limiting (3-second minimum interval)
- **Error handling**: Graceful degradation when network is unavailable

### System-level Optimizations
```bash
# Increase swap space for AI processing
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Optimize boot time
sudo systemctl disable bluetooth  # If not needed
sudo systemctl disable cups       # If not printing

# Monitor system resources
htop  # Install with: sudo apt install htop
```

## Safety and Accessibility

### Critical Safety Notes
- **This system is an assistive aid only** - never rely solely on AI for navigation
- **Always maintain situational awareness** - the system supplements, not replaces, human judgment  
- **Test thoroughly** in controlled environments before real-world use
- **Have backup methods** - physical buttons, traditional navigation aids, human assistance
- **Regular maintenance** - keep system updated and test functionality regularly

### Accessibility Features
- **Voice-first interface**: Natural speech commands for hands-free operation
- **Multiple command phrases**: Various ways to trigger the same action
- **Audio feedback**: System confirms commands and provides detailed descriptions  
- **Adjustable settings**: Customizable speech rate, volume, and sensitivity
- **Offline voice processing**: Whisper works without internet for privacy and reliability

### Privacy and Security
- **Local voice processing**: All voice commands processed locally on device (Whisper)
- **No voice data sent**: Only image analysis uses external APIs (OpenAI Vision)
- **Audio files**: Temporary recordings automatically deleted after processing
- **API key security**: Store API keys securely, never share in logs or public areas

### Customization Options
- **Voice model size**: Adjust Whisper model for speed vs accuracy balance
- **Language support**: Configure for 60+ languages supported by Whisper
- **Custom commands**: Add specific phrases relevant to user needs
- **Analysis prompts**: Modify OpenAI prompts for specific use cases or environments
- **Audio preferences**: Fine-tune microphone sensitivity and speech output

### Recommended Usage Patterns
- **Indoor navigation**: Excellent for describing room layouts, obstacles, objects
- **Outdoor awareness**: Good for general environment description, landmark identification
- **Reading assistance**: Can read visible text, signs, labels when clearly captured
- **Object identification**: Helps identify objects, people, and environmental features
- **Not recommended for**: Vehicle navigation, detailed obstacle avoidance, critical safety decisions

## Support and Updates

### Getting Help
- Check log files for error messages
- Review this setup guide
- Test individual components separately
- Consider hardware troubleshooting

### Maintenance
- Regular system updates
- Monitor disk space
- Check camera lens cleanliness
- Battery maintenance (if using portable power)

## Advanced Features and Capabilities

### Voice Command Processing
- **OpenAI Whisper integration**: State-of-the-art offline speech recognition
- **Multi-language support**: 60+ languages including English, Spanish, French, German, etc.
- **Noise robustness**: Works well in various acoustic environments
- **Natural language**: Understands variations and natural speech patterns

### AI Vision Analysis  
- **OpenAI GPT-4 Vision**: Advanced image understanding and description
- **Context-aware descriptions**: Tailored specifically for visually impaired users
- **Multi-modal AI**: Combines vision and language understanding
- **Detailed analysis**: Objects, people, text, spatial relationships, hazards

### System Architecture
- **Modular design**: Easy to extend and customize individual components
- **Threaded processing**: Voice recognition and image analysis run concurrently
- **Error resilience**: Graceful handling of component failures
- **Resource management**: Efficient memory and CPU usage

### Development and Testing
- **Comprehensive test suite**: Separate tests for each component
- **Simulation modes**: Test without hardware for development
- **Extensive logging**: Detailed logs for troubleshooting and analysis
- **Configuration validation**: Automatic checking of settings

## Legal and Privacy

### Privacy Improvements with Whisper
- **Voice processing**: 100% local, never transmitted anywhere
- **Image processing**: Only images sent to OpenAI for vision analysis
- **No audio storage**: Voice recordings immediately deleted after processing
- **Reduced data exposure**: Significantly less data sent to external services

### Important Considerations
- **Images analyzed by OpenAI**: Images are processed by OpenAI's vision API
- **Review policies**: Check OpenAI's current privacy policy and terms of service  
- **Data retention**: Configure whether to save images and analysis locally
- **Network security**: Ensure secure internet connection for API calls
- **Local alternatives**: Consider fully offline solutions for maximum privacy

### Compliance and Regulations
- **Assistive device regulations**: Check local laws regarding AI-powered assistive devices
- **Accessibility standards**: Ensure compliance with relevant accessibility guidelines
- **Data protection**: Follow GDPR, CCPA, or other applicable data protection laws
- **Medical device considerations**: This is not a medical device - consult professionals for medical needs

### Recommended Practices
- **Regular updates**: Keep all components updated for security
- **Secure configuration**: Protect API keys and sensitive configuration data  
- **User consent**: Ensure users understand what data is processed and how
- **Backup systems**: Maintain traditional navigation methods as backup 
