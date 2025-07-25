#!/usr/bin/env python3
"""
INTA AI Demo Script
Interactive demonstration of INTA AI assistant capabilities
"""

import time
import json
import logging
from pathlib import Path

# Import the INTA AI manager
from modules.inta_ai_manager import IntaAIManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_config():
    """Load configuration"""
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        print("⚠️  config.json not found. Using default configuration.")
        return {
            "openai": {"api_key": ""},
            "inta": {
                "sample_rate": 8000,
                "chunk_size": 512,
                "vad_aggressiveness": 2,
                "speech_frames_threshold": 3,
                "silence_frames_threshold": 10,
                "realtime_buffer_size": 4096,
                "max_audio_length": 10.0,
                "whisper_model": "tiny"
            }
        }

def print_demo_header():
    """Print demo header"""
    print("=" * 70)
    print("🎤 INTA AI Assistant Demo")
    print("=" * 70)
    print("Welcome to the INTA AI assistant demonstration!")
    print("INTA (Intelligent Navigation and Text Analysis) is an AI assistant")
    print("designed to help visually impaired users navigate and understand")
    print("their surroundings through natural voice interaction.")
    print()

def print_capabilities():
    """Print INTA capabilities"""
    print("🔧 INTA Capabilities:")
    print("• Voice Recognition: Understands natural speech using Whisper")
    print("• Command Execution: Controls assistive glasses functions")
    print("• Context Awareness: Maintains conversation history")
    print("• Accessibility: Designed for visually impaired users")
    print()

def print_example_commands():
    """Print example commands"""
    print("💬 Example Voice Commands:")
    print("• 'Hello INTA, how are you?'")
    print("• 'Take a picture of my surroundings'")
    print("• 'What do you see in front of me?'")
    print("• 'Is there any text I should know about?'")
    print("• 'Help me navigate safely'")
    print("• 'What time is it?'")
    print("• 'Tell me about the weather'")
    print("• 'Shutdown the system'")
    print()

def demo_text_conversation(inta):
    """Demo text-based conversation"""
    print("\n" + "=" * 50)
    print("💬 Text Conversation Demo")
    print("=" * 50)
    print("Let's have a conversation with INTA!")
    print("Type your messages and press Enter.")
    print("Type 'demo' to see more examples, 'quit' to end.")
    print()
    
    # Pre-defined demo responses for when AI is not configured
    demo_responses = [
        "Hello! I'm INTA, your AI assistant. I'm here to help you navigate and understand your surroundings.",
        "I can help you take pictures, analyze your environment, read text, and provide navigation assistance.",
        "I'm designed to work with assistive glasses to make your daily activities easier and safer.",
        "I can understand natural language commands and maintain context throughout our conversation.",
        "My voice recognition uses Whisper AI, and I can process commands through OpenAI.",
        "I'm constantly listening for your voice commands, so you can interact hands-free.",
        "I can help you identify objects, read signs, and describe what's around you.",
        "I'm here to provide companionship and assistance whenever you need me."
    ]
    
    demo_index = 0
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Ending conversation demo...")
                break
            
            if user_input.lower() == 'demo':
                print("\n🎯 Demo Examples:")
                print("• 'What can you do?'")
                print("• 'How do you help visually impaired users?'")
                print("• 'Tell me about your voice recognition'")
                print("• 'What AI systems do you use?'")
                print("• 'How do you process commands?'")
                print("• 'What makes you special?'")
                print("• 'How do you maintain context?'")
                print("• 'What's your role in assistive technology?'")
                print()
                continue
            
            if user_input:
                print("INTA: ", end="", flush=True)
                
                # Simulate typing effect
                response = inta.process_command(user_input)
                
                # If no AI backend configured, use demo responses
                if "couldn't process" in response.lower() or "couldn't process" in response.lower():
                    response = demo_responses[demo_index % len(demo_responses)]
                    demo_index += 1
                
                # Print response with typing effect
                for char in response:
                    print(char, end="", flush=True)
                    time.sleep(0.02)
                print()
                
            else:
                print("Please enter a message.")
                
        except KeyboardInterrupt:
            print("\nConversation demo interrupted.")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def demo_voice_recognition(inta):
    """Demo voice recognition capabilities"""
    print("\n" + "=" * 50)
    print("🎤 Voice Recognition Demo")
    print("=" * 50)
    print("This demo shows INTA's voice recognition capabilities.")
    print("Note: This requires a microphone and Whisper model.")
    print()
    
    status = inta.get_status()
    
    if not status["whisper_available"]:
        print("❌ Whisper not available. Install with: pip install openai-whisper")
        return
    
    if not status["audio_available"]:
        print("❌ Audio recording not available. Install PyAudio.")
        return
    
    print("✅ Voice recognition components available!")
    print("To test voice recognition:")
    print("1. Run: python test_inta_ai.py")
    print("2. Select option 1: 'Start continuous listening'")
    print("3. Speak clearly into your microphone")
    print("4. Try commands like 'Hello INTA' or 'Take a picture'")
    print()

