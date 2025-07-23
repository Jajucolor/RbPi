# 🤖 INTA Discord Bot Setup Guide

Transform your assistive glasses system into a Discord bot that anyone can interact with from anywhere in the world! This guide will help you set up the INTA Discord Bot with voice receive capabilities.

## 🎯 What This Does

The Discord bot brings your entire assistive glasses system to Discord:
- **🎙️ Voice interaction** - Users speak in Discord voice channels, INTA responds
- **🚨 Real-time obstacle warnings** - Broadcasts sensor alerts to all connected users
- **📷 Image analysis** - Users can request vision analysis via voice or commands
- **💬 Natural conversation** - Chat with INTA in text or voice channels
- **🔍 System monitoring** - Check obstacle sensor status and recent readings

## 📋 Prerequisites

### 1. Create Discord Bot Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "INTA Assistive Glasses")
3. Go to the "Bot" section
4. Click "Add Bot"
5. Copy the bot token (you'll need this later)
6. Enable these "Privileged Gateway Intents":
   - ✅ Message Content Intent
   - ✅ Server Members Intent (optional)

### 2. Bot Permissions

Your bot needs these permissions:
- ✅ Read Messages
- ✅ Send Messages
- ✅ Connect (to voice channels)
- ✅ Speak (in voice channels)
- ✅ Use Voice Activity
- ✅ Attach Files
- ✅ Embed Links

**Invite URL Generator:**
Use this URL (replace YOUR_CLIENT_ID with your bot's client ID):
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=36703232&scope=bot
```

## 🛠️ Installation

### 1. Install Discord Dependencies

```bash
# Install Discord-specific requirements
pip install -r requirements_discord.txt

# Or install individual packages:
pip install discord.py discord-ext-voice-recv PyNaCl ffmpeg-python
```

### 2. Install FFmpeg (Required for Voice)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
1. Download from [FFmpeg website](https://ffmpeg.org/download.html)
2. Add to system PATH

**macOS:**
```bash
brew install ffmpeg
```

### 3. Configure Bot Token

Add your Discord bot token to `config.json`:

```json
{
  "discord": {
    "token": "your-discord-bot-token-here",
    "command_prefix": "!",
    "activity_name": "for voice commands | !join to start"
  },
  "openai": {
    "api_key": "your-openai-api-key-here"
  }
}
```

## 🚀 Running the Discord Bot

### 1. Start the Bot

```bash
# Run the Discord bot
python3 discord_bot.py
```

You should see:
```
🚀 INTABot#1234 is online and ready!
📡 Bot is in 1 guilds
✅ All system components initialized
🔍 Ultrasonic sensor monitoring started
```

### 2. Invite Bot to Server

1. Use the invite URL you generated earlier
2. Select your Discord server
3. Confirm permissions

### 3. Test the Bot

**In a Discord text channel:**
```
!status          # Check bot status
!join            # Bot joins your voice channel
!chat Hello INTA # Chat with INTA
!capture         # Take a picture and analyze it
!obstacle        # Check obstacle sensor status
!leave           # Bot leaves voice channel
```

## 🎙️ Voice Interaction

### Using Voice Commands

1. **Join Voice Channel**: Type `!join` while you're in a voice channel
2. **Start Talking**: Just speak normally - no wake words needed!
3. **INTA Responds**: The bot will speak back in the voice channel

**Example Voice Interactions:**
- *"Hello INTA, how are you today?"*
- *"Take a picture and tell me what you see"*
- *"What's around me right now?"*
- *"I'm feeling nervous about walking"*

### Automatic Features

- **🚨 Obstacle Alerts**: Automatic warnings when obstacles are detected
- **💬 Conversation Logging**: Voice conversations appear in text channel
- **📷 Image Analysis**: Say "take a picture" to trigger vision analysis
- **⏰ Proactive Check-ins**: INTA will check on users periodically

## 🔧 System Integration

### Components Running

When the Discord bot starts, it automatically initializes:

1. **🤖 INTA AI Companion** - Conversational AI with personality
2. **🔍 Ultrasonic Sensor** - Distance monitoring and obstacle detection
3. **📷 Camera Manager** - Image capture for vision analysis
4. **🎤 Voice Recognition** - OpenAI Whisper for speech-to-text
5. **🔊 Text-to-Speech** - gTTS for natural voice responses

### Data Logging

All system data is automatically logged:
- **📊 `discord_distance_log.csv`** - Obstacle sensor readings
- **🗂️ Voice conversations** - Logged to Discord text channels
- **📷 Captured images** - Automatically uploaded to Discord

## 🎛️ Discord Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!join` | Join your voice channel | `!join` |
| `!leave` | Leave voice channel | `!leave` |
| `!chat <message>` | Chat with INTA via text | `!chat How are you?` |
| `!capture` | Take and analyze photo | `!capture` |
| `!obstacle` | Check sensor status | `!obstacle` |
| `!status` | Bot system status | `!status` |

## 🚨 Obstacle Detection in Discord

### How It Works

1. **Continuous Monitoring**: Ultrasonic sensor runs in background
2. **Automatic Alerts**: Obstacles trigger immediate voice warnings
3. **Multi-Channel Broadcast**: Warnings sent to all connected voice channels
4. **Text Backup**: Alerts also posted in text channels

### Warning Levels

- **🔴 CRITICAL (<30cm)**: *"URGENT! Very close obstacle at 25cm! Stop immediately!"*
- **🟡 HIGH (<60cm)**: *"Caution: Obstacle ahead at 45cm. Slow down."*
- **🟠 MEDIUM (<100cm)**: *"Obstacle detected 85cm ahead. Be aware."*
- **🟢 CLEAR (>100cm)**: Path is safe

## 🔧 Troubleshooting

### Common Issues

**Bot won't start:**
- ✅ Check Discord token is correct
- ✅ Verify all dependencies installed
- ✅ Ensure FFmpeg is installed and in PATH

**No voice response:**
- ✅ Check bot has "Speak" permission
- ✅ Verify PyNaCl is installed (`pip install PyNaCl`)
- ✅ Test with `!chat` command first

**Voice recognition not working:**
- ✅ Ensure Whisper is installed (`pip install openai-whisper`)
- ✅ Check microphone permissions in Discord
- ✅ Test audio quality in Discord voice settings

**Obstacle detection not working:**
- ✅ Check sensor configuration in config.json
- ✅ Run `!obstacle` command to check status
- ✅ Verify GPIO pins if using hardware

### Debug Mode

Run with debug logging:
```bash
python3 discord_bot.py --debug
```

## 🌟 Advanced Features

### Multiple Server Support

The bot can be in multiple Discord servers simultaneously:
- Each server gets independent obstacle monitoring
- INTA maintains separate conversation contexts
- Cross-server obstacle warnings (if desired)

### Custom Personalities

Modify INTA's personality in `config.json`:
```json
{
  "companion": {
    "personality": "inta",  // or "jarvis", "assistant", "iris"
    "proactive_mode": true,
    "constant_listening": true
  }
}
```

### Hardware Integration

When running on Raspberry Pi:
1. Uncomment RPi.GPIO in requirements
2. Connect HC-SR04 sensor to GPIO pins
3. Bot automatically switches from simulation to hardware mode

## 🔐 Security & Privacy

### Privacy Features

- **🔒 Local Processing**: Whisper runs locally for voice recognition
- **🛡️ No Voice Storage**: Audio data processed in real-time, not stored
- **📊 Anonymous Logs**: CSV logs contain distance data only
- **🔑 Secure APIs**: OpenAI API calls use secure HTTPS

### Recommended Setup

- **🎧 Use headphones** to prevent audio feedback
- **🔇 Mute when not needed** to preserve privacy
- **👥 Trusted servers only** - invite bot to servers you control

## 🚀 Production Deployment

### Cloud Hosting

**Recommended platforms:**
- **Railway** - Easy Discord bot hosting
- **Heroku** - Free tier available
- **DigitalOcean** - VPS with full control
- **AWS EC2** - Scalable cloud hosting

### Process Management

Use PM2 for production:
```bash
npm install -g pm2
pm2 start discord_bot.py --name inta-bot --interpreter python3
pm2 save
pm2 startup
```

### Environment Variables

For production, use environment variables:
```bash
export DISCORD_TOKEN="your-token-here"
export OPENAI_API_KEY="your-key-here"
python3 discord_bot.py
```

## 🎉 Success! Your Discord Bot is Ready

Once everything is working, you'll have:

✅ **INTA AI Companion** available in Discord  
✅ **Voice interaction** in voice channels  
✅ **Obstacle detection** with real-time warnings  
✅ **Image analysis** via voice commands  
✅ **Natural conversation** with context awareness  
✅ **Multi-server support** for broader accessibility  

**Test it:**
1. Join a voice channel
2. Type `!join`
3. Say *"Hello INTA, take a picture and tell me what you see"*
4. Watch INTA respond with intelligent analysis!

---

## 📞 Support

If you need help:
- Check the troubleshooting section above
- Review bot logs for error messages
- Test individual components with `!status`
- Verify Discord permissions and bot setup

**Your assistive glasses system is now available to help people worldwide through Discord! 🌍🕶️🤖** 