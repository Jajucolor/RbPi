#!/usr/bin/env python3
"""
INTA Conversation Test
Demonstrates the constant listening and conversation capabilities of INTA
"""

import sys
import logging
import time
from modules.ai_companion import AICompanion
from modules.speech_manager import SpeechManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_inta_constant_listening():
    """Test INTA's constant listening and conversation capabilities"""
    print("\n" + "="*60)
    print("INTA - Intelligent Navigation and Assistance Companion")
    print("Constant Listening Mode Test")
    print("="*60)
    
    # Create INTA companion
    inta = AICompanion(
        api_key=None,  # Simulation mode - set your OpenAI API key for real AI responses
        personality="inta",
        voice_enabled=False  # Set to True for speech output
    )
    
    print("\n🎯 Starting INTA...")
    inta.start_companion()
    time.sleep(1)
    
    print("\n🎙️ INTA is now constantly listening and ready to respond to everything you say!")
    print("💬 Examples of natural conversation with INTA:")
    
    # Example conversations showing constant listening
    conversations = [
        "Hi INTA, how are you today?",
        "I'm feeling a bit nervous about walking outside",
        "What should I do if I get lost?",
        "Can you tell me what's around me?",
        "I heard a strange noise, what could it be?",
        "Thank you for being so helpful",
        "Tell me a joke to cheer me up",
        "I'm ready to go out now"
    ]
    
    for i, user_input in enumerate(conversations, 1):
        print(f"\n[Example {i}]")
        print(f"👤 You: {user_input}")
        
        # Get INTA's response
        response = inta.handle_conversation(user_input)
        print(f"🤖 INTA: {response}")
        
        time.sleep(1)  # Brief pause between conversations
    
    print("\n" + "="*60)
    print("🖼️ Testing Vision Analysis Enhancement")
    print("="*60)
    
    # Test vision analysis enhancement
    vision_scenarios = [
        "A busy street with cars, pedestrians, and traffic lights",
        "A quiet park with benches, trees, and a walking path",
        "A grocery store aisle with shelves of products",
        "A home kitchen with counters, appliances, and a table"
    ]
    
    for i, scenario in enumerate(vision_scenarios, 1):
        print(f"\n[Vision Test {i}]")
        print(f"📷 Raw Vision: {scenario}")
        
        enhanced_response = inta.process_vision_analysis(scenario)
        print(f"🤖 INTA Enhanced: {enhanced_response}")
        
        time.sleep(1)
    
    print("\n" + "="*60)
    print("🔄 Testing Proactive Check-ins")
    print("="*60)
    
    print("⏰ Simulating idle time - INTA should check in proactively...")
    time.sleep(2)
    
    # Simulate proactive check-in
    inta._proactive_check_in()
    
    print("\n" + "="*60)
    print("📊 INTA Status Summary")
    print("="*60)
    
    status = inta.get_companion_status()
    print(f"🤖 Companion: {status['name']}")
    print(f"✅ Active: {status['active']}")
    print(f"🗣️ Voice Enabled: {status['voice_enabled']}")
    print(f"🔄 Proactive Mode: {status['proactive_mode']}")
    print(f"💬 Conversation Length: {status['conversation_length']}")
    print(f"🧠 OpenAI Available: {status['openai_available']}")
    
    print("\n👋 Stopping INTA...")
    inta.stop_companion()
    time.sleep(1)
    
    inta.cleanup()
    print("✅ INTA test completed!")

def interactive_inta_chat():
    """Interactive chat session with INTA"""
    print("\n" + "="*60)
    print("🎙️ Interactive INTA Chat Session")
    print("="*60)
    print("💡 INTA is in constant listening mode - just type naturally!")
    print("📝 Type 'capture' to simulate vision analysis")
    print("🚪 Type 'quit' to exit")
    print("="*60)
    
    inta = AICompanion(
        api_key=None,  # Set your OpenAI API key for real AI responses
        personality="inta",
        voice_enabled=False  # Set to True for speech output
    )
    
    inta.start_companion()
    
    try:
        while True:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'capture':
                # Simulate vision analysis
                print("📷 [Simulating camera capture...]")
                fake_vision = "A well-lit room with a couch, coffee table, and TV. Clear walking path with no obstacles."
                response = inta.process_vision_analysis(fake_vision)
                print(f"🤖 INTA: {response}")
            elif user_input:
                response = inta.handle_conversation(user_input)
                print(f"🤖 INTA: {response}")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Session interrupted")
    finally:
        print("\n👋 Goodbye! INTA signing off...")
        inta.stop_companion()
        inta.cleanup()

def test_with_speech():
    """Test INTA with actual speech synthesis"""
    print("\n" + "="*60)
    print("🔊 Testing INTA with Speech Output")
    print("="*60)
    
    try:
        # Initialize speech manager
        speech_manager = SpeechManager()
        
        # Create INTA with speech enabled
        inta = AICompanion(
            api_key=None,
            personality="inta",
            voice_enabled=True
        )
        
        # Connect speech manager
        inta.set_speech_manager(speech_manager)
        
        print("🔊 Starting INTA with speech output...")
        inta.start_companion()
        
        # Test a few interactions with speech
        test_phrases = [
            "Hello INTA, nice to meet you!",
            "How can you help me navigate?",
            "I'm ready to explore the world with you."
        ]
        
        for phrase in test_phrases:
            print(f"\n👤 You: {phrase}")
            response = inta.handle_conversation(phrase)
            print(f"🤖 INTA: {response}")
            print("🔊 [INTA is speaking...]")
            time.sleep(4)  # Wait for speech to complete
        
        inta.stop_companion()
        time.sleep(2)  # Wait for farewell speech
        
        inta.cleanup()
        speech_manager.cleanup()
        
        print("✅ Speech test completed!")
        
    except Exception as e:
        print(f"❌ Speech test failed: {e}")
        print("💡 This is normal if gTTS/pygame aren't properly configured")

def main():
    """Main test function for INTA"""
    print("🤖 INTA (Intelligent Navigation and Assistance Companion)")
    print("Constant Listening Mode Test Suite")
    print("="*70)
    
    tests = [
        ("🎯 Constant Listening Demo", test_inta_constant_listening),
        ("🔊 Speech Integration Test", test_with_speech),
    ]
    
    try:
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            test_func()
            print(f"✅ {test_name} completed")
        
        print(f"\n{'='*20} All Tests Completed {'='*20}")
        
        # Offer interactive chat
        response = input("\n💬 Would you like to try interactive chat with INTA? (y/n): ").lower()
        if response == 'y':
            interactive_inta_chat()
    
    except KeyboardInterrupt:
        print("\n\n🛑 Test suite interrupted")
    except Exception as e:
        print(f"❌ Error in test suite: {e}")

if __name__ == "__main__":
    main() 