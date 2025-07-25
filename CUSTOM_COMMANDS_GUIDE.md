# Custom Commands Guide for INTA AI

## 🎯 **Where to Add Commands**

There are **3 main places** where you can add custom commands to your INTA AI system:

### **1. 📁 `modules/inta_ai_manager.py` - Main Command Hub**

This is the **primary location** for adding commands. Look for the `execute_function` method around line 330.

### **2. 🎙️ Voice Command Recognition**

Commands are processed through the `process_command` method and can trigger specific functions.

### **3. 🔧 Configuration-Based Commands**

You can add command aliases and shortcuts in the configuration file.

---

## 🚀 **How to Add Commands**

### **Method 1: Add to `execute_function` (Recommended)**

**Location:** `modules/inta_ai_manager.py` → `execute_function` method

**Current Commands:**
```python
def execute_function(self, function_name: str, params: Dict[str, Any] = None) -> str:
    """Execute specific functions based on commands"""
    try:
        if function_name == "capture_image":
            return "I'll capture an image of your surroundings."
        elif function_name == "describe_surroundings":
            return "I'll analyze and describe what's around you."
        elif function_name == "navigate":
            return "I'll help you navigate safely."
        elif function_name == "read_text":
            return "I'll read any text I can see."
        elif function_name == "identify_objects":
            return "I'll identify objects in your environment."
        # ADD YOUR COMMANDS HERE
        else:
            return f"I don't recognize the function '{function_name}'."
```

**Example - Adding New Commands:**
```python
def execute_function(self, function_name: str, params: Dict[str, Any] = None) -> str:
    """Execute specific functions based on commands"""
    try:
        if function_name == "capture_image":
            return "I'll capture an image of your surroundings."
        elif function_name == "describe_surroundings":
            return "I'll analyze and describe what's around you."
        elif function_name == "navigate":
            return "I'll help you navigate safely."
        elif function_name == "read_text":
            return "I'll read any text I can see."
        elif function_name == "identify_objects":
            return "I'll identify objects in your environment."
        
        # 🆕 YOUR NEW COMMANDS HERE
        elif function_name == "weather":
            return "I'll check the weather for you."
        elif function_name == "time":
            return f"The current time is {time.strftime('%H:%M')}."
        elif function_name == "date":
            return f"Today is {time.strftime('%A, %B %d, %Y')}."
        elif function_name == "joke":
            return "Why don't scientists trust atoms? Because they make up everything!"
        elif function_name == "volume_up":
            return "I'll increase the volume."
        elif function_name == "volume_down":
            return "I'll decrease the volume."
        elif function_name == "emergency":
            return "EMERGENCY MODE ACTIVATED! I'm here to help."
        else:
            return f"I don't recognize the function '{function_name}'."
```

### **Method 2: Enhanced Command Processing**

**Location:** `modules/inta_ai_manager.py` → `process_command` method

**Add Command Recognition:**
```python
def process_command(self, text: str) -> str:
    """Process user command and generate response"""
    try:
        text_lower = text.lower().strip()
        
        # 🆕 COMMAND RECOGNITION
        if "capture" in text_lower or "take picture" in text_lower:
            return self.execute_function("capture_image")
        elif "describe" in text_lower or "what do you see" in text_lower:
            return self.execute_function("describe_surroundings")
        elif "navigate" in text_lower or "help me walk" in text_lower:
            return self.execute_function("navigate")
        elif "read" in text_lower or "what does it say" in text_lower:
            return self.execute_function("read_text")
        elif "identify" in text_lower or "what is that" in text_lower:
            return self.execute_function("identify_objects")
        elif "weather" in text_lower:
            return self.execute_function("weather")
        elif "time" in text_lower:
            return self.execute_function("time")
        elif "date" in text_lower:
            return self.execute_function("date")
        elif "joke" in text_lower or "tell me a joke" in text_lower:
            return self.execute_function("joke")
        elif "volume up" in text_lower or "louder" in text_lower:
            return self.execute_function("volume_up")
        elif "volume down" in text_lower or "quieter" in text_lower:
            return self.execute_function("volume_down")
        elif "emergency" in text_lower or "help" in text_lower:
            return self.execute_function("emergency")
        
        # Fallback to OpenAI
        if self.openai_client:
            response = self._query_openai(text)
            if response:
                return response
        
        # Default response
        return "I'm sorry, I couldn't process your request. Please try again."
        
    except Exception as e:
        self.logger.error(f"Error processing command: {str(e)}")
        return "I encountered an error processing your request."
```

### **Method 3: Configuration-Based Commands**

**Location:** `config.json`

