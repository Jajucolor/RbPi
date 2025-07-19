# Assistive Glasses for Visually Impaired People

A Raspberry Pi-based assistive device that uses computer vision and AI to help visually impaired individuals navigate their environment. The system captures images through a camera, analyzes them using OpenAI's vision API, and provides audio descriptions of the surroundings.

## Features

- **Real-time Environment Analysis**: Captures and analyzes surroundings using OpenAI's GPT-4 Vision API
- **Audio Feedback**: Converts visual information to speech using text-to-speech technology
- **Simple Controls**: Easy-to-use button interface for capturing and analyzing environments
- **Modular Design**: Well-organized codebase with separate modules for different functionalities
- **Configurable**: Customizable settings for camera, speech, and system behavior
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

## Quick Start

1. **Hardware Setup**
   - Connect Raspberry Pi camera
   - Connect capture button to GPIO pin 18
   - Connect shutdown button to GPIO pin 3
   - Connect audio output (speakers/headphones)

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

3. **Usage**
   - Press capture button to analyze surroundings
   - Listen to audio description
   - Press shutdown button to safely exit

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

