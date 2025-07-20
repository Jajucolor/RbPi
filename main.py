#!/usr/bin/env python3
"""
Visually Impaired Assistance Glasses
Main application for Raspberry Pi based assistive glasses
"""

import time
import sys
import threading
import signal
from datetime import datetime
import logging
from pathlib import Path

# Import custom modules
from modules.camera_manager import CameraManager
from modules.vision_analyzer import VisionAnalyzer
from modules.speech_manager import SpeechManager
from modules.config_manager import ConfigManager
from modules.button_manager import ButtonManager
from modules.voice_command_manager import VoiceCommandManager
from modules.ai_companion import AICompanion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('glasses_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class AssistiveGlasses:
    """Main class for the assistive glasses system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.capture_thread = None
        self.last_capture_time = 0
        self.min_capture_interval = 3  # Minimum seconds between captures
        
        # Initialize all components
        self.config = ConfigManager()
        self.camera = CameraManager()
        self.vision_analyzer = VisionAnalyzer(self.config.get_openai_key())
        
        # Initialize speech manager with config settings
        speech_config = self.config.get_speech_config()
        self.speech = SpeechManager(
            volume=speech_config.get('volume', 0.9),
            language='en',
            slow=False
        )
        
        self.button_manager = ButtonManager()
        
        # Initialize voice command manager with config settings
        voice_config = self.config.get('voice_commands', {})
        self.voice_command_manager = VoiceCommandManager(
            model_size=voice_config.get('model_size', 'base'),
            language=voice_config.get('language', 'en'),
            chunk_duration=voice_config.get('chunk_duration', 2.0),
            silence_threshold=voice_config.get('silence_threshold', 0.01)
        )
        
        # Initialize AI companion
        companion_config = self.config.get('companion', {})
        self.ai_companion = AICompanion(
            api_key=self.config.get_openai_key(),
            model=companion_config.get('model', 'gpt-4o-mini'),
            personality=companion_config.get('personality', 'jarvis'),
            voice_enabled=companion_config.get('voice_enabled', True)
        )
        
        # Set up button callbacks
        self.button_manager.set_capture_callback(self.manual_capture)
        self.button_manager.set_shutdown_callback(self.shutdown)
        
        # Set up voice command callbacks
        self.voice_command_manager.set_capture_callback(self.voice_capture)
        self.voice_command_manager.set_shutdown_callback(self.shutdown)
        
        # Connect AI companion to voice command manager and speech system
        self.ai_companion.set_speech_manager(self.speech)
        self.voice_command_manager.set_companion(self.ai_companion)
        
        self.logger.info("Assistive glasses system initialized")
    
    def start(self):
        """Start the main system loop"""
        self.logger.info("Starting assistive glasses system...")
        self.running = True
        
        # Start AI companion (includes welcome message)
        self.ai_companion.start_companion()
        
        # Start button monitoring (as backup)
        self.button_manager.start_monitoring()
        
        # Start voice command listening
        self.voice_command_manager.start_listening()
        
        # Start main loop
        self.main_loop()
    
    def main_loop(self):
        """Main system loop"""
        try:
            while self.running:
                # Check for automatic capture based on motion or other triggers
                # For now, we'll rely on manual button presses
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
            self.shutdown()
    
    def manual_capture(self):
        """Handle manual capture triggered by button press"""
        current_time = time.time()
        
        # Rate limiting to prevent too frequent captures
        if current_time - self.last_capture_time < self.min_capture_interval:
            remaining_time = self.min_capture_interval - (current_time - self.last_capture_time)
            self.speech.speak(f"Please wait {remaining_time:.1f} more seconds before next capture")
            return
        
        self.last_capture_time = current_time
        
        # Run capture in a separate thread to avoid blocking
        if self.capture_thread is None or not self.capture_thread.is_alive():
            self.capture_thread = threading.Thread(target=self.capture_and_analyze)
            self.capture_thread.daemon = True
            self.capture_thread.start()
        else:
            self.speech.speak("Analysis in progress, please wait")
    
    def voice_capture(self):
        """Handle voice-activated capture"""
        self.logger.info("Voice capture command received")
        # Provide audio feedback that the command was heard
        self.speech.speak("Voice command received. Capturing image now.")
        # Use the same capture logic as manual capture
        self.manual_capture()
    
    def capture_and_analyze(self):
        """Capture image and analyze with OpenAI Vision"""
        try:
            self.logger.info("Starting image capture and analysis")
            self.speech.speak("Capturing image...")
            
            # Capture image
            image_path = self.camera.capture_image()
            if not image_path:
                self.speech.speak("Failed to capture image, please try again")
                return
            
            self.speech.speak("Analyzing surroundings...")
            
            # Analyze with OpenAI Vision
            description = self.vision_analyzer.analyze_image(image_path)
            
            if description:
                self.logger.info(f"Analysis complete: {description}")
                
                # Process with AI companion for enhanced response
                enhanced_response = self.ai_companion.process_vision_analysis(description)
                self.speech.speak(enhanced_response)
                
                # Save analysis to log file
                self.save_analysis_log(f"Raw: {description}\nEnhanced: {enhanced_response}")
            else:
                self.speech.speak("Sorry, I couldn't analyze the image. Please try again.")
                
        except Exception as e:
            self.logger.error(f"Error during capture and analysis: {str(e)}")
            self.speech.speak("An error occurred during analysis. Please try again.")
    
    def save_analysis_log(self, description):
        """Save analysis results to a log file"""
        try:
            log_file = Path("analysis_log.txt")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {description}\n")
                
        except Exception as e:
            self.logger.error(f"Error saving analysis log: {str(e)}")
    
    def shutdown(self):
        """Graceful shutdown of the system"""
        self.logger.info("Shutting down assistive glasses system...")
        self.running = False
        
        # Stop AI companion (includes farewell message)
        if self.ai_companion:
            self.ai_companion.stop_companion()
        
        # Clean up resources
        if self.camera:
            self.camera.cleanup()
        
        if self.button_manager:
            self.button_manager.stop_monitoring()
        
        if self.voice_command_manager:
            self.voice_command_manager.stop_listening()
        
        if self.ai_companion:
            self.ai_companion.cleanup()
        
        # Wait for any running threads to complete
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
        
        self.logger.info("System shutdown complete")
        sys.exit(0)

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    print("\nReceived signal to shutdown...")
    if 'glasses_system' in globals():
        glasses_system.shutdown()
    else:
        sys.exit(0)

def main():
    """Main entry point"""
    global glasses_system
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        glasses_system = AssistiveGlasses()
        glasses_system.start()
        
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 