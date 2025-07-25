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
from modules.realtime_speech_manager import RealtimeSpeechManager
from modules.config_manager import ConfigManager
from modules.button_manager import ButtonManager
from modules.inta_ai_manager import IntaAIManager

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
        
        # Initialize real-time speech manager with config settings
        speech_config = self.config.get_speech_config()
        self.speech = RealtimeSpeechManager(
            volume=speech_config.get('volume', 0.9),
            language='en',
            slow=False
        )
        
        # Configure real-time speech settings
        self.speech.set_realtime_settings(
            word_delay=0.05,  # Very fast word-by-word
            sentence_delay=0.2,  # Short pause between sentences
            chunk_size=2  # Speak 2 words at a time for natural flow
        )
        
        self.button_manager = ButtonManager()
        
        # Initialize INTA AI assistant
        self.inta_ai = IntaAIManager(self.config.config)
        
        # Set up button callbacks
        self.button_manager.set_capture_callback(self.manual_capture)
        self.button_manager.set_shutdown_callback(self.shutdown)
        
        # Set up INTA AI response callback
        self.inta_ai._emit_response = self.handle_inta_response
        
        # Connect INTA AI to real-time speech
        self.inta_ai.set_speech_callback(self.speech.speak_realtime)
        
        self.logger.info("Assistive glasses system initialized")
    
    def start(self):
        """Start the main system loop"""
        self.logger.info("Starting assistive glasses system...")
        self.running = True
        
        # Welcome message
        self.speech.speak("Assistive glasses system starting. INTA AI assistant is ready. Press the button to capture and analyze your surroundings.")
        
        # Start button monitoring
        self.button_manager.start_monitoring()
        
        # Start INTA AI listening
        if self.inta_ai.start_listening():
            self.speech.speak("INTA AI is now listening for voice commands.")
        else:
            self.speech.speak("INTA AI voice recognition is not available. Using button controls only.")
        
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
                self.speech.speak(f"I can see: {description}")
                
                # Save analysis to log file
                self.save_analysis_log(description)
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
    
    def handle_inta_response(self, response: str):
        """Handle responses from INTA AI assistant"""
        try:
            self.logger.info(f"INTA AI Response: {response}")
            
            # Speak the response
            self.speech.speak(response)
            
            # Check if response contains commands for the system
            if "capture" in response.lower() or "take picture" in response.lower():
                self.manual_capture()
            elif "describe" in response.lower() or "analyze" in response.lower():
                self.manual_capture()
            elif "shutdown" in response.lower() or "turn off" in response.lower():
                self.shutdown()
                
        except Exception as e:
            self.logger.error(f"Error handling INTA response: {str(e)}")
    
    def shutdown(self):
        """Graceful shutdown of the system"""
        self.logger.info("Shutting down assistive glasses system...")
        self.running = False
        
        self.speech.speak("Shutting down assistive glasses system. Goodbye!")
        
        # Clean up resources
        if self.camera:
            self.camera.cleanup()
        
        if self.button_manager:
            self.button_manager.stop_monitoring()
        
        if self.inta_ai:
            self.inta_ai.cleanup()
        
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