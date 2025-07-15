"""
Button Manager Module
Handles hardware button interactions for the assistive glasses system
"""

import time
import logging
import threading
from typing import Callable, Optional

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO not available - using simulation mode")

class ButtonManager:
    """Manages hardware button interactions for the assistive glasses"""
    
    def __init__(self, capture_pin: int = 18, shutdown_pin: int = 3, debounce_time: float = 0.2):
        self.logger = logging.getLogger(__name__)
        self.capture_pin = capture_pin
        self.shutdown_pin = shutdown_pin
        self.debounce_time = debounce_time
        
        # Callback functions
        self.capture_callback = None
        self.shutdown_callback = None
        
        # Button state tracking
        self.last_capture_press = 0
        self.last_shutdown_press = 0
        self.monitoring = False
        self.monitor_thread = None
        
        # Initialize GPIO
        self.initialize_gpio()
        
        # For simulation mode
        self.simulation_mode = not GPIO_AVAILABLE
        self.simulation_thread = None
    
    def initialize_gpio(self):
        """Initialize GPIO pins for buttons"""
        if not GPIO_AVAILABLE:
            self.logger.warning("GPIO not available - running in simulation mode")
            return
        
        try:
            # Set GPIO mode
            GPIO.setmode(GPIO.BCM)
            
            # Set up capture button (pull-up resistor, trigger on falling edge)
            GPIO.setup(self.capture_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Set up shutdown button (pull-up resistor, trigger on falling edge)
            GPIO.setup(self.shutdown_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            self.logger.info(f"GPIO initialized - Capture pin: {self.capture_pin}, Shutdown pin: {self.shutdown_pin}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GPIO: {str(e)}")
            self.simulation_mode = True
    
    def set_capture_callback(self, callback: Callable):
        """Set the callback function for capture button press"""
        self.capture_callback = callback
        self.logger.info("Capture callback set")
    
    def set_shutdown_callback(self, callback: Callable):
        """Set the callback function for shutdown button press"""
        self.shutdown_callback = callback
        self.logger.info("Shutdown callback set")
    
    def start_monitoring(self):
        """Start monitoring button presses"""
        if self.monitoring:
            self.logger.warning("Button monitoring already started")
            return
        
        self.monitoring = True
        
        if GPIO_AVAILABLE and not self.simulation_mode:
            # Real hardware monitoring
            self.monitor_thread = threading.Thread(target=self._monitor_buttons_gpio, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Started GPIO button monitoring")
        else:
            # Simulation monitoring
            self.simulation_thread = threading.Thread(target=self._monitor_buttons_simulation, daemon=True)
            self.simulation_thread.start()
            self.logger.info("Started simulation button monitoring")
    
    def stop_monitoring(self):
        """Stop monitoring button presses"""
        self.monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
        
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1)
        
        self.logger.info("Button monitoring stopped")
    
    def _monitor_buttons_gpio(self):
        """Monitor buttons using GPIO (real hardware)"""
        while self.monitoring:
            try:
                # Check capture button
                if GPIO.input(self.capture_pin) == GPIO.LOW:
                    current_time = time.time()
                    if current_time - self.last_capture_press > self.debounce_time:
                        self.last_capture_press = current_time
                        self.logger.info("Capture button pressed")
                        self._handle_capture_press()
                
                # Check shutdown button
                if GPIO.input(self.shutdown_pin) == GPIO.LOW:
                    current_time = time.time()
                    if current_time - self.last_shutdown_press > self.debounce_time:
                        self.last_shutdown_press = current_time
                        self.logger.info("Shutdown button pressed")
                        self._handle_shutdown_press()
                
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                self.logger.error(f"Error in GPIO monitoring: {str(e)}")
                time.sleep(0.1)
    
    def _monitor_buttons_simulation(self):
        """Monitor buttons using simulation (keyboard input)"""
        self.logger.info("Simulation mode: Press 'c' for capture, 'q' for quit, 's' for shutdown")
        
        while self.monitoring:
            try:
                # In a real implementation, this would use keyboard input
                # For now, we'll just simulate button presses periodically
                time.sleep(1)
                
                # You could add keyboard input here if needed for testing
                # For production, this would be replaced with actual GPIO
                
            except Exception as e:
                self.logger.error(f"Error in simulation monitoring: {str(e)}")
                time.sleep(0.1)
    
    def _handle_capture_press(self):
        """Handle capture button press"""
        if self.capture_callback:
            try:
                self.capture_callback()
            except Exception as e:
                self.logger.error(f"Error in capture callback: {str(e)}")
        else:
            self.logger.warning("No capture callback set")
    
    def _handle_shutdown_press(self):
        """Handle shutdown button press"""
        if self.shutdown_callback:
            try:
                self.shutdown_callback()
            except Exception as e:
                self.logger.error(f"Error in shutdown callback: {str(e)}")
        else:
            self.logger.warning("No shutdown callback set")
    
    def simulate_capture_press(self):
        """Simulate a capture button press (for testing)"""
        self.logger.info("Simulating capture button press")
        self._handle_capture_press()
    
    def simulate_shutdown_press(self):
        """Simulate a shutdown button press (for testing)"""
        self.logger.info("Simulating shutdown button press")
        self._handle_shutdown_press()
    
    def get_button_status(self) -> dict:
        """Get current button status"""
        if GPIO_AVAILABLE and not self.simulation_mode:
            try:
                return {
                    "gpio_available": True,
                    "monitoring": self.monitoring,
                    "capture_pin": self.capture_pin,
                    "shutdown_pin": self.shutdown_pin,
                    "capture_state": GPIO.input(self.capture_pin),
                    "shutdown_state": GPIO.input(self.shutdown_pin),
                    "debounce_time": self.debounce_time
                }
            except Exception as e:
                self.logger.error(f"Error getting GPIO status: {str(e)}")
                return {"error": str(e)}
        else:
            return {
                "gpio_available": False,
                "monitoring": self.monitoring,
                "simulation_mode": True,
                "capture_pin": self.capture_pin,
                "shutdown_pin": self.shutdown_pin,
                "debounce_time": self.debounce_time
            }
    
    def cleanup(self):
        """Clean up GPIO resources"""
        self.logger.info("Cleaning up button manager...")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Clean up GPIO
        if GPIO_AVAILABLE and not self.simulation_mode:
            try:
                GPIO.cleanup()
                self.logger.info("GPIO cleanup complete")
            except Exception as e:
                self.logger.error(f"Error during GPIO cleanup: {str(e)}")
        
        self.logger.info("Button manager cleanup complete")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Additional utility functions for testing
def test_buttons():
    """Test function for button manager"""
    logging.basicConfig(level=logging.INFO)
    
    def on_capture():
        print("Capture button pressed!")
    
    def on_shutdown():
        print("Shutdown button pressed!")
    
    button_manager = ButtonManager()
    button_manager.set_capture_callback(on_capture)
    button_manager.set_shutdown_callback(on_shutdown)
    
    button_manager.start_monitoring()
    
    try:
        if button_manager.simulation_mode:
            print("Running in simulation mode. Testing button presses...")
            time.sleep(2)
            button_manager.simulate_capture_press()
            time.sleep(1)
            button_manager.simulate_shutdown_press()
        else:
            print("Running with real GPIO. Press buttons to test...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        button_manager.cleanup()

if __name__ == "__main__":
    test_buttons() 