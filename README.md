# INTA AI - Intelligent Assistive Glasses System

## **Overview**

INTA AI is an intelligent voice assistant designed for assistive glasses, providing real-time speech recognition, computer vision analysis, and natural conversation capabilities. Built with Raspberry Pi optimization and cross-platform compatibility.

---

## **Key Features**

### **Advanced Speech Recognition**
- **Wake Word System**: INTA responds only when called by name ("INTA", "Hey INTA", etc.)
- **Speech Recognition Library**: Cross-platform compatibility with automatic microphone detection
- **Whisper Integration**: Offline speech recognition with multiple model options
- **Real-time Processing**: Continuous listening with voice activity detection
- **Ambient Noise Adjustment**: Automatic sensitivity adjustment for different environments

### **AI-Powered Conversations**
- **OpenAI Integration**: Natural language processing with GPT models
- **Contextual Command Understanding**: Understands natural language variations and asks for confirmation
- **Real-time Speech Synthesis**: Word-by-word speech generation for natural conversations
- **Command Recognition**: Built-in commands for system control and assistance
- **Context Awareness**: Maintains conversation history for better interactions

### **Computer Vision**
- **Raspberry Pi Camera**: High-quality image capture and analysis
- **OpenAI Vision API**: Advanced image description and object recognition
- **Real-time Analysis**: Instant environment assessment and description
- **Text Recognition**: OCR capabilities for reading text in images

### **Performance Optimizations**
- **Low Latency Audio**: Optimized for Raspberry Pi with configurable settings
- **Resource Management**: Efficient CPU and memory usage
- **Cross-platform Support**: Works on Windows, macOS, and Linux
- **Modular Architecture**: Easy to extend and customize

---

##   **System Architecture**

### **Core Components**

| Component | Description | File |
|-----------|-------------|------|
| **INTA AI Manager** | Voice assistant and command processing | `modules/inta_ai_manager.py` |
| **Camera Manager** | Image capture and camera control | `modules/camera_manager.py` |
| **Vision Analyzer** | Image analysis and description | `modules/vision_analyzer.py` |
| **Speech Manager** | Text-to-speech and audio output | `modules/speech_manager.py` |
| **Config Manager** | System configuration and settings | `modules/config_manager.py` |
| **Button Manager** | Hardware button control | `modules/button_manager.py` |

### **Audio Processing Pipeline**

```
Microphone → Speech Recognition → Command Processing → AI Response → Text-to-Speech
     ↓              ↓                    ↓              ↓              ↓
 Pirewire        Whisper            OpenAI GPT      Real-time      Audio Output
```

---

## **Quick Start**

### **1. Installation**
```bash
# Clone the repository
git clone <repository-url>
cd RbPi

# Run the setup script
python setup_inta.py
```

### **2. Configuration**
```bash
# Copy example configuration
cp config.example.json config.json

# Edit with your API keys
nano config.json
```

### **3. Run the System**
```bash
python main.py
```

---

## **Configuration Guide**

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

### **Speech Recognition Settings**
```json
{
  "inta": {
      "sample_rate": 16000,
      "chunk_size": 1024,
      "energy_threshold": 300,
      "pause_threshold": 0.8,
      "whisper_model": "tiny",
      "wake_word": "inta",
      "wake_word_confidence": 0.7,
      "wake_word_timeout": 5.0,
      "contextual_mode": true,
      "confirmation_required": true,
      "confirmation_timeout": 10.0
  }
}
```

### **Real-time Speech Settings**
```json
{
  "speech": {
      "realtime_enabled": true,
      "word_delay": 0.05,
      "sentence_delay": 0.2,
      "chunk_size": 2
  }
}
```

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

---

## **Speech Recognition System**

### **Features**
- **Wake Word Activation**: INTA only responds when called by name ("INTA", "Hey INTA", etc.)
- **Automatic Microphone Detection**: No manual device selection needed
- **Cross-platform Compatibility**: Works on Windows, macOS, and Linux
- **Dual Recognition Engine**: Google Speech Recognition (online) + Whisper (offline)
- **Ambient Noise Adjustment**: Automatic sensitivity adjustment
- **Real-time Processing**: Continuous listening with voice activity detection

### **Whisper Model Options**

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `"tiny"` | 39 MB | ⚡⚡⚡ | ⭐⭐ | Fast commands, limited resources |
| `"base"` | 74 MB | ⚡⚡ | ⭐⭐⭐ | Balanced speed/accuracy |
| `"small"` | 244 MB | ⚡ | ⭐⭐⭐⭐ | Good accuracy, moderate speed |
| `"medium"` | 769 MB | 🐌 | ⭐⭐⭐⭐⭐ | High accuracy, slower |
| `"large"` | 1550 MB | 🐌🐌 | ⭐⭐⭐⭐⭐ | Best accuracy, slowest |

### **Recommended Settings**

#### **For Raspberry Pi:**
```json
{
  "inta": {
      "sample_rate": 16000,
      "chunk_size": 1024,
      "energy_threshold": 300,
      "whisper_model": "tiny"
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
  }
}
```

---

## **Wake Word System**

