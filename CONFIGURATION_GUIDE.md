# Configuration Guide

## ⚙️ **System Configuration**

Your INTA AI system uses a JSON configuration file (`config.json`) to control all aspects of the system. Here's a complete guide to all settings.

---

## 📁 **Configuration Structure**

### **OpenAI Settings**
```json
{
  "openai": {
      "api_key": "your-openai-api-key-here",
      "model": "gpt-4o-mini",
      "max_tokens": 300,
      "temperature": 0.3
  }
}
```

| Setting | Value | Description |
|---------|-------|-------------|
| **api_key** | String | Your OpenAI API key |
| **model** | String | AI model to use (gpt-4o-mini recommended) |
| **max_tokens** | Number | Maximum response length |
| **temperature** | 0.0-1.0 | Response creativity (0.3 = balanced) |

### **INTA AI Settings (Speech Recognition)**
```json
{
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
  }
}
```

| Setting | Value | Description |
|---------|-------|-------------|
| **sample_rate** | Number | Audio sample rate (16000 = standard) |
| **chunk_size** | Number | Audio chunk size for processing |
| **energy_threshold** | Number | Minimum audio energy for recording |
| **pause_threshold** | Number | Seconds of silence to end phrase |
| **phrase_threshold** | Number | Minimum speaking time for phrase |
| **dynamic_energy_threshold** | Boolean | Auto-adjust for ambient noise |
| **non_speaking_duration** | Number | Keep audio before/after speech |
| **phrase_time_limit** | Number/null | Max phrase length (null = unlimited) |
| **whisper_model** | String | Whisper model size (tiny/base/small) |

### **Camera Settings**
```json
{
  "camera": {
      "width": 1920,
      "height": 1080,
      "quality": 85,
      "auto_focus": true
  }
}
```

| Setting | Value | Description |
|---------|-------|-------------|
| **width** | Number | Image width in pixels |
| **height** | Number | Image height in pixels |
| **quality** | 1-100 | JPEG quality (85 = good balance) |
| **auto_focus** | Boolean | Enable auto-focus |

### **Speech Settings (Real-time TTS)**
```json
{
  "speech": {
      "rate": 250,
      "volume": 0.9,
      "voice_id": "",
      "interrupt_on_capture": true,
      "allow_interrupt": true,
      "interrupt_threshold": 0.5,
      "realtime_enabled": true,
      "word_delay": 0.05,
      "sentence_delay": 0.2,
      "chunk_size": 2
  }
}
```

| Setting | Value | Description |
|---------|-------|-------------|
| **rate** | Number | Speech rate (words per minute) |
| **volume** | 0.0-1.0 | Audio volume level |
| **voice_id** | String | Voice ID (empty = default) |
| **interrupt_on_capture** | Boolean | Stop speech during capture |
| **allow_interrupt** | Boolean | Allow speech interruption |
| **interrupt_threshold** | Number | Interruption sensitivity |
| **realtime_enabled** | Boolean | Enable real-time speech |
| **word_delay** | Number | Delay between words (seconds) |
| **sentence_delay** | Number | Delay between sentences |
| **chunk_size** | Number | Words spoken at once |

### **System Settings**
```json
{
  "system": {
      "capture_interval": 3,
      "log_level": "INFO",
      "save_images": true,
      "save_analysis": true
  }
}
```

| Setting | Value | Description |
|---------|-------|-------------|
| **capture_interval** | Number | Minimum seconds between captures |
| **log_level** | String | Logging level (DEBUG/INFO/WARNING/ERROR) |
| **save_images** | Boolean | Save captured images |
| **save_analysis** | Boolean | Save analysis results |

### **Hardware Settings**
```json
{
  "hardware": {
      "button_pin": 18,
      "led_pin": 24,
      "shutdown_pin": 3,
      "debounce_time": 0.2
  }
}
```

| Setting | Value | Description |
|---------|-------|-------------|
| **button_pin** | Number | GPIO pin for capture button |
| **led_pin** | Number | GPIO pin for status LED |
| **shutdown_pin** | Number | GPIO pin for shutdown button |
| **debounce_time** | Number | Button debounce time (seconds) |

---

## 🎯 **Recommended Settings**

### **For Raspberry Pi:**
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

### **For Windows:**
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

### **For High Accuracy:**
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

### **For Fast Response:**
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

## 🔧 **Configuration Tips**

### **Speech Recognition Sensitivity:**
- **Low sensitivity** (300+): Good for quiet environments
- **Medium sensitivity** (200-300): Balanced for most environments
- **High sensitivity** (100-200): Good for noisy environments

### **Real-time Speech Speed:**
- **Very fast** (0.02s): Almost instant response
- **Fast** (0.05s): Natural conversation speed
- **Normal** (0.1s): Clear pronunciation
- **Slow** (0.2s): Very clear, slower pace

### **Whisper Model Selection:**
- **tiny** (39MB): Fastest, lowest accuracy
- **base** (74MB): Balanced speed/accuracy
- **small** (244MB): Better accuracy, slower
- **medium** (769MB): High accuracy, slower
- **large** (1550MB): Best accuracy, slowest

---

## 🚨 **Troubleshooting**

### **If Speech Recognition is Poor:**
```json
{
  "inta": {
      "energy_threshold": 150,
      "pause_threshold": 1.0,
      "whisper_model": "base"
  }
}
```

### **If System is Too Slow:**
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

### **If Audio Quality is Poor:**
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

---

## 📝 **Creating Your Config**

### **Method 1: Use Setup Script**
```bash
python setup_inta.py
```

### **Method 2: Copy Example**
```bash
cp config.example.json config.json
# Then edit config.json with your settings
```

### **Method 3: Create Manually**
```bash
# Create config.json with the structure above
# Add your OpenAI API key and preferred settings
```

---

## ✅ **Configuration Checklist**

- [ ] **OpenAI API key** is set
- [ ] **Sample rate** is appropriate for your system
- [ ] **Energy threshold** is adjusted for your environment
- [ ] **Whisper model** is suitable for your hardware
- [ ] **Real-time speech** settings are comfortable
- [ ] **Camera settings** match your hardware
- [ ] **Hardware pins** match your wiring

**Your configuration is now ready for the new speech recognition system!** ⚙️✨ 