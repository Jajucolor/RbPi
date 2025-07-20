#!/usr/bin/env python3
"""
Test script for AI Companion functionality
Demonstrates the conversational AI capabilities for the assistive glasses
"""

import sys
import logging
import time
from modules.ai_companion import AICompanion
from modules.speech_manager import SpeechManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_companion_personalities():
    """Test different AI companion personalities"""
    personalities = ["helpful_assistant", "jarvis", "friendly_companion"]
    
    for personality in personalities:
        print(f"\n=== Testing {personality.upper()} personality ===")
        
        # Create companion
        companion = AICompanion(
            api_key=None,  # Will use simulation mode
            personality=personality,
            voice_enabled=False  # Text output only for testing
        )
        
        # Test greeting
        companion.start_companion()
        time.sleep(1)
        
        # Test conversation
        test_inputs = [
            "Hello, how are you?",
            "What can you help me with?",
            "I'm feeling a bit lost today."
        ]
        
        for user_input in test_inputs:
            print(f"\nUser: {user_input}")
            response = companion.handle_conversation(user_input)
            print(f"{companion.personality_config['name']}: {response}")
        
        companion.stop_companion()
        companion.cleanup()
        print(f"\n{personality} test completed.")

def test_vision_analysis_enhancement():
    """Test how the companion enhances vision analysis"""
    print("\n=== Testing Vision Analysis Enhancement ===")
    
    # Create JARVIS companion
    companion = AICompanion(
        api_key=None,  # Simulation mode
        personality="jarvis",
        voice_enabled=False
    )
    
    companion.start_companion()
    
    # Test different vision analysis scenarios
    test_scenarios = [
        "A living room with a couch, coffee table, and TV. There are some books on the table.",
        "An outdoor sidewalk with a tree on the left and a parked car on the right.",
        "A kitchen with counters, a sink, and what appears to be a microwave.",
        "A hallway with doors on both sides and good lighting."
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nScenario {i}: {scenario}")
        enhanced_response = companion.process_vision_analysis(scenario)
        print(f"Enhanced Response: {enhanced_response}")
    
    companion.stop_companion()
    companion.cleanup()

def test_conversation_flow():
    """Test natural conversation flow with context"""
    print("\n=== Testing Conversation Flow ===")
    
    companion = AICompanion(
        api_key=None,  # Simulation mode
        personality="friendly_companion",
        voice_enabled=False
    )
    
    companion.start_companion()
    
    # Simulate a conversation
    conversation = [
        "Hi Iris, I'm about to go for a walk.",
        "I'm a bit nervous about navigating on my own.",
        "Can you help me stay confident?",
        "Thanks, that makes me feel better.",
        "What should I do if I get confused about my location?"
    ]
    
    for user_input in conversation:
        print(f"\nUser: {user_input}")
        response = companion.handle_conversation(user_input)
        print(f"Iris: {response}")
        time.sleep(0.5)  # Simulate natural conversation pace
    
    # Check conversation history
    print(f"\nConversation history length: {len(companion.conversation_history)}")
    summary = companion.get_conversation_summary()
    print(f"Conversation summary:\n{summary}")
    
    companion.stop_companion()
    companion.cleanup()

def test_companion_with_speech():
    """Test companion with actual speech synthesis"""
    print("\n=== Testing Companion with Speech ===")
    
    try:
        # Initialize speech manager
        speech_manager = SpeechManager()
        
        # Create companion with speech enabled
        companion = AICompanion(
            api_key=None,
            personality="jarvis",
            voice_enabled=True
        )
        
        # Connect speech manager
        companion.set_speech_manager(speech_manager)
        
        print("Starting companion with speech... (you should hear audio)")
        companion.start_companion()
        
        # Test a few interactions
        test_phrases = [
            "Hello J.A.R.V.I.S.",
            "What's your status?",
            "Thank you for your help."
        ]
        
        for phrase in test_phrases:
            print(f"\nTesting phrase: {phrase}")
            response = companion.handle_conversation(phrase)
            print(f"Response: {response}")
            time.sleep(3)  # Wait for speech to complete
        
        companion.stop_companion()
        time.sleep(2)  # Wait for farewell
        
        companion.cleanup()
        speech_manager.cleanup()
        
    except Exception as e:
        print(f"Speech test failed: {e}")
        print("This is normal if gTTS/pygame aren't properly configured")

def test_companion_status():
    """Test companion status and configuration"""
    print("\n=== Testing Companion Status ===")
    
    companion = AICompanion(
        personality="jarvis",
        voice_enabled=True
    )
    
    # Check initial status
    status = companion.get_companion_status()
    print("Initial status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Start companion
    companion.start_companion()
    
    # Check active status
    status = companion.get_companion_status()
    print("\nActive status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test personality change
    print("\nTesting personality change...")
    companion.set_personality("friendly_companion")
    
    # Test proactive mode toggle
    print("\nTesting proactive mode toggle...")
    companion.enable_proactive_mode(False)
    companion.enable_proactive_mode(True)
    
    companion.stop_companion()
    companion.cleanup()

def interactive_companion_test():
    """Interactive test where you can chat with the companion"""
    print("\n=== Interactive Companion Test ===")
    print("Type 'quit' to exit, 'capture' to simulate vision analysis")
    
    companion = AICompanion(
        api_key=None,  # Simulation mode - set your API key for real responses
        personality="jarvis",
        voice_enabled=False  # Set to True for speech output
    )
    
    companion.start_companion()
    
    try:
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'capture':
                # Simulate vision analysis
                fake_vision = "A room with chairs and tables, good lighting, clear path ahead"
                response = companion.process_vision_analysis(fake_vision)
                print(f"Vision Analysis: {fake_vision}")
                print(f"J.A.R.V.I.S.: {response}")
            elif user_input:
                response = companion.handle_conversation(user_input)
                print(f"J.A.R.V.I.S.: {response}")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        companion.stop_companion()
        companion.cleanup()

def main():
    """Main test function"""
    print("AI Companion Test Suite for Assistive Glasses")
    print("=" * 50)
    
    tests = [
        ("Companion Personalities", test_companion_personalities),
        ("Vision Analysis Enhancement", test_vision_analysis_enhancement),
        ("Conversation Flow", test_conversation_flow),
        ("Companion Status", test_companion_status),
        ("Speech Integration", test_companion_with_speech),
    ]
    
    try:
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            test_func()
            print(f"✓ {test_name} completed")
        
        print(f"\n{'='*20} All Tests Completed {'='*20}")
        
        # Offer interactive test
        response = input("\nWould you like to try the interactive companion test? (y/n): ").lower()
        if response == 'y':
            interactive_companion_test()
    
    except KeyboardInterrupt:
        print("\nTest suite interrupted")
    except Exception as e:
        print(f"Error in test suite: {e}")

if __name__ == "__main__":
    main() 