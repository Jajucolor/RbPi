#!/usr/bin/env python3
"""
Test script for gTTS functionality
Simple test to verify Google Text-to-Speech is working correctly
"""

import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_gtts_import():
    """Test if gTTS can be imported"""
    try:
        from gtts import gTTS
        print("✓ gTTS imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import gTTS: {e}")
        return False

def test_pygame_import():
    """Test if pygame can be imported"""
    try:
        import pygame
        print("✓ pygame imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import pygame: {e}")
        return False

def test_gtts_creation():
    """Test creating a gTTS object"""
    try:
        from gtts import gTTS
        tts = gTTS(text="Hello, this is a test", lang='en', slow=False)
        print("✓ gTTS object created successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to create gTTS object: {e}")
        return False

def test_pygame_mixer():
    """Test pygame mixer initialization"""
    try:
        import pygame
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=4096)
        pygame.mixer.init()
        print("✓ pygame mixer initialized successfully")
        pygame.mixer.quit()
        return True
    except Exception as e:
        print(f"✗ Failed to initialize pygame mixer: {e}")
        return False

def test_speech_manager():
    """Test the speech manager module"""
    try:
        from modules.speech_manager import SpeechManager
        speech = SpeechManager()
        print("✓ SpeechManager created successfully")
        
        # Test status
        status = speech.get_speech_status()
        print(f"✓ Speech status: {status}")
        
        # Cleanup
        speech.cleanup()
        return True
    except Exception as e:
        print(f"✗ Failed to test SpeechManager: {e}")
        return False

def main():
    """Main test function"""
    print("Testing gTTS integration for assistive glasses...\n")
    
    tests = [
        ("gTTS Import", test_gtts_import),
        ("pygame Import", test_pygame_import),
        ("gTTS Creation", test_gtts_creation),
        ("pygame Mixer", test_pygame_mixer),
        ("Speech Manager", test_speech_manager)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- Testing {test_name} ---")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n--- Test Summary ---")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! gTTS integration is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please install missing dependencies:")
        print("\nFor Raspberry Pi, try:")
        print("pip install gTTS pygame")
        print("sudo apt install -y python3-pygame")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 