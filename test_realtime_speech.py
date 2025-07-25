#!/usr/bin/env python3
"""
Test Real-Time Speech System
Demonstrates word-by-word speech generation
"""

import time
import logging
from modules.realtime_speech_manager import RealtimeSpeechManager

def test_realtime_speech():
    """Test real-time speech functionality"""
    logging.basicConfig(level=logging.INFO)
    
    print("🎙️ REAL-TIME SPEECH TEST")
    print("="*50)
    
    # Initialize real-time speech manager
    speech = RealtimeSpeechManager(volume=0.9, language='en', slow=False)
    
    # Configure for very fast real-time speech
    speech.set_realtime_settings(
        word_delay=0.03,  # Very fast
        sentence_delay=0.1,  # Short pause
        chunk_size=1  # One word at a time
    )
    
    # Set up callbacks to see progress
    def on_word_spoken(word):
        print(f"🗣️  Spoke: '{word}'")
    
    def on_sentence_complete(sentence):
        print(f"📝 Sentence complete: '{sentence}'")
    
    speech.set_callbacks(on_word_spoken, on_sentence_complete)
    
    try:
        print("\n🚀 Testing real-time speech...")
        print("You should hear each word spoken as it's processed!")
        
        # Test 1: Short response
        print("\n1️⃣ Test 1: Short response")
        test_text1 = "Hello! I am speaking in real-time."
        speech.speak_realtime(test_text1)
        time.sleep(5)
        
        # Test 2: Medium response
        print("\n2️⃣ Test 2: Medium response")
        test_text2 = "This is a longer response that demonstrates how the system speaks each word as it is generated. It makes conversations much more natural and responsive."
        speech.speak_realtime(test_text2)
        time.sleep(10)
        
        # Test 3: Command response
        print("\n3️⃣ Test 3: Command response")
        test_text3 = "I can see a table with a laptop on it. There is also a coffee cup nearby. The room appears to be well-lit."
        speech.speak_realtime(test_text3)
        time.sleep(8)
        
        print("\n✅ Real-time speech test complete!")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    finally:
        speech.cleanup()

def test_speed_comparison():
    """Compare real-time vs traditional speech"""
    logging.basicConfig(level=logging.INFO)
    
    print("\n⚡ SPEED COMPARISON TEST")
    print("="*50)
    
    speech = RealtimeSpeechManager(volume=0.9, language='en', slow=False)
    
    test_text = "This is a test to compare the speed of real-time speech versus traditional speech generation."
    
    try:
        # Test traditional speech
        print("\n🐌 Traditional speech (waiting for complete response):")
        start_time = time.time()
        speech.speak(test_text)
        traditional_time = time.time() - start_time
        print(f"⏱️  Traditional time: {traditional_time:.2f} seconds")
        
        time.sleep(2)
        
        # Test real-time speech
        print("\n⚡ Real-time speech (word-by-word):")
        start_time = time.time()
        speech.speak_realtime(test_text)
        time.sleep(8)  # Wait for completion
        realtime_time = time.time() - start_time
        print(f"⏱️  Real-time time: {realtime_time:.2f} seconds")
        
        print(f"\n📊 Comparison:")
        print(f"   Traditional: {traditional_time:.2f}s")
        print(f"   Real-time: {realtime_time:.2f}s")
        print(f"   Difference: {abs(traditional_time - realtime_time):.2f}s")
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    finally:
        speech.cleanup()

if __name__ == "__main__":
    print("🎯 Choose test:")
    print("1. Real-time speech demo")
    print("2. Speed comparison")
    print("3. Both tests")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_realtime_speech()
    elif choice == "2":
        test_speed_comparison()
    elif choice == "3":
        test_realtime_speech()
        test_speed_comparison()
    else:
        print("Invalid choice. Running real-time speech demo...")
        test_realtime_speech() 