def demo_function_execution(inta):
    """Demo function execution"""
    print("\n" + "=" * 50)
    print("🔧 Function Execution Demo")
    print("=" * 50)
    print("INTA can execute various functions based on voice commands:")
    print()
    
    functions = [
        ("capture_image", "Take a picture of surroundings"),
        ("describe_surroundings", "Analyze and describe environment"),
        ("navigate", "Provide navigation assistance"),
        ("read_text", "Read any visible text"),
        ("identify_objects", "Identify objects in environment")
    ]
    
    for func_name, description in functions:
        print(f"• {func_name}: {description}")
        response = inta.execute_function(func_name)
        print(f"  Response: {response}")
        time.sleep(0.5)
    
    print()

def demo_ai_integration(inta):
    """Demo AI integration capabilities"""
    print("\n" + "=" * 50)
    print("🤖 AI Integration Demo")
    print("=" * 50)
    
    status = inta.get_status()
    
    print("AI Backend Status:")
    print(f"• OpenAI Configured: {status['openai_configured']}")
    print(f"• Conversation History: {status['conversation_length']} messages")
    print()

    
    if status['openai_configured']:
        print("✅ OpenAI AI backend available")
        print("OpenAI provides AI processing capabilities for natural conversation.")
    else:
        print("⚠️  OpenAI not configured")
        print("To enable OpenAI:")
        print("1. Get API key from https://platform.openai.com/")
        print("2. Add to config.json")
        print()

def main():
    """Main demo function"""
    print_demo_header()
    
    # Load configuration
    config = load_config()
    
    # Initialize INTA AI
    print("Initializing INTA AI...")
    inta = IntaAIManager(config)
    
    # Check status
    status = inta.get_status()
    print(f"✅ INTA AI initialized successfully")
    print(f"   Voice Recognition: {'✅' if status['whisper_available'] else '❌'}")
    print(f"   Audio Recording: {'✅' if status['audio_available'] else '❌'}")
    print()
    
    # Show capabilities
    print_capabilities()
    
    # Show example commands
    print_example_commands()
    
    # Demo options
    while True:
        print("🎯 Demo Options:")
        print("1. Text Conversation Demo")
        print("2. Voice Recognition Demo")
        print("3. Function Execution Demo")
        print("4. AI Integration Demo")
        print("5. Exit")
        print()
        
        try:
            choice = input("Select demo option (1-5): ").strip()
            
            if choice == "1":
                demo_text_conversation(inta)
            elif choice == "2":
                demo_voice_recognition(inta)
            elif choice == "3":
                demo_function_execution(inta)
            elif choice == "4":
                demo_ai_integration(inta)
            elif choice == "5":
                break
            else:
                print("Invalid choice. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user.")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Cleanup
    inta.cleanup()
    
    print("\n" + "=" * 70)
    print("🎉 INTA AI Demo Complete!")
    print("=" * 70)
    print("Thank you for trying INTA AI!")
    print()
    print("Next steps:")
    print("• Run 'python test_inta_ai.py' for full testing")
    print("• Run 'python main.py' to use with assistive glasses")
    print("• See README_INTA.md for detailed documentation")
    print("• Configure OpenAI for enhanced capabilities")
    print()
    print("Happy exploring! 🚀")

if __name__ == "__main__":
    main() 