**Add Command Aliases:**
```json
{
    "inta": {
        "enabled": true,
        "voice_interaction": true,
        "command_recognition": true,
        "conversation_history_length": 10,
        "whisper_model": "base",
        "audio_sample_rate": 16000,
        "silence_threshold": 0.01,
        "silence_duration": 0.2,
        "listen_while_speaking": true,
        "interrupt_speech": true,
        "continuous_listening": true,
        "background_listening": true,
        "custom_commands": {
            "capture": ["take picture", "snap photo", "capture image"],
            "describe": ["what do you see", "describe surroundings", "tell me what's around"],
            "navigate": ["help me walk", "guide me", "navigate safely"],
            "read": ["read text", "what does it say", "read that"],
            "weather": ["what's the weather", "weather forecast", "is it raining"],
            "time": ["what time is it", "current time", "time now"],
            "date": ["what day is it", "what's the date", "today's date"],
            "joke": ["tell me a joke", "make me laugh", "funny joke"],
            "volume_up": ["louder", "increase volume", "turn up"],
            "volume_down": ["quieter", "decrease volume", "turn down"],
            "emergency": ["help", "emergency", "urgent", "sos"]
        }
    }
}
```

---

## 🎯 **Example Commands You Can Add**

### **📸 Camera & Vision Commands:**
```python
elif function_name == "zoom_in":
    return "I'll zoom in on the object."
elif function_name == "zoom_out":
    return "I'll zoom out for a wider view."
elif function_name == "focus":
    return "I'll focus on the nearest object."
elif function_name == "scan_area":
    return "I'll scan the entire area for you."
```

### **🎵 Audio Commands:**
```python
elif function_name == "mute":
    return "I'll mute the audio."
elif function_name == "unmute":
    return "I'll unmute the audio."
elif function_name == "speak_slower":
    return "I'll speak more slowly."
elif function_name == "speak_faster":
    return "I'll speak more quickly."
```

### **📱 System Commands:**
```python
elif function_name == "battery_status":
    return "I'll check the battery level."
elif function_name == "system_status":
    return "I'll check the system status."
elif function_name == "restart":
    return "I'll restart the system."
elif function_name == "shutdown":
    return "I'll shut down the system."
```

### **🌍 Environment Commands:**
```python
elif function_name == "temperature":
    return "I'll check the temperature."
elif function_name == "light_level":
    return "I'll check the light level."
elif function_name == "distance":
    return "I'll measure the distance to objects."
elif function_name == "obstacle_detection":
    return "I'll scan for obstacles."
```

### **🎮 Interactive Commands:**
```python
elif function_name == "play_game":
    return "I'll start a voice-controlled game."
elif function_name == "quiz":
    return "I'll start a quiz for you."
elif function_name == "story":
    return "I'll tell you a story."
elif function_name == "music":
    return "I'll play some music for you."
```

---

## 🔧 **Advanced Command Features**

### **Commands with Parameters:**
```python
elif function_name == "set_volume":
    volume = params.get('volume', 0.5) if params else 0.5
    return f"I'll set the volume to {volume * 100}%."
elif function_name == "search":
    query = params.get('query', '') if params else ''
    return f"I'll search for: {query}"
elif function_name == "reminder":
    time = params.get('time', '') if params else ''
    message = params.get('message', '') if params else ''
    return f"I'll remind you at {time}: {message}"
```

### **Commands with External APIs:**
```python
elif function_name == "weather":
    # You could add actual weather API calls here
    return "I'll check the weather for your location."
elif function_name == "news":
    return "I'll get the latest news for you."
elif function_name == "translate":
    text = params.get('text', '') if params else ''
    language = params.get('language', 'Spanish') if params else 'Spanish'
    return f"I'll translate '{text}' to {language}."
```

---

## 🚀 **How to Test Your Commands**

1. **Add your commands** to the `execute_function` method
2. **Save the file**
3. **Restart the application:**
   ```bash
   python main.py
   ```
4. **Test with voice commands:**
   - "Take a picture"
   - "What's the weather?"
   - "Tell me a joke"
   - "What time is it?"

---

## 📝 **Best Practices**

1. **Use descriptive function names** - `capture_image` not `cap`
2. **Add error handling** - Always wrap in try/catch
3. **Provide helpful responses** - Tell the user what you're doing
4. **Keep commands simple** - One action per command
5. **Add logging** - Log command execution for debugging
6. **Test thoroughly** - Make sure commands work reliably

---

## 🎯 **Quick Start Example**

**To add a simple "time" command:**

1. **Open `modules/inta_ai_manager.py`**
2. **Find the `execute_function` method**
3. **Add this line:**
   ```python
   elif function_name == "time":
       return f"The current time is {time.strftime('%H:%M')}."
   ```
4. **Save and restart the application**
5. **Say "What time is it?" to test**

**That's it! Your custom command is now active!** 🎉 