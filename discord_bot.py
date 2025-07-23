#!/usr/bin/env python3
"""
INTA Assistive Glasses Discord Bot
Integrates the complete assistive glasses system into Discord voice channels
Uses discord-ext-voice-recv for voice receiving and processing
"""

import discord
from discord.ext import commands, voice_recv
import asyncio
import logging
import threading
import tempfile
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
import io
import wave

# Import our existing modules
from modules.ai_companion import AICompanion
from modules.ultrasonic_sensor import UltrasonicSensor
from modules.camera_manager import CameraManager
from modules.vision_analyzer import VisionAnalyzer
from modules.speech_manager import SpeechManager
from modules.config_manager import ConfigManager
from modules.voice_command_manager import VoiceCommandManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class INTADiscordBot(commands.Bot):
    """Discord bot integrating INTA assistive glasses system"""
    
    def __init__(self):
        # Discord bot setup
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description="INTA Assistive Glasses System - Your AI companion for navigation and assistance"
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Initialize system components
        self.initialize_components()
        
        # Discord-specific state
        self.voice_clients: Dict[int, discord.VoiceClient] = {}  # guild_id -> voice_client
        self.active_channels: Dict[int, dict] = {}  # guild_id -> channel_info
        self.user_states: Dict[int, dict] = {}  # user_id -> state info
        
        # Audio processing
        self.whisper_model = None
        self.processing_audio = {}  # user_id -> processing state
        
        self.logger.info("🤖 INTA Discord Bot initialized")
    
    def initialize_components(self):
        """Initialize all system components"""
        try:
            # Initialize AI companion (INTA)
            companion_config = self.config.get('companion', {})
            self.ai_companion = AICompanion(
                api_key=self.config.get('openai_api_key'),
                personality=companion_config.get('personality', 'inta'),
                voice_enabled=False  # Discord handles voice output
            )
            
            # Initialize speech manager for TTS
            self.speech_manager = SpeechManager()
            self.ai_companion.set_speech_manager(self.speech_manager)
            
            # Initialize camera and vision analyzer
            self.camera_manager = CameraManager()
            self.vision_analyzer = VisionAnalyzer(self.config.get('openai_api_key'))
            
            # Initialize ultrasonic sensor
            sensor_config = self.config.get('ultrasonic_sensor', {})
            self.ultrasonic_sensor = UltrasonicSensor(
                trigger_pin=sensor_config.get('trigger_pin', 23),
                echo_pin=sensor_config.get('echo_pin', 24),
                obstacle_threshold_cm=sensor_config.get('obstacle_threshold_cm', 100.0),
                csv_file=sensor_config.get('csv_file', 'discord_distance_log.csv')
            )
            
            # Set up obstacle detection callbacks
            self.ultrasonic_sensor.set_obstacle_callback(self.handle_obstacle_detection)
            self.ultrasonic_sensor.set_distance_callback(self.handle_distance_update)
            
            # Initialize Whisper for voice recognition
            self.initialize_whisper()
            
            self.logger.info("✅ All system components initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing components: {e}")
            raise
    
    def initialize_whisper(self):
        """Initialize OpenAI Whisper for voice recognition"""
        try:
            import whisper
            model_size = self.config.get('whisper', {}).get('model', 'base')
            self.whisper_model = whisper.load_model(model_size)
            self.logger.info(f"🎤 Whisper model '{model_size}' loaded")
        except ImportError:
            self.logger.error("❌ OpenAI Whisper not installed. Install with: pip install openai-whisper")
            self.whisper_model = None
        except Exception as e:
            self.logger.error(f"❌ Error loading Whisper: {e}")
            self.whisper_model = None
    
    async def on_ready(self):
        """Called when bot is ready"""
        self.logger.info(f"🚀 {self.user} is online and ready!")
        self.logger.info(f"📡 Bot is in {len(self.guilds)} guilds")
        
        # Start INTA companion
        self.ai_companion.start_companion()
        
        # Start obstacle detection monitoring
        sensor_interval = self.config.get('ultrasonic_sensor', {}).get('reading_interval', 1.0)
        self.ultrasonic_sensor.start_monitoring(reading_interval=sensor_interval)
        
        # Set Discord activity
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="for voice commands | !join to start"
        )
        await self.change_presence(activity=activity)
    
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state changes"""
        if member == self.user:
            return
        
        guild_id = member.guild.id
        
        # User joined voice channel
        if before.channel is None and after.channel is not None:
            if guild_id in self.active_channels:
                await self.announce_user_join(member, after.channel)
        
        # User left voice channel
        elif before.channel is not None and after.channel is None:
            if guild_id in self.active_channels:
                await self.announce_user_leave(member, before.channel)
    
    async def announce_user_join(self, member, channel):
        """Announce when a user joins the voice channel"""
        welcome_msg = f"Hello {member.display_name}! I'm INTA, your AI assistant. I can help with navigation, describe images, and chat with you. Just start speaking!"
        response = self.ai_companion.handle_conversation(
            f"A new user named {member.display_name} just joined the voice channel. Please welcome them."
        )
        await self.speak_in_channel(channel.guild.id, response)
    
    async def announce_user_leave(self, member, channel):
        """Announce when a user leaves the voice channel"""
        farewell = f"Goodbye {member.display_name}! Take care and stay safe out there."
        await self.speak_in_channel(channel.guild.id, farewell)
    
    @commands.command(name='join')
    async def join_voice(self, ctx):
        """Join the user's voice channel"""
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel for me to join!")
            return
        
        channel = ctx.author.voice.channel
        
        try:
            # Join with voice receive client
            voice_client = await channel.connect(cls=voice_recv.VoiceRecvClient)
            
            # Create audio sink for processing voice
            sink = INTAAudioSink(self, ctx.guild.id)
            voice_client.listen(sink)
            
            # Store voice client
            self.voice_clients[ctx.guild.id] = voice_client
            self.active_channels[ctx.guild.id] = {
                'channel': channel,
                'text_channel': ctx.channel,
                'started_at': time.time()
            }
            
            # INTA greeting
            greeting = self.ai_companion.handle_conversation(
                f"I just joined the voice channel '{channel.name}' in the Discord server '{ctx.guild.name}'. Please introduce yourself to everyone."
            )
            
            await ctx.send(f"✅ Joined **{channel.name}**! INTA is now listening and ready to assist.")
            await self.speak_in_channel(ctx.guild.id, greeting)
            
            self.logger.info(f"🔊 Joined voice channel: {channel.name} in {ctx.guild.name}")
            
        except Exception as e:
            await ctx.send(f"❌ Failed to join voice channel: {str(e)}")
            self.logger.error(f"Error joining voice: {e}")
    
    @commands.command(name='leave')
    async def leave_voice(self, ctx):
        """Leave the voice channel"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.voice_clients:
            await ctx.send("❌ I'm not in a voice channel!")
            return
        
        try:
            # INTA farewell
            farewell = self.ai_companion.handle_conversation(
                "I'm about to leave the voice channel. Please say goodbye to everyone."
            )
            await self.speak_in_channel(guild_id, farewell)
            
            # Wait a moment for farewell to play
            await asyncio.sleep(3)
            
            # Disconnect
            voice_client = self.voice_clients[guild_id]
            await voice_client.disconnect()
            
            # Clean up
            del self.voice_clients[guild_id]
            if guild_id in self.active_channels:
                del self.active_channels[guild_id]
            
            await ctx.send("👋 Left the voice channel. See you later!")
            self.logger.info(f"🔇 Left voice channel in {ctx.guild.name}")
            
        except Exception as e:
            await ctx.send(f"❌ Error leaving voice channel: {str(e)}")
            self.logger.error(f"Error leaving voice: {e}")
    
    @commands.command(name='capture', aliases=['picture', 'image', 'see'])
    async def capture_image(self, ctx):
        """Capture and analyze an image"""
        try:
            await ctx.send("📸 Capturing image...")
            
            # Capture image
            image_path = self.camera_manager.capture_image()
            if not image_path:
                await ctx.send("❌ Failed to capture image")
                return
            
            await ctx.send("🔍 Analyzing image with INTA...")
            
            # Analyze with vision API
            vision_result = await asyncio.get_event_loop().run_in_executor(
                None, self.vision_analyzer.analyze_image, image_path
            )
            
            if not vision_result:
                await ctx.send("❌ Failed to analyze image")
                return
            
            # Process with INTA for enhanced response
            enhanced_description = self.ai_companion.process_vision_analysis(
                vision_result, f"Image captured from Discord by {ctx.author.display_name}"
            )
            
            # Send text response
            await ctx.send(f"👁️ **Vision Analysis:**\n{enhanced_description}")
            
            # Speak response if in voice channel
            if ctx.guild.id in self.voice_clients:
                await self.speak_in_channel(ctx.guild.id, enhanced_description)
            
            # Send image
            with open(image_path, 'rb') as f:
                await ctx.send(file=discord.File(f, 'captured_image.jpg'))
            
            self.logger.info(f"📷 Image captured and analyzed for {ctx.author}")
            
        except Exception as e:
            await ctx.send(f"❌ Error capturing image: {str(e)}")
            self.logger.error(f"Error in image capture: {e}")
    
    @commands.command(name='obstacle')
    async def obstacle_status(self, ctx):
        """Get current obstacle detection status"""
        try:
            status = self.ultrasonic_sensor.get_sensor_status()
            recent_readings = self.ultrasonic_sensor.get_recent_readings(5)
            
            embed = discord.Embed(
                title="🔍 Obstacle Detection Status",
                color=discord.Color.blue()
            )
            
            # Status info
            embed.add_field(
                name="📡 Sensor Status",
                value=f"**Monitoring:** {'✅ Active' if status['monitoring'] else '❌ Inactive'}\n"
                      f"**Mode:** {'🖥️ Simulation' if status['simulation_mode'] else '🔧 Hardware'}\n"
                      f"**Last Distance:** {status['last_distance_cm']}cm" if status['last_distance_cm'] else "No readings",
                inline=False
            )
            
            # Recent readings
            if recent_readings:
                readings_text = ""
                for reading in recent_readings[-3:]:  # Last 3 readings
                    timestamp = reading['timestamp'].split('T')[1][:8]
                    icon = "🚨" if reading['is_obstacle'] else "✅"
                    readings_text += f"{icon} {timestamp}: {reading['distance_cm']}cm ({reading['obstacle_level']})\n"
                
                embed.add_field(
                    name="📊 Recent Readings",
                    value=readings_text,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error getting obstacle status: {str(e)}")
    
    @commands.command(name='chat')
    async def chat_with_inta(self, ctx, *, message):
        """Chat with INTA via text"""
        try:
            response = self.ai_companion.handle_conversation(
                f"Discord user {ctx.author.display_name} says: {message}"
            )
            
            await ctx.send(f"🤖 **INTA:** {response}")
            
            # Also speak if in voice channel
            if ctx.guild.id in self.voice_clients:
                await self.speak_in_channel(ctx.guild.id, response)
            
        except Exception as e:
            await ctx.send(f"❌ Error chatting with INTA: {str(e)}")
    
    @commands.command(name='status')
    async def bot_status(self, ctx):
        """Get bot status and information"""
        embed = discord.Embed(
            title="🤖 INTA Assistive Glasses Bot Status",
            color=discord.Color.green()
        )
        
        # Basic info
        embed.add_field(
            name="🔊 Voice Channels",
            value=f"Connected to: {len(self.voice_clients)} channels",
            inline=True
        )
        
        # Components status
        components_status = "✅ AI Companion (INTA)\n"
        components_status += "✅ Speech Manager\n" 
        components_status += f"{'✅' if self.camera_manager else '❌'} Camera Manager\n"
        components_status += f"{'✅' if self.ultrasonic_sensor.monitoring else '❌'} Obstacle Detection\n"
        components_status += f"{'✅' if self.whisper_model else '❌'} Voice Recognition\n"
        
        embed.add_field(
            name="🔧 Components",
            value=components_status,
            inline=True
        )
        
        # Commands
        embed.add_field(
            name="📝 Available Commands",
            value="!join - Join voice channel\n"
                  "!leave - Leave voice channel\n"
                  "!capture - Take a picture\n"
                  "!obstacle - Obstacle status\n"
                  "!chat <message> - Chat with INTA\n"
                  "!status - This status\n"
                  "Or just speak in voice channel!",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    async def speak_in_channel(self, guild_id: int, text: str):
        """Speak text in the voice channel using TTS"""
        if guild_id not in self.voice_clients:
            return
        
        try:
            # Generate TTS audio
            audio_file = await asyncio.get_event_loop().run_in_executor(
                None, self.generate_tts_audio, text
            )
            
            if audio_file:
                voice_client = self.voice_clients[guild_id]
                
                # Play audio in Discord voice channel
                if not voice_client.is_playing():
                    source = discord.FFmpegPCMAudio(audio_file)
                    voice_client.play(source)
                    
                    # Wait for audio to finish
                    while voice_client.is_playing():
                        await asyncio.sleep(0.1)
                    
                    # Clean up temp file
                    try:
                        os.unlink(audio_file)
                    except:
                        pass
        
        except Exception as e:
            self.logger.error(f"Error speaking in channel: {e}")
    
    def generate_tts_audio(self, text: str) -> Optional[str]:
        """Generate TTS audio file"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.close()
            
            # Generate TTS
            from gtts import gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_file.name)
            
            return temp_file.name
            
        except Exception as e:
            self.logger.error(f"Error generating TTS: {e}")
            return None
    
    def handle_obstacle_detection(self, reading, analysis):
        """Handle obstacle detection from ultrasonic sensor"""
        try:
            # Get INTA's obstacle warning response
            warning_response = self.ai_companion.handle_obstacle_warning(
                distance_cm=reading.distance_cm,
                urgency=analysis['urgency'],
                obstacle_level=analysis['level']
            )
            
            if warning_response:
                self.logger.warning(f"🚨 Obstacle: {reading.distance_cm}cm ({analysis['level']})")
                
                # Broadcast warning to all active voice channels
                for guild_id in self.voice_clients:
                    asyncio.create_task(
                        self.speak_in_channel(guild_id, warning_response)
                    )
                    
                    # Also send text message to channels
                    if guild_id in self.active_channels:
                        channel = self.active_channels[guild_id]['text_channel']
                        asyncio.create_task(
                            channel.send(f"🚨 **Obstacle Alert:** {warning_response}")
                        )
        
        except Exception as e:
            self.logger.error(f"Error handling obstacle detection: {e}")
    
    def handle_distance_update(self, reading, analysis):
        """Handle distance updates from ultrasonic sensor"""
        try:
            # Update INTA's environmental context
            self.ai_companion.handle_distance_update(
                distance_cm=reading.distance_cm,
                status=analysis['level']
            )
        except Exception as e:
            self.logger.error(f"Error handling distance update: {e}")
    
    async def close(self):
        """Clean up when bot shuts down"""
        self.logger.info("🛑 Shutting down INTA Discord Bot...")
        
        # Stop components
        if hasattr(self, 'ultrasonic_sensor'):
            self.ultrasonic_sensor.cleanup()
        
        if hasattr(self, 'ai_companion'):
            self.ai_companion.stop_companion()
            self.ai_companion.cleanup()
        
        if hasattr(self, 'speech_manager'):
            self.speech_manager.cleanup()
        
        # Disconnect from all voice channels
        for voice_client in self.voice_clients.values():
            try:
                await voice_client.disconnect()
            except:
                pass
        
        await super().close()
        self.logger.info("✅ INTA Discord Bot shutdown complete")


