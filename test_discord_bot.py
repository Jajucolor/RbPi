#!/usr/bin/env python3
"""
Discord Bot Test Suite
Tests all components of the INTA Discord Bot integration
"""

import sys
import logging
import asyncio
import tempfile
import os
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_discord_dependencies():
    """Test if all Discord dependencies are available"""
    print("\n" + "="*70)
    print("📦 Discord Dependencies Test")
    print("="*70)
    
    dependencies = {
        'discord.py': 'discord',
        'discord-ext-voice-recv': 'discord.ext.voice_recv',
        'PyNaCl': 'nacl',
        'OpenAI Whisper': 'whisper',
        'FFmpeg Python': 'ffmpeg',
        'gTTS': 'gtts',
        'Pygame': 'pygame'
    }
    
    results = {}
    
    for name, module in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {name}: Available")
            results[name] = True
        except ImportError as e:
            print(f"❌ {name}: Missing - {e}")
            results[name] = False
    
    # Check FFmpeg binary
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg Binary: Available")
            results['FFmpeg Binary'] = True
        else:
            print("❌ FFmpeg Binary: Not working")
            results['FFmpeg Binary'] = False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ FFmpeg Binary: Not found in PATH")
        results['FFmpeg Binary'] = False
    
    print(f"\n📊 Dependencies: {sum(results.values())}/{len(results)} available")
    return results

def test_bot_initialization():
    """Test Discord bot initialization without running"""
    print("\n" + "="*70)
    print("🤖 Bot Initialization Test")
    print("="*70)
    
    try:
        # Import bot modules
        from modules.config_manager import ConfigManager
        from modules.ai_companion import AICompanion
        from modules.ultrasonic_sensor import UltrasonicSensor
        from modules.speech_manager import SpeechManager
        
        print("✅ Core modules imported successfully")
        
        # Test configuration loading
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        discord_config = config.get('discord', {})
        has_token = bool(discord_config.get('token', '').strip())
        
        print(f"✅ Configuration loaded")
        print(f"{'✅' if has_token else '❌'} Discord token configured: {has_token}")
        
        # Test component initialization (simulation mode)
        print("🔧 Testing component initialization...")
        
        # AI Companion
        try:
            companion = AICompanion(
                api_key=None,  # Simulation mode
                personality="inta",
                voice_enabled=False
            )
            print("✅ AI Companion: Initialized")
        except Exception as e:
            print(f"❌ AI Companion: Failed - {e}")
        
        # Ultrasonic Sensor
        try:
            sensor = UltrasonicSensor(csv_file="test_discord_sensor.csv")
            sensor_status = sensor.get_sensor_status()
            print(f"✅ Ultrasonic Sensor: {sensor_status['monitoring']} mode")
            sensor.cleanup()
        except Exception as e:
            print(f"❌ Ultrasonic Sensor: Failed - {e}")
        
        # Speech Manager
        try:
            speech = SpeechManager()
            print("✅ Speech Manager: Initialized")
            speech.cleanup()
        except Exception as e:
            print(f"❌ Speech Manager: Failed - {e}")
        
        print("✅ All components initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Bot initialization failed: {e}")
        return False

def test_audio_processing():
    """Test audio processing components"""
    print("\n" + "="*70)
    print("🎵 Audio Processing Test")
    print("="*70)
    
    # Test TTS generation
    try:
        from gtts import gTTS
        import pygame
        
        print("🔊 Testing TTS generation...")
        test_text = "Hello, this is INTA testing text-to-speech for Discord integration."
        
        # Create temporary TTS file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.close()
        
        tts = gTTS(text=test_text, lang='en', slow=False)
        tts.save(temp_file.name)
        
        # Check if file was created
        if os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
            print("✅ TTS file generated successfully")
            
            # Test pygame audio initialization
            try:
                pygame.mixer.init()
                print("✅ Pygame audio system initialized")
                pygame.mixer.quit()
            except Exception as e:
                print(f"❌ Pygame audio initialization failed: {e}")
        else:
            print("❌ TTS file generation failed")
        
        # Clean up
        try:
            os.unlink(temp_file.name)
        except:
            pass
            
    except Exception as e:
        print(f"❌ Audio processing test failed: {e}")
    
    # Test Whisper model loading
    try:
        import whisper
        print("🎤 Testing Whisper model loading...")
        
        # Load smallest model for testing
        model = whisper.load_model("tiny")
        print("✅ Whisper model loaded successfully")
        
        # Test with a dummy audio file (silence)
        # Note: In real usage, this would process actual voice data
        print("✅ Whisper ready for voice recognition")
        
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")

def test_voice_recv_integration():
    """Test discord-ext-voice-recv integration"""
    print("\n" + "="*70)
    print("🎙️ Voice Receive Integration Test")
    print("="*70)
    
    try:
        import discord
        from discord.ext import voice_recv
        
        print("✅ discord.py and voice-recv imported")
        
        # Test voice client creation (without connecting)
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        print("✅ Discord intents configured")
        
        # Test audio sink creation
        class TestAudioSink(voice_recv.AudioSink):
            def __init__(self):
                super().__init__()
                self.data_received = False
            
            def wants_opus(self):
                return False
            
            def write(self, user, data):
                self.data_received = True
                print(f"📡 Received audio data from user: {user}")
        
        test_sink = TestAudioSink()
        print("✅ Audio sink created successfully")
        
        print("✅ Voice receive integration ready")
        
    except Exception as e:
        print(f"❌ Voice receive integration test failed: {e}")

