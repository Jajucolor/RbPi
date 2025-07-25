# Whisper Models & Listening Configuration Guide

## 🎙️ **Whisper Model Options**

### **Available Models (from fastest to most accurate):**

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `"tiny"` | 39 MB | ⚡⚡⚡ | ⭐⭐ | Fast commands, limited resources |
| `"base"` | 74 MB | ⚡⚡ | ⭐⭐⭐ | Balanced speed/accuracy |
| `"small"` | 244 MB | ⚡ | ⭐⭐⭐⭐ | Good accuracy, moderate speed |
| `"medium"` | 769 MB | 🐌 | ⭐⭐⭐⭐⭐ | High accuracy, slower |
| `"large"` | 1550 MB | 🐌🐌 | ⭐⭐⭐⭐⭐ | Best accuracy, slowest |

### **How to Change Whisper Model:**

1. **Open `config.json`**
2. **Find the `"whisper_model"` line**
3. **Change the value:**

```json
"whisper_model": "base"  // Change this to your preferred model
```

### **Recommended Settings:**

#### **For Raspberry Pi (Limited Resources):**
```json
"whisper_model": "tiny",
"audio_sample_rate": 8000
```

#### **For Windows/Desktop (Good Performance):**
```json
"whisper_model": "base",
"audio_sample_rate": 16000
```

#### **For High Accuracy:**
```json
"whisper_model": "small",
"audio_sample_rate": 16000
```

## 🎧 **Listening While AI is Talking**

### **Current Settings (Enabled):**
```json
"speech": {
    "interrupt_on_capture": true,
    "allow_interrupt": true,
    "interrupt_threshold": 0.5
},
"inta": {
    "listen_while_speaking": true,
    "interrupt_speech": true,
    "continuous_listening": true,
    "background_listening": true
}
```

### **What These Settings Do:**

- **`listen_while_speaking: true`** - INTA listens even when speaking
- **`interrupt_speech: true`** - You can interrupt INTA mid-sentence
- **`continuous_listening: true`** - Always listening for commands
- **`background_listening: true`** - Listens in background during other tasks
- **`interrupt_threshold: 0.5`** - How loud you need to be to interrupt (0.0-1.0)

### **Interrupt Threshold Options:**
- **`0.1`** - Very sensitive (whisper can interrupt)
- **`0.3`** - Sensitive (normal speech)
- **`0.5`** - Balanced (current setting)
- **`0.7`** - Less sensitive (loud speech needed)
- **`0.9`** - Very insensitive (shouting needed)

## ⚙️ **Quick Configuration Examples**

### **Fast & Responsive (Raspberry Pi):**
```json
{
    "whisper_model": "tiny",
    "audio_sample_rate": 8000,
    "silence_duration": 0.1,
    "interrupt_threshold": 0.3,
    "listen_while_speaking": true
}
```

### **Balanced Performance (Desktop):**
```json
{
    "whisper_model": "base",
    "audio_sample_rate": 16000,
    "silence_duration": 0.2,
    "interrupt_threshold": 0.5,
    "listen_while_speaking": true
}
```

### **High Accuracy (Powerful PC):**
```json
{
    "whisper_model": "small",
    "audio_sample_rate": 16000,
    "silence_duration": 0.3,
    "interrupt_threshold": 0.4,
    "listen_while_speaking": true
}
```

## 🔧 **How to Apply Changes**

1. **Edit `config.json`**
2. **Change the values you want**
3. **Save the file**
4. **Restart the application:**
   ```bash
   python main.py
   ```

## 📊 **Performance Comparison**

| Setting | CPU Usage | Memory | Speed | Accuracy |
|---------|-----------|--------|-------|----------|
| `tiny` | 10% | 50MB | ⚡⚡⚡ | 85% |
| `base` | 20% | 100MB | ⚡⚡ | 90% |
| `small` | 40% | 300MB | ⚡ | 95% |
| `medium` | 70% | 800MB | 🐌 | 98% |
| `large` | 90% | 1600MB | 🐌🐌 | 99% |

## 🎯 **Current Configuration**

Your current settings are optimized for:
- ✅ **Listening while AI talks**
- ✅ **Interrupt capability**
- ✅ **Balanced speed/accuracy**
- ✅ **Continuous listening**

**Ready to use!** 🚀 