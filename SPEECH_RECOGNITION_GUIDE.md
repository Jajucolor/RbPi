# Speech Recognition Implementation Guide

## 🎤 **New Speech Recognition System**

Your INTA AI now uses the **`speech_recognition`** library for better microphone detection and compatibility, following the approach from the [ChatGPT Voice Assistant](https://github.com/ThomasVuNguyen/chatGPT-Voice-Assistant/blob/main/chatgpt_voice.py).

---

## ⚡ **Key Improvements**

### **✅ Better Microphone Detection**
- Automatic microphone discovery
- No PyAudio/ALSA dependencies
- Cross-platform compatibility
- Automatic device selection

### **✅ Enhanced Speech Recognition**
- Google Speech Recognition (primary)
- Whisper fallback (offline)
- Ambient noise adjustment
- Dynamic energy threshold

### **✅ Improved Reliability**
- No more device selection issues
- Better error handling
- Automatic fallbacks
- Platform-independent

---

## 🔧 **How It Works**

### **1. Microphone Detection**
```python
# Automatic microphone detection
microphone = sr.Microphone()
mics = sr.Microphone.list_microphone_names()
```

### **2. Ambient Noise Adjustment**
```python
# Automatically adjusts for background noise
with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)
```

### **3. Speech Recognition**
```python
# Primary: Google Speech Recognition
text = recognizer.recognize_google(audio)

# Fallback: Whisper (offline)
result = whisper_model.transcribe(audio_file)
```

---

## 📋 **Installation**

### **1. Install Dependencies**
```bash
pip install speechrecognition>=3.10.0
pip install pyaudio>=0.2.11  # Still needed as backend
```

### **2. System Dependencies (Linux/Raspberry Pi)**
```bash
sudo apt install portaudio19-dev python3-pyaudio
sudo apt install flac  # For Google Speech Recognition
```

### **3. Windows Dependencies**
```bash
# PyAudio should install automatically with pip
# If not, download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
```

---

## 🧪 **Testing**

### **Test Microphone Detection:**
```bash
python test_speech_recognition.py
# Choose option 2 for microphone listing
```

### **Test Full System:**
```bash
python test_speech_recognition.py
# Choose option 1 for full test
```

### **Test with Main Application:**
```bash
python main.py
# Then speak commands like "What time is it?"
```

---

## ⚙️ **Configuration**

### **Current Settings (config.json):**
```json
{
    "inta": {
        "sample_rate": 16000,
        "chunk_size": 1024,
        "whisper_model": "tiny",
        "energy_threshold": 300,
        "pause_threshold": 0.8,
        "phrase_threshold": 0.3
    }
}
```

### **Speech Recognition Settings:**

| Setting | Value | Effect |
|---------|-------|--------|
| **energy_threshold** | 300 | Minimum audio energy for recording |
| **pause_threshold** | 0.8 | Seconds of silence to end phrase |
| **phrase_threshold** | 0.3 | Minimum speaking time for phrase |
| **dynamic_energy_threshold** | true | Auto-adjust for ambient noise |

---

## 🎯 **Features**

### **✅ Automatic Microphone Selection**
- Detects all available microphones
- Chooses best available device
- No manual configuration needed

### **✅ Ambient Noise Adjustment**
- Automatically adjusts sensitivity
- Handles different environments
- Reduces false triggers

### **✅ Dual Recognition Engine**
- **Primary:** Google Speech Recognition (online, accurate)
- **Fallback:** Whisper (offline, privacy-focused)

### **✅ Real-time Processing**
- Continuous listening
- Immediate response
- Natural conversation flow

---

## 🔍 **Troubleshooting**

### **Microphone Not Detected:**
```bash
# Test microphone listing
python test_speech_recognition.py
# Choose option 2
```

### **Low Recognition Accuracy:**
```python
# Adjust energy threshold
recognizer.energy_threshold = 200  # Lower = more sensitive
```

### **Background Noise Issues:**
```python
# Increase ambient noise adjustment duration
recognizer.adjust_for_ambient_noise(source, duration=3)
```

### **Network Issues (Google Speech):**
- Falls back to Whisper automatically
- Works offline
- No internet required

---

## 📊 **Performance Comparison**

### **Before (PyAudio/ALSA):**
- ❌ Manual device selection
- ❌ Platform-specific issues
- ❌ Complex configuration
- ❌ Device compatibility problems

### **After (speech_recognition):**
- ✅ Automatic device detection
- ✅ Cross-platform compatibility
- ✅ Simple configuration
- ✅ Reliable operation

---

## 🚀 **Usage Examples**

### **Basic Commands:**
```python
# Time and date
"What time is it?"
"What's the date today?"

# Entertainment
"Tell me a joke"
"System status"

# Control
"Volume up"
"Mute audio"
"Emergency mode"
```

### **Advanced Commands:**
```python
# Environment analysis
"Take a picture"
"Describe what you see"
"Are there obstacles ahead?"

# General conversation
"Hello, how are you?"
"What can you help me with?"
"Tell me about yourself"
```

---

## 🔧 **Customization**

### **Adjust Recognition Sensitivity:**
```python
# In inta_ai_manager.py
self.recognizer.energy_threshold = 200  # More sensitive
self.recognizer.energy_threshold = 500  # Less sensitive
```

### **Change Recognition Engine:**
```python
# Force Whisper only
text = self._speech_to_text_whisper(audio)

# Force Google only
text = self.recognizer.recognize_google(audio)
```

### **Add Custom Commands:**
```python
# In process_command method
elif any(word in text_lower for word in ["custom", "command"]):
    return self.execute_function("custom_function")
```

---

## 🎉 **Benefits Summary**

| Feature | Before | After |
|---------|--------|-------|
| **Setup Complexity** | High | Low |
| **Device Compatibility** | Limited | Universal |
| **Recognition Accuracy** | Variable | High |
| **Error Handling** | Basic | Advanced |
| **Platform Support** | Linux-focused | Cross-platform |

---

## 🚀 **Next Steps**

1. **Install the new dependencies:**
   ```bash
   pip install speechrecognition>=3.10.0
   ```

2. **Test the system:**
   ```bash
   python test_speech_recognition.py
   ```

3. **Run the main application:**
   ```bash
   python main.py
   ```

4. **Enjoy improved speech recognition!**

**Your INTA AI now has reliable, cross-platform speech recognition that works out of the box!** 🎤✨ 