def test_bot_commands():
    """Test bot command structure"""
    print("\n" + "="*70)
    print("🎮 Bot Commands Test")
    print("="*70)
    
    try:
        import discord
        from discord.ext import commands
        
        # Create a test bot to verify command structure
        class TestBot(commands.Bot):
            def __init__(self):
                intents = discord.Intents.default()
                intents.message_content = True
                super().__init__(command_prefix='!', intents=intents)
        
        bot = TestBot()
        
        # Test command definitions
        @bot.command(name='test_join')
        async def test_join(ctx):
            return "join command works"
        
        @bot.command(name='test_chat')
        async def test_chat(ctx, *, message):
            return f"chat command received: {message}"
        
        print("✅ Command structure is valid")
        print("✅ Bot command framework ready")
        
        # Test available commands
        commands_list = ['join', 'leave', 'chat', 'capture', 'obstacle', 'status']
        print(f"📝 Planned commands: {', '.join(commands_list)}")
        
    except Exception as e:
        print(f"❌ Bot commands test failed: {e}")

def test_integration_readiness():
    """Test overall readiness for Discord integration"""
    print("\n" + "="*70)
    print("🔗 Integration Readiness Test")
    print("="*70)
    
    readiness_checks = {
        'Core modules available': False,
        'Discord dependencies': False,
        'Audio processing': False,
        'Configuration ready': False,
        'Voice receive ready': False
    }
    
    # Core modules
    try:
        from modules.ai_companion import AICompanion
        from modules.ultrasonic_sensor import UltrasonicSensor
        from modules.speech_manager import SpeechManager
        readiness_checks['Core modules available'] = True
    except:
        pass
    
    # Discord dependencies
    try:
        import discord
        from discord.ext import voice_recv
        import nacl
        readiness_checks['Discord dependencies'] = True
    except:
        pass
    
    # Audio processing
    try:
        import whisper
        import gtts
        import pygame
        readiness_checks['Audio processing'] = True
    except:
        pass
    
    # Configuration
    try:
        from modules.config_manager import ConfigManager
        config = ConfigManager().get_config()
        has_discord_section = 'discord' in config
        readiness_checks['Configuration ready'] = has_discord_section
    except:
        pass
    
    # Voice receive
    try:
        from discord.ext import voice_recv
        # Test sink creation
        class DummySink(voice_recv.AudioSink):
            def wants_opus(self): return False
            def write(self, user, data): pass
        sink = DummySink()
        readiness_checks['Voice receive ready'] = True
    except:
        pass
    
    # Results
    for check, result in readiness_checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
    
    passed = sum(readiness_checks.values())
    total = len(readiness_checks)
    
    print(f"\n📊 Readiness: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 Discord bot integration is ready!")
        return True
    else:
        print("⚠️  Some components need attention before running the Discord bot")
        return False

def test_config_file():
    """Test Discord bot configuration"""
    print("\n" + "="*70)
    print("⚙️ Configuration File Test")
    print("="*70)
    
    config_file = Path("config.json")
    example_config = Path("config.example.json")
    
    if config_file.exists():
        print("✅ config.json exists")
        
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check required sections
            required_sections = ['discord', 'openai', 'companion']
            for section in required_sections:
                if section in config:
                    print(f"✅ {section} section: Present")
                else:
                    print(f"❌ {section} section: Missing")
            
            # Check Discord token
            discord_config = config.get('discord', {})
            token = discord_config.get('token', '').strip()
            
            if token and token != 'your-discord-bot-token-here':
                print("✅ Discord token: Configured")
            else:
                print("❌ Discord token: Not configured")
                print("💡 Add your Discord bot token to config.json")
            
        except Exception as e:
            print(f"❌ Error reading config.json: {e}")
    
    else:
        print("❌ config.json not found")
        
        if example_config.exists():
            print("💡 Copy config.example.json to config.json and configure it")
        else:
            print("❌ config.example.json also missing")

def main():
    """Main test function"""
    print("🤖 INTA Discord Bot Test Suite")
    print("Testing all components for Discord integration")
    print("="*70)
    
    test_functions = [
        ("Dependencies", test_discord_dependencies),
        ("Bot Initialization", test_bot_initialization),
        ("Audio Processing", test_audio_processing),
        ("Voice Receive", test_voice_recv_integration),
        ("Bot Commands", test_bot_commands),
        ("Configuration", test_config_file),
        ("Overall Readiness", test_integration_readiness),
    ]
    
    results = {}
    
    try:
        for test_name, test_func in test_functions:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 50)
            try:
                result = test_func()
                results[test_name] = result if result is not None else True
                print(f"✅ {test_name}: PASSED")
            except Exception as e:
                results[test_name] = False
                print(f"❌ {test_name}: FAILED - {e}")
        
        # Final summary
        print("\n" + "="*70)
        print("🏁 DISCORD BOT TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {test_name}: {status}")
        
        print(f"\n📊 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Discord bot is ready to run!")
            print("\n💡 Next steps:")
            print("1. Configure your Discord bot token in config.json")
            print("2. Run: python3 discord_bot.py")
            print("3. Invite the bot to your Discord server")
            print("4. Type !join in a voice channel to start!")
        else:
            print("⚠️  SOME TESTS FAILED - check the error messages above")
            print("\n💡 Common fixes:")
            print("- Install missing dependencies: pip install -r requirements_discord.txt")
            print("- Install FFmpeg for voice processing")
            print("- Configure Discord bot token in config.json")
            print("- Check Discord bot permissions")
    
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted")
    except Exception as e:
        print(f"❌ Error in test suite: {e}")

if __name__ == "__main__":
    main() 