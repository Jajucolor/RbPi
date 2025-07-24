#!/usr/bin/env python3
"""
Simple Audio Test Script
Test audio recording and processing for INTA AI
"""

import time
import tempfile
import os
import struct
import numpy as np

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("❌ PyAudio not available")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("❌ Whisper not available")

def test_audio_recording():
    """Test basic audio recording"""
    if not PYAUDIO_AVAILABLE:
        print("Cannot test audio recording - PyAudio not available")
        return False
    
    print("🎤 Testing audio recording...")
    
    try:
        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        
        # Audio settings
        sample_rate = 16000
        chunk_size = 1024
        channels = 1
        format_type = pyaudio.paInt16
        
        # Open stream
        stream = audio.open(
            format=format_type,
            channels=channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size
        )
        
        print("✅ Audio stream opened successfully")
        print("Recording 3 seconds of audio...")
        
        frames = []
        for i in range(0, int(sample_rate / chunk_size * 3)):  # 3 seconds
            data = stream.read(chunk_size, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        audio_data = b''.join(frames)
        print(f"✅ Recorded {len(audio_data)} bytes of audio")
        
        return audio_data
        
    except Exception as e:
        print(f"❌ Audio recording failed: {e}")
        return None

def test_wav_creation(audio_data):
    """Test WAV file creation"""
    if not audio_data:
        print("No audio data to test")
        return None
    
    print("\n📁 Testing WAV file creation...")
    
    try:
        # Create WAV file with proper header
        sample_rate = 16000
        channels = 1
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            # WAV header for 16-bit PCM, 1 channel, 16000 Hz
            wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
                b'RIFF',
                36 + len(audio_data),  # File size
                b'WAVE',
                b'fmt ',
                16,  # fmt chunk size
                1,   # Audio format (PCM)
                channels,   # Number of channels
                sample_rate,  # Sample rate
                sample_rate * channels * 2,  # Byte rate
                channels * 2,   # Block align
                16,  # Bits per sample
                b'data',
                len(audio_data)  # Data size
            )
            
            temp_file.write(wav_header)
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        print(f"✅ WAV file created: {temp_file_path}")
        print(f"   File size: {os.path.getsize(temp_file_path)} bytes")
        
        return temp_file_path
        
    except Exception as e:
        print(f"❌ WAV creation failed: {e}")
        return None

def test_whisper_transcription(wav_file):
    """Test Whisper transcription"""
    if not WHISPER_AVAILABLE:
        print("Cannot test Whisper - not available")
        return False
    
    if not wav_file:
        print("No WAV file to test")
        return False
    
    print("\n🤖 Testing Whisper transcription...")
    
    try:
        # Load Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model("tiny")  # Use tiny for faster testing
        print("✅ Whisper model loaded")
        
        # Transcribe
        print("Transcribing audio...")
        result = model.transcribe(wav_file)
        
        transcription = result["text"].strip()
        print(f"✅ Transcription: '{transcription}'")
        
        return transcription
        
    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        return None

def main():
    """Main test function"""
    print("=" * 50)
    print("🎤 Audio Test for INTA AI")
    print("=" * 50)
    
    # Test audio recording
    audio_data = test_audio_recording()
    
    if audio_data:
        # Test WAV creation
        wav_file = test_wav_creation(audio_data)
        
        if wav_file:
            # Test Whisper transcription
            transcription = test_whisper_transcription(wav_file)
            
            # Clean up
            try:
                os.unlink(wav_file)
                print(f"\n🗑️  Cleaned up temporary file: {wav_file}")
            except:
                pass
            
            if transcription:
                print("\n🎉 All audio tests passed!")
                print("INTA AI audio system is working correctly.")
            else:
                print("\n⚠️  Audio recording works, but transcription failed.")
        else:
            print("\n⚠️  Audio recording works, but WAV creation failed.")
    else:
        print("\n❌ Audio recording failed. Check your microphone setup.")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main() 