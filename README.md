# Assistive Glasses for Visually Impaired People

A Raspberry Pi-based assistive device that uses computer vision and AI to help visually impaired individuals navigate their environment. The system captures images through a camera, analyzes them using OpenAI's vision API, and provides audio descriptions of the surroundings.

## Features

### 🕶️ Physical Glasses System
- **INTA - Constantly Listening AI Companion**: Always-active microphone with intelligent conversational AI that responds to everything you say
- **Real-time Obstacle Detection**: Ultrasonic sensor continuously monitors for obstacles and provides intelligent warnings through INTA
- **CSV Data Logging**: All distance measurements are automatically saved to CSV files for analysis and tracking
- **Natural Conversation**: No wake words needed - just start talking and INTA responds naturally with contextual intelligence
- **Smart Obstacle Warnings**: INTA provides context-aware obstacle alerts with appropriate urgency levels (critical/high/medium)
- **Real-time Environment Analysis**: Captures and analyzes surroundings using OpenAI's GPT-4 Vision API when requested
- **Enhanced Vision Descriptions**: INTA processes and enhances image descriptions with personality and contextual understanding
- **Multiple Personalities**: Choose from INTA (default), helpful assistant, J.A.R.V.I.S., or friendly companion personalities
- **Proactive Assistance**: INTA checks in regularly and offers help based on your activity patterns
- **Continuous Voice Recognition**: Always-active microphone using OpenAI Whisper for offline, privacy-preserving speech processing
- **High-Quality Audio**: Google Text-to-Speech (gTTS) for clear, natural speech output

