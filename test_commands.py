#!/usr/bin/env python3
"""
Test Script for INTA AI Commands
Demonstrates all available commands
"""

import json
import time
from modules.inta_ai_manager import IntaAIManager

def test_commands():
    """Test all available commands"""
    print("🧪 TESTING INTA AI COMMANDS")
    print("="*50)
    
    # Load configuration
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found!")
        return
    
    # Initialize INTA AI
    print("🔧 Initializing INTA AI...")
    inta = IntaAIManager(config)
    
    # Test commands
    test_commands = [
        # Vision commands
        "take a picture",
        "describe what you see",
        "help me navigate",
        "read this text",
        "identify objects",
        
        # Time and date
        "what time is it",
        "what's the date today",
        
        # Fun commands
        "tell me a joke",
        
        # System commands
        "system status",
        "help",
        
        # Audio commands
        "volume up",
        "volume down",
        "mute",
        "unmute",
        
        # Emergency commands
        "emergency",
        "sos",
        
        # Weather and environment
        "what's the weather",
        "measure distance",
        "scan for obstacles",
        
        # Natural conversation
        "hello",
        "how are you",
        "what can you do"
    ]
    
    print(f"\n🎯 Testing {len(test_commands)} commands...")
    print("-" * 50)
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i:2d}. 🎤 Command: '{command}'")
        print("   📝 Response:", end=" ")
        
        try:
            response = inta.process_command(command)
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(0.5)  # Small delay between commands
    
    print("\n" + "="*50)
    print("✅ Command testing complete!")
    print("\n🚀 To test with voice:")
    print("   python main.py")
    print("   Then say any of the commands above!")

if __name__ == "__main__":
    test_commands() 