class INTAAudioSink(voice_recv.AudioSink):
    """Audio sink for processing voice data from Discord"""
    
    def __init__(self, bot: INTADiscordBot, guild_id: int):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id
        self.logger = logging.getLogger(f"{__name__}.AudioSink")
        
        # Audio processing state
        self.user_audio_buffers = {}  # user_id -> audio buffer
        self.user_silence_timers = {}  # user_id -> last audio time
        self.silence_threshold = 1.0  # Seconds of silence before processing
        
        # Start silence detection thread
        self.silence_thread = threading.Thread(target=self._monitor_silence, daemon=True)
        self.silence_thread.start()
        
        self.logger.info(f"🎤 Audio sink created for guild {guild_id}")
    
    def wants_opus(self) -> bool:
        """We want PCM data for processing"""
        return False
    
    def write(self, user, data: voice_recv.VoiceData):
        """Process incoming voice data"""
        if not user or not data.pcm:
            return
        
        user_id = user.id
        current_time = time.time()
        
        # Initialize buffer for new users
        if user_id not in self.user_audio_buffers:
            self.user_audio_buffers[user_id] = {
                'audio_data': [],
                'user': user,
                'start_time': current_time
            }
        
        # Add audio data to buffer
        self.user_audio_buffers[user_id]['audio_data'].append(data.pcm)
        self.user_silence_timers[user_id] = current_time
    
    def _monitor_silence(self):
        """Monitor for silence to trigger audio processing"""
        while True:
            try:
                current_time = time.time()
                users_to_process = []
                
                # Check for users who have stopped speaking
                for user_id, last_audio_time in list(self.user_silence_timers.items()):
                    if (current_time - last_audio_time) > self.silence_threshold:
                        if user_id in self.user_audio_buffers:
                            users_to_process.append(user_id)
                
                # Process audio for users who stopped speaking
                for user_id in users_to_process:
                    asyncio.create_task(self._process_user_audio(user_id))
                    
                    # Clean up
                    del self.user_silence_timers[user_id]
                    del self.user_audio_buffers[user_id]
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                self.logger.error(f"Error in silence monitoring: {e}")
                time.sleep(1)
    
    async def _process_user_audio(self, user_id: int):
        """Process audio data for a user using Whisper"""
        if not self.bot.whisper_model:
            return
        
        try:
            buffer_data = self.user_audio_buffers.get(user_id)
            if not buffer_data or not buffer_data['audio_data']:
                return
            
            user = buffer_data['user']
            audio_data = buffer_data['audio_data']
            
            self.logger.info(f"🎤 Processing audio from {user.display_name}")
            
            # Combine audio data
            combined_audio = b''.join(audio_data)
            
            # Convert to temporary WAV file for Whisper
            temp_wav = await asyncio.get_event_loop().run_in_executor(
                None, self._create_wav_file, combined_audio
            )
            
            if not temp_wav:
                return
            
            # Transcribe with Whisper
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.bot.whisper_model.transcribe, temp_wav
            )
            
            # Clean up temp file
            try:
                os.unlink(temp_wav)
            except:
                pass
            
            if result and result.get('text', '').strip():
                transcribed_text = result['text'].strip()
                self.logger.info(f"💬 {user.display_name}: {transcribed_text}")
                
                # Process with INTA
                await self._handle_voice_command(user, transcribed_text)
        
        except Exception as e:
            self.logger.error(f"Error processing audio for user {user_id}: {e}")
    
    def _create_wav_file(self, pcm_data: bytes) -> Optional[str]:
        """Create a temporary WAV file from PCM data"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            
            # Write WAV file
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(2)  # Stereo
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(48000)  # 48kHz (Discord's rate)
                wav_file.writeframes(pcm_data)
            
            return temp_file.name
            
        except Exception as e:
            self.logger.error(f"Error creating WAV file: {e}")
            return None
    
    async def _handle_voice_command(self, user, text: str):
        """Handle voice command from user"""
        try:
            # Check for system commands
            text_lower = text.lower().strip()
            
            if any(cmd in text_lower for cmd in ['take picture', 'capture image', 'take photo', 'analyze image']):
                # Image capture command
                response = "I'll capture and analyze an image for you right now."
                await self.bot.speak_in_channel(self.guild_id, response)
                
                # Trigger image capture
                try:
                    image_path = self.bot.camera_manager.capture_image()
                    if image_path:
                        vision_result = await asyncio.get_event_loop().run_in_executor(
                            None, self.bot.vision_analyzer.analyze_image, image_path
                        )
                        
                        if vision_result:
                            enhanced_description = self.bot.ai_companion.process_vision_analysis(
                                vision_result, f"Image requested by {user.display_name} via voice"
                            )
                            await self.bot.speak_in_channel(self.guild_id, enhanced_description)
                            
                            # Send to text channel too
                            if self.guild_id in self.bot.active_channels:
                                channel = self.bot.active_channels[self.guild_id]['text_channel']
                                await channel.send(f"📸 **Vision Analysis for {user.display_name}:**\n{enhanced_description}")
                
                except Exception as e:
                    error_response = "I'm sorry, I had trouble capturing or analyzing the image."
                    await self.bot.speak_in_channel(self.guild_id, error_response)
                    self.logger.error(f"Error in voice-triggered image capture: {e}")
                
                return
            
            # Regular conversation with INTA
            response = self.bot.ai_companion.handle_conversation(
                f"Discord user {user.display_name} says: {text}"
            )
            
            # Speak the response
            await self.bot.speak_in_channel(self.guild_id, response)
            
            # Also log to text channel
            if self.guild_id in self.bot.active_channels:
                channel = self.bot.active_channels[self.guild_id]['text_channel']
                await channel.send(f"💬 **{user.display_name}:** {text}\n🤖 **INTA:** {response}")
        
        except Exception as e:
            self.logger.error(f"Error handling voice command: {e}")
    
    def cleanup(self):
        """Clean up audio sink"""
        self.logger.info(f"🧹 Cleaning up audio sink for guild {self.guild_id}")


async def main():
    """Main function to run the Discord bot"""
    # Load Discord token
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    discord_config = config.get('discord', {})
    discord_token = discord_config.get('token')
    
    if not discord_token:
        print("❌ Discord token not found in config!")
        print("📝 Please add Discord configuration to your config.json:")
        print("""
{
  "discord": {
    "token": "your-discord-bot-token-here"
  }
}
        """)
        return
    
    # Create and run bot
    bot = INTADiscordBot()
    
    try:
        print("🚀 Starting INTA Discord Bot...")
        await bot.start(discord_token)
    except KeyboardInterrupt:
        print("\n🛑 Bot interrupted by user")
    except Exception as e:
        print(f"❌ Error running bot: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main()) 