### 🤖 Discord Bot Integration
- **Global Accessibility**: Transform your assistive glasses into a Discord bot accessible worldwide
- **Voice Channel Integration**: Join Discord voice channels and interact with users naturally using [discord-ext-voice-recv](https://github.com/imayhaveborkedit/discord-ext-voice-recv)
- **Real-time Voice Processing**: Receive voice input from Discord users and respond with INTA's personality
- **Remote Image Analysis**: Users can request vision analysis through Discord voice or text commands
- **Multi-Server Support**: Bot can operate in multiple Discord servers simultaneously
- **Obstacle Broadcast**: Share real-time obstacle warnings with all connected Discord users
- **Cross-Platform**: Works on any computer with internet connection, no physical hardware required
- **Modular Design**: Well-organized codebase with separate modules for different functionalities
- **Configurable**: Customizable settings for camera, speech, companion personality, and system behavior
- **Raspberry Pi Optimized**: Designed specifically for Raspberry Pi hardware

## System Components

### Main Application (`main.py`)
- Orchestrates all system components
- Handles button press events
- Manages the main application loop
- Provides graceful shutdown functionality

### Camera Manager (`modules/camera_manager.py`)
- Handles Raspberry Pi camera operations
- Captures high-quality images
- Supports simulation mode for testing
- Manages image storage and cleanup

### Vision Analyzer (`modules/vision_analyzer.py`)
- Integrates with OpenAI's Vision API
- Processes images and generates descriptions
- Provides specialized analysis modes
- Handles API errors gracefully

### Speech Manager (`modules/speech_manager.py`)
- Converts text to speech
- Manages speech queue and priorities
- Supports voice customization
- Handles audio output

### Configuration Manager (`modules/config_manager.py`)
- Manages system configuration
- Handles API key storage
- Validates configuration settings
- Supports configuration import/export

### Button Manager (`modules/button_manager.py`)
- Manages hardware button inputs
- Handles GPIO operations
- Provides debouncing functionality
- Supports simulation mode

### Voice Command Manager (`modules/voice_command_manager.py`)
- Listens for voice commands using OpenAI Whisper
- Supports multiple trigger words for capture and shutdown
- Works offline (no internet required for voice commands)
- High accuracy and privacy-friendly speech recognition
- Handles natural conversation routing to AI companion

### AI Companion (`modules/ai_companion.py`)
- **INTA**: Your intelligent navigation and assistance companion - constantly listening and responding
- Multiple personalities available (INTA, Assistant, J.A.R.V.I.S., Iris)
- Enhances vision analysis with contextual intelligence and natural language
- **Intelligent obstacle warnings**: Processes ultrasonic sensor data and provides context-aware safety alerts
- Provides proactive assistance and check-ins based on user activity
- Maintains conversation history and user context for better responses
- Supports both OpenAI API integration and offline fallback modes

### Ultrasonic Sensor (`modules/ultrasonic_sensor.py`)
- **Real-time distance measurement**: Continuously monitors distance to obstacles using HC-SR04 sensor
- **CSV data logging**: Automatically saves all readings with timestamps and obstacle classifications
- **Multi-level obstacle detection**: Categorizes obstacles as close (<30cm), medium (<60cm), far (<100cm), or clear
- **Simulation mode**: Works on any computer for testing without physical hardware
- **Configurable thresholds**: Adjustable distance thresholds and warning levels
- **Thread-safe monitoring**: Continuous background monitoring with callback-based alerts

## Quick Start

1. **Hardware Setup**
   - Connect Raspberry Pi camera
   - **Connect HC-SR04 ultrasonic sensor** (Trigger: GPIO 23, Echo: GPIO 24)
   - Connect capture button to GPIO pin 18 (optional backup)
   - Connect shutdown button to GPIO pin 3 (optional backup)
   - Connect audio output (headphones recommended to prevent feedback)

2. **Software Installation**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd assistive-glasses
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure system
   cp config.example.json config.json
   # Edit config.json with your OpenAI API key
   
   # Run system
   python3 main.py
   ```

3. **Usage with INTA and Obstacle Detection**
   - **🎙️ Just start talking** - INTA's microphone is always active and responds to everything
   - **🚨 Automatic obstacle warnings** - INTA monitors distance continuously and warns about obstacles:
     - *"URGENT: Very close obstacle at 25cm! Stop immediately!"* (Critical)
     - *"Caution: Obstacle ahead at 45cm. Slow down."* (High priority)
     - *"Obstacle detected 85cm ahead. Be aware."* (Medium priority)
   - **💬 Natural conversation**: "Hi INTA, how are you?", "I'm feeling nervous", "What should I do?"
   - **📷 Vision analysis**: "Take a picture" or "Capture image" to analyze surroundings
   - **🛑 System control**: "Shutdown" or "quit" to safely exit
   - **⏰ Proactive assistance**: INTA checks in when you're quiet: "How can I help you navigate?"
   - **📊 CSV logging**: All distance data automatically saved to `distance_log.csv`
   - Buttons also work as backup (capture: GPIO 18, shutdown: GPIO 3)

## 🤖 Discord Bot Quick Start

Transform your assistive glasses system into a Discord bot accessible worldwide!

### 1. Create Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application → Bot → Copy token

### 2. Install & Configure
```bash
# Install Discord dependencies
pip install -r requirements_discord.txt

# Add Discord token to config.json
{
  "discord": {
    "token": "your-discord-bot-token-here"
  }
}

# Test integration
python3 test_discord_bot.py
```

### 3. Run Discord Bot
```bash
python3 discord_bot.py
```

### 4. Use in Discord
- Invite bot to server with voice permissions
- Join voice channel → Type `!join`
- **Talk naturally** - INTA responds in voice!
- `!capture` - Image analysis  
- `!obstacle` - Sensor status

**📖 Complete setup guide: [DISCORD_SETUP.md](DISCORD_SETUP.md)**

## Detailed Setup

For comprehensive setup instructions, please see [SETUP.md](SETUP.md).

## Configuration

The system uses a JSON configuration file with the following sections:

- **OpenAI**: API key and model settings
- **Camera**: Resolution, quality, and camera settings
- **Speech**: Voice rate, volume, and TTS settings
- **System**: Logging, storage, and behavior settings
- **Hardware**: GPIO pin assignments and timing

## Safety and Accessibility

⚠️ **Important**: This system is designed as an assistive aid and should not be used as a replacement for traditional navigation methods. Always have backup navigation tools available.

### Key Safety Features
- Rate limiting to prevent excessive API calls
- Graceful error handling
- Comprehensive logging for troubleshooting
- Configurable audio feedback

### Accessibility Considerations
- Adjustable speech rate and volume
- Simple button interface
- Clear audio feedback
- Customizable analysis prompts

## Requirements

### Hardware
- Raspberry Pi 4 (4GB RAM recommended)
- Raspberry Pi Camera Module v2 or v3
- Push buttons (2x)
- Audio output device
- MicroSD card (32GB+)

### Software
- Raspberry Pi OS (64-bit)
- Python 3.8+
- OpenAI API key
- Internet connection

## Dependencies

Core dependencies include:
- `openai` - OpenAI API client
- `picamera2` - Raspberry Pi camera interface
- `gTTS` - Google Text-to-Speech engine
- `pygame` - Audio playback
- `openai-whisper` - Offline voice command recognition
- `torch` - PyTorch for Whisper neural network
- `PyAudio` - Microphone input
- `RPi.GPIO` - GPIO control
- `Pillow` - Image processing

See [requirements.txt](requirements.txt) for complete list.

## Architecture

The system follows a modular architecture:

```
main.py (Application Controller)
├── modules/
│   ├── camera_manager.py (Camera Operations)
│   ├── vision_analyzer.py (AI Analysis)
│   ├── speech_manager.py (Audio Output)
│   ├── config_manager.py (Configuration)
│   └── button_manager.py (Hardware Input)
├── config.json (Configuration)
├── requirements.txt (Dependencies)
└── SETUP.md (Setup Guide)
```

## Privacy and Data

- Images are processed by OpenAI's API
- No images are stored permanently by default
- Analysis results can be logged locally
- Review OpenAI's privacy policy
- Consider local processing for sensitive use cases

## Contributing

Contributions are welcome! Please consider:
- Improving accessibility features
- Adding new analysis modes
- Enhancing hardware compatibility
- Optimizing performance
- Adding documentation

## License

This project is provided as-is for educational and assistive purposes. Please ensure compliance with local regulations for assistive devices.

## Support

For support and troubleshooting:
1. Check [SETUP.md](SETUP.md) for detailed instructions
2. Review log files for error messages
3. Test individual components separately
4. Verify hardware connections

## Acknowledgments

This project was created to help visually impaired individuals gain better awareness of their surroundings using modern AI technology and affordable hardware.