### **How It Works**
- **Wake Word Detection**: INTA continuously listens for its name ("INTA", "Hey INTA", etc.)
- **Activation**: When the wake word is detected, INTA responds with "Yes, I'm listening. How can I help you?"
- **Command Mode**: After wake word activation, INTA listens for your command for 5 seconds
- **Timeout**: If no command is given within 5 seconds, INTA returns to sleep mode

### **Wake Word Variations**
- **"INTA"** - Simple and direct
- **"Hey INTA"** - Casual and friendly
- **"Hello INTA"** - Formal greeting
- **"Hi INTA"** - Informal greeting
- **"Okay INTA"** - Confirmation style
- **"Listen INTA"** - Attention seeking
- **"Attention INTA"** - Formal attention

### **Configuration**
```json
{
  "inta": {
      "wake_word": "inta",
      "wake_word_confidence": 0.7,
      "wake_word_timeout": 5.0
  }
}
```

---

## **Real-time Speech System**

### **How It Works**
- **Word-by-Word Generation**: Speaks each word as it's generated
- **No Waiting**: No delays for complete responses
- **Natural Flow**: Continuous conversation like talking to a person
- **Interrupt Capability**: Can interrupt mid-sentence

### **Speed Options**

| Setting | Value | Effect |
|---------|-------|--------|
| **Very Fast** | `word_delay: 0.02` | Almost instant |
| **Fast** | `word_delay: 0.05` | Natural pace |
| **Normal** | `word_delay: 0.1` | Clear pronunciation |
| **Slow** | `word_delay: 0.2` | Very clear, slower pace |

### **Configuration**
```json
{
  "speech": {
      "realtime_enabled": true,
      "word_delay": 0.05,
      "sentence_delay": 0.2,
      "chunk_size": 2,
      "interrupt_on_capture": true,
      "allow_interrupt": true
  }
}
```

---

## **Contextual Command Understanding**

### **How It Works**
- **Natural Language Processing**: INTA understands commands even when you don't use exact keywords
- **Context Analysis**: Uses AI to interpret your intent from natural language
- **Confirmation System**: Always asks for confirmation before executing commands
- **Fallback**: If contextual understanding fails, falls back to exact keyword matching

### **Examples of Contextual Understanding**

#### **Vision-Related Requests**
- **"I can't see what's in front of me"** → Capture and describe surroundings
- **"What's around me?"** → Analyze environment
- **"Is there anything I should know about?"** → Capture and analyze
- **"Can you see anything important?"** → Describe surroundings

#### **Navigation Requests**
- **"I need help walking"** → Navigation assistance
- **"Is it safe to walk forward?"** → Obstacle detection
- **"What's the path like?"** → Environment analysis
- **"Help me navigate"** → Navigation guidance

#### **Information Requests**
- **"What's the weather like?"** → Weather information
- **"What time is it?"** → Current time
- **"What day is it?"** → Current date
- **"How's the system doing?"** → System status

### **Confirmation Process**
1. **User**: "I can't see what's in front of me"
2. **INTA**: "I understood you want me to capture and describe your surroundings. Is that correct? Say yes or no."
3. **User**: "Yes"
4. **INTA**: *Executes the command*

### **Configuration**
```json
{
  "inta": {
      "contextual_mode": true,
      "confirmation_required": true,
      "confirmation_timeout": 10.0
  }
}
```

---

## **Custom Commands**

### **Wake Word Usage**
- **"INTA"** - Basic wake word
- **"Hey INTA"** - Casual wake word
- **"Hello INTA"** - Formal wake word
- **"Listen INTA"** - Attention wake word

### **Built-in Commands**
- **"Take a picture"** - Capture and analyze environment
- **"Describe what you see"** - Get detailed environment description
- **"What time is it?"** - Get current time
- **"Tell me a joke"** - Entertainment
- **"System status"** - Check system health
- **"Emergency mode"** - Activate emergency assistance

### **Contextual Understanding Examples**
- **"I can't see what's in front of me"** → INTA asks: "I understood you want me to capture and describe your surroundings. Is that correct?"
- **"What's the weather like?"** → INTA asks: "I understood you want me to check the weather information. Is that correct?"
- **"I need help walking"** → INTA asks: "I understood you want me to help with navigation. Is that correct?"

### **Adding Custom Commands**

**Location:** `modules/inta_ai_manager.py` → `execute_function` method

```python
def execute_function(self, function_name: str, params: Dict[str, Any] = None) -> str:
    """Execute specific functions based on commands"""
    try:
        if function_name == "capture_image":
            return "I'll capture an image of your surroundings."
        elif function_name == "describe_surroundings":
            return "I'll analyze and describe what's around you."
        # ADD YOUR COMMANDS HERE
        elif function_name == "weather":
            return "I'll check the weather for you."
        elif function_name == "time":
            return f"The current time is {time.strftime('%H:%M')}."
        else:
            return f"I don't recognize the function '{function_name}'."
```

### **Command Recognition**
```python
def process_command(self, text: str) -> str:
    """Process user command and generate response"""
    text_lower = text.lower().strip()
    
    if "capture" in text_lower or "take picture" in text_lower:
        return self.execute_function("capture_image")
    elif "describe" in text_lower or "what do you see" in text_lower:
        return self.execute_function("describe_surroundings")
    elif "weather" in text_lower:
        return self.execute_function("weather")
    # ADD MORE COMMAND RECOGNITION HERE

