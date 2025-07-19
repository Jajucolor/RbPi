# Assistive Glasses System Setup Guide

This guide will help you set up the assistive glasses system on your Raspberry Pi.

## Hardware Requirements

### Essential Components
- Raspberry Pi 4 (4GB RAM recommended)
- Raspberry Pi Camera Module v2 or v3
- MicroSD card (32GB or larger, Class 10)
- Power supply (5V, 3A)
- Speakers or headphones with 3.5mm jack
- USB microphone or USB headset with microphone
- Push buttons (2x momentary push buttons) - Optional backup
- Breadboard and jumper wires - Optional for buttons
- Resistors (2x 10kΩ pull-up resistors) - Optional for buttons

### Optional Components
- Portable battery pack for mobile use
- Small amplifier for better audio output
- LED indicators for system status
- Enclosure/case for protection

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
   sudo apt install -y mpg321 mpg123
   sudo apt install -y portaudio19-dev python3-pyaudio
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
   ```bash
   pip install openai
   pip install gTTS
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Step 4: Hardware Connections

#### Button Connections
- **Capture Button**: Connect to GPIO pin 18
  - One terminal to GPIO 18
  - Other terminal to Ground (GND)
  - Optional: Add 10kΩ pull-up resistor between GPIO 18 and 3.3V

- **Shutdown Button**: Connect to GPIO pin 3
  - One terminal to GPIO 3
  - Other terminal to Ground (GND)
  - Optional: Add 10kΩ pull-up resistor between GPIO 3 and 3.3V

#### Camera Connection
- Connect the Raspberry Pi Camera Module to the camera connector
- Ensure the camera is enabled in raspi-config

#### Audio Connection
- Connect speakers or headphones to the 3.5mm audio jack
- Or use USB audio device if preferred

#### Microphone Connection
- Connect USB microphone to any USB port
- Or use USB headset with built-in microphone
- Test microphone: `arecord -l` (should list your microphone)

### Step 5: Configuration

1. **Create configuration file**
   ```bash
   cp config.example.json config.json
   ```

2. **Edit configuration**
   ```json
   {
     "openai": {
       "api_key": "your-openai-api-key-here",
       "model": "gpt-4o-mini"
     },
     "camera": {
       "width": 1920,
       "height": 1080,
       "quality": 85
     },
     "speech": {
       "rate": 150,
       "volume": 0.9
     },
     "hardware": {
       "button_pin": 18,
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

### Step 6: Test the System

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

4. **Test voice commands**
   ```bash
   python3 test_voice_commands.py
   ```

5. **Test complete system**
   ```bash
   python3 main.py
   ```

## Running the System

### Basic Usage

1. **Start the system**
   ```bash
   python3 main.py
   ```

2. **Use voice commands or buttons**
   - **Voice Commands**: 
     - Say "capture", "analyze", "take picture", or "describe" to analyze surroundings
     - Say "shutdown", "quit", or "exit" to safely shutdown the system
   - **Backup Buttons** (if connected):
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

### Performance
- Use lower camera resolution for faster processing
- Adjust speech rate for better comprehension
- Implement local caching for common responses

### Power Management
- Use efficient power supply
- Implement sleep modes between captures
- Consider battery optimization settings

### Audio Quality
- Use external USB audio device for better quality
- Adjust volume levels in configuration
- Consider using Bluetooth audio

## Safety and Accessibility

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

## Legal and Privacy

### Important Considerations
- Images are processed by OpenAI's servers
- Review OpenAI's privacy policy
- Consider data retention policies
- Implement local processing if privacy is critical

### Compliance
- Check local regulations for assistive devices
- Consider accessibility standards
- Review data protection requirements 