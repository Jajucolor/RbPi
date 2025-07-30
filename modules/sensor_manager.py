#!/usr/bin/env python3
"""
Navigation Sensor Manager
Manages ultrasonic and infrared sensors for navigation assistance
Starts distance detection when navigation is activated and stops when user says to stop
"""

import serial
import threading
import time
import logging
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SensorStatus(Enum):
    """Sensor status enumeration"""
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
    CONNECTING = "connecting"

@dataclass
class SensorData:
    """Sensor data structure"""
    distance: Optional[float]  # Distance in centimeters
    timestamp: float           # Timestamp when data was collected
    sensor_type: str           # "ultrasonic" or "infrared"
    status: SensorStatus       # Current sensor status
    error_message: Optional[str] = None

class NavigationSensorManager:
    """
    Navigation Sensor Manager for continuous distance monitoring
    Designed to work with the navigation monitoring system
    """
    
    def __init__(self, 
                 port: str = '/dev/ttyACM0', 
                 baudrate: int = 9600,
                 timeout: float = 1.0,
                 poll_interval: float = 0.1):
        """
        Initialize the navigation sensor manager
        
        Args:
            port: Serial port for Arduino communication
            baudrate: Serial communication baudrate
            timeout: Serial timeout in seconds
            poll_interval: How often to poll sensors (seconds)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.poll_interval = poll_interval
        
        # Serial connection
        self.serial_connection: Optional[serial.Serial] = None
        
        # Threading
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Status and data
        self.status = SensorStatus.STOPPED
        self.latest_data: Optional[SensorData] = None
        self.error_count = 0
        self.max_errors = 5
        
        # Callbacks
        self.distance_callback: Optional[Callable[[float], None]] = None
        self.warning_callback: Optional[Callable[[str], None]] = None
        self.status_callback: Optional[Callable[[SensorStatus], None]] = None
        
        # Navigation monitoring state
        self.navigation_active = False
        self.last_warning_time = 0
        self.warning_interval = 0  # No interval - warn every time
        
        # Voice overlap prevention
        self.is_speaking = False
        self.speech_lock = threading.Lock()
        self.pending_warnings = []
        
        # Sensor data tracking
        self.last_valid_distance = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10
        
        logger.info(f"Navigation Sensor Manager initialized for port {port}")
    
    def set_callbacks(self, 
                     distance_callback: Optional[Callable[[float], None]] = None,
                     warning_callback: Optional[Callable[[str], None]] = None,
                     status_callback: Optional[Callable[[SensorStatus], None]] = None):
        """Set callback functions for sensor events"""
        self.distance_callback = distance_callback
        self.warning_callback = warning_callback
        self.status_callback = status_callback
        logger.info("Callbacks set for navigation sensor manager")
    
    def _safe_warning_callback(self, message: str):
        """Safely call warning callback with voice overlap prevention"""
        with self.speech_lock:
            if self.is_speaking:
                # Add to pending warnings if already speaking
                self.pending_warnings.append(message)
                logger.debug(f"Warning queued (speaking): {message}")
            else:
                # Mark as speaking and call callback
                self.is_speaking = True
                if self.warning_callback:
                    self.warning_callback(message)
                logger.debug(f"Warning sent: {message}")
    
    def mark_speech_complete(self):
        """Mark that speech has completed and process pending warnings"""
        with self.speech_lock:
            self.is_speaking = False
            
            # Process any pending warnings
            if self.pending_warnings:
                next_warning = self.pending_warnings.pop(0)
                self.is_speaking = True
                if self.warning_callback:
                    self.warning_callback(next_warning)
                logger.debug(f"Pending warning sent: {next_warning}")
    
    def connect(self) -> bool:
        """Connect to the Arduino sensor system for continuous streaming"""
        try:
            logger.info(f"Attempting to connect to {self.port} at {self.baudrate} baud")
            self.status = SensorStatus.CONNECTING
            
            # Use shorter timeout for continuous streaming
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.5  # Shorter timeout for responsive reading
            )
            
            # Test connection
            if self.serial_connection.is_open:
                logger.info("Successfully connected to sensor system")
                logger.info("Arduino should be sending data continuously")
                self.status = SensorStatus.STOPPED
                self.error_count = 0
                return True
            else:
                logger.error("Failed to open serial connection")
                self.status = SensorStatus.ERROR
                return False
                
        except serial.SerialException as e:
            logger.error(f"Serial connection error: {e}")
            self.status = SensorStatus.ERROR
            return False
        except Exception as e:
            logger.error(f"Unexpected connection error: {e}")
            self.status = SensorStatus.ERROR
            return False
    
    def disconnect(self):
        """Disconnect from the Arduino sensor system"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                logger.info("Disconnected from sensor system")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
        finally:
            self.serial_connection = None
            self.status = SensorStatus.STOPPED
    
    def start_navigation_monitoring(self) -> bool:
        """Start continuous navigation monitoring"""
        if self.navigation_active:
            logger.warning("Navigation monitoring is already active")
            return True
        
        if not self.serial_connection or not self.serial_connection.is_open:
            if not self.connect():
                logger.error("Cannot start monitoring - no sensor connection")
                return False
        
        try:
            # Reset stop event
            self.stop_event.clear()
            
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="NavigationSensorMonitor"
            )
            self.monitoring_thread.start()
            
            self.navigation_active = True
            self.status = SensorStatus.RUNNING
            self.last_warning_time = 0
            
            logger.info("Navigation monitoring started")
            
            if self.status_callback:
                self.status_callback(self.status)
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting navigation monitoring: {e}")
            self.status = SensorStatus.ERROR
            return False
    
    def stop_navigation_monitoring(self) -> bool:
        """Stop continuous navigation monitoring"""
        if not self.navigation_active:
            logger.info("Navigation monitoring is not active")
            return True
        
        try:
            # Signal thread to stop
            self.stop_event.set()
            
            # Wait for thread to finish
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            self.navigation_active = False
            self.status = SensorStatus.STOPPED
            self.monitoring_thread = None
            
            logger.info("Navigation monitoring stopped")
            
            if self.status_callback:
                self.status_callback(self.status)
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping navigation monitoring: {e}")
            return False
    
    def _monitoring_loop(self):
        """Main monitoring loop for navigation assistance"""
        logger.info("Navigation monitoring loop started")
        
        try:
            while not self.stop_event.is_set():
                try:
                    # Read sensor data from continuous stream
                    distance = self._read_distance()
                    
                    if distance is not None:
                        # Reset consecutive errors on successful read
                        self.consecutive_errors = 0
                        self.last_valid_distance = distance
                        
                        # Create sensor data object
                        sensor_data = SensorData(
                            distance=distance,
                            timestamp=time.time(),
                            sensor_type="ultrasonic",
                            status=self.status
                        )
                        self.latest_data = sensor_data
                        
                        # Call distance callback
                        if self.distance_callback:
                            self.distance_callback(distance)
                        
                        # Check for warnings if navigation is active
                        if self.navigation_active:
                            self._check_navigation_warnings(distance)
                    else:
                        # No data available (normal for streaming)
                        # Only increment errors if we haven't had data for a while
                        if self.consecutive_errors < 50:  # Allow more consecutive "no data" readings
                            self.consecutive_errors += 1
                        
                        # If we have a last valid distance and navigation is active, 
                        # we can still provide warnings based on the last reading
                        if self.last_valid_distance is not None and self.navigation_active:
                            # Only warn occasionally when using last valid distance
                            if self.consecutive_errors % 10 == 0:  # Every 10th "no data" reading
                                logger.debug(f"Using last valid distance: {self.last_valid_distance}")
                                self._check_navigation_warnings(self.last_valid_distance)
                    
                    # Shorter wait for continuous streaming
                    self.stop_event.wait(0.1)  # Check every 100ms for new data
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    self.error_count += 1
                    self.consecutive_errors += 1
                    
                    if self.error_count >= self.max_errors:
                        logger.error("Too many errors, stopping monitoring")
                        break
                    
                    time.sleep(1)  # Wait before retrying
            
            logger.info("Navigation monitoring loop ended")
            
        except Exception as e:
            logger.error(f"Fatal error in monitoring loop: {e}")
            self.status = SensorStatus.ERROR
        finally:
            self.navigation_active = False
    
    def _read_distance(self) -> Optional[float]:
        """Read distance from sensor - continuous streaming mode"""
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                return None
            
            # Check if data is available to read
            if self.serial_connection.in_waiting > 0:
                # Read available data from continuous stream
                response = self.serial_connection.readline().decode('utf-8').strip()
                
                if response:
                    # Try to extract numeric value from response
                    # Handle different response formats:
                    # 1. Pure number: "10.30"
                    # 2. Text with number: "Infrared sensor is out of range,Using ultrasonic sensor value"
                    
                    # First, try to find any decimal number in the response
                    import re
                    number_match = re.search(r'\d+\.?\d*', response)
                    
                    if number_match:
                        try:
                            distance = float(number_match.group())
                            self.error_count = 0  # Reset error count on successful read
                            logger.debug(f"Extracted distance: {distance} from response: {response}")
                            return distance
                        except ValueError:
                            logger.warning(f"Could not convert '{number_match.group()}' to float from response: {response}")
                            return None
                    else:
                        logger.debug(f"No numeric value found in response: {response}")
                        return None
                else:
                    # Empty response, return None (normal for streaming)
                    return None
            else:
                # No data available, return None (normal for streaming)
                return None
                
        except serial.SerialException as e:
            logger.error(f"Serial communication error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading distance: {e}")
            return None

    def _check_navigation_warnings(self, distance: float):
        """Check for navigation warnings based on distance - warns every time"""
        # Very close obstacle - URGENT warning (below 50cm)
        if distance < 50:
            warning_msg = f"URGENT: Obstacle very close at {distance:.0f} centimeters! Stop immediately!"
            logger.warning(warning_msg)
            self._safe_warning_callback(warning_msg)
        
        # Close obstacle - Caution warning (50-100cm)
        elif distance < 100:
            warning_msg = f"Caution: Object detected at {distance:.0f} centimeters ahead."
            logger.info(warning_msg)
            self._safe_warning_callback(warning_msg)
        
        # Moderate distance - Info message (100-200cm)
        elif distance < 200:
            info_msg = f"Path clear. Object at {distance:.0f} centimeters."
            logger.info(info_msg)
            self._safe_warning_callback(info_msg)
    
    def get_latest_distance(self) -> Optional[float]:
        """Get the latest distance reading"""
        if self.latest_data:
            return self.latest_data.distance
        return None

    def get_sensor_status(self) -> dict:
        """Get current sensor status"""
        return {
            "status": self.status.value,
            "navigation_active": self.navigation_active,
            "connected": self.serial_connection is not None and self.serial_connection.is_open,
            "latest_distance": self.get_latest_distance(),
            "error_count": self.error_count,
            "port": self.port,
            "baudrate": self.baudrate
        }
    
    def is_navigation_active(self) -> bool:
        """Check if navigation monitoring is active"""
        return self.navigation_active
    
    def get_sensor_info(self) -> dict:
        """Get sensor system information"""
        return {
            "name": "Navigation Sensor Manager",
            "type": "Ultrasonic + Infrared",
            "port": self.port,
            "baudrate": self.baudrate,
            "poll_interval": self.poll_interval,
            "status": self.status.value,
            "navigation_active": self.navigation_active
        }
    
    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up navigation sensor manager")
        self.stop_navigation_monitoring()
        self.disconnect()


# Legacy compatibility class (for existing code)
class SensorMonitor:
    """
    Legacy SensorMonitor class for backward compatibility
    Wraps the new NavigationSensorManager
    """
    
    def __init__(self, port='/dev/ttyACM0', baudrate=9600, poll_interval=0.1):
        self.sensor_manager = NavigationSensorManager(
            port=port,
            baudrate=baudrate,
            poll_interval=poll_interval
        )

    def start(self):
        """Start sensor monitoring (legacy method)"""
        return self.sensor_manager.start_navigation_monitoring()

    def stop(self):
        """Stop sensor monitoring (legacy method)"""
        return self.sensor_manager.stop_navigation_monitoring()

    def get_latest_distance(self):
        """Get latest distance (legacy method)"""
        return self.sensor_manager.get_latest_distance()
    
    def get_status(self):
        """Get sensor status (legacy method)"""
        return self.sensor_manager.get_sensor_status()


# Example usage and testing
if __name__ == "__main__":
    def distance_callback(distance):
        print(f"Distance: {distance:.1f} cm")
    
    def warning_callback(message):
        print(f"WARNING: {message}")
    
    def status_callback(status):
        print(f"Status: {status.value}")
    
    # Create sensor manager
    sensor_manager = NavigationSensorManager()
    
    # Set callbacks
    sensor_manager.set_callbacks(
        distance_callback=distance_callback,
        warning_callback=warning_callback,
        status_callback=status_callback
    )
    
    print("Navigation Sensor Manager Test")
    print("="*40)
    
    # Test connection
    if sensor_manager.connect():
        print("✓ Connected to sensor system")
        
        # Test navigation monitoring
        print("\nStarting navigation monitoring...")
        if sensor_manager.start_navigation_monitoring():
            print("✓ Navigation monitoring started")
            
            # Let it run for a few seconds
            time.sleep(10)
            
            print("\nStopping navigation monitoring...")
            sensor_manager.stop_navigation_monitoring()
            print("✓ Navigation monitoring stopped")
        else:
            print("✗ Failed to start navigation monitoring")
    else:
        print("✗ Failed to connect to sensor system")
    
    # Cleanup
    sensor_manager.cleanup()
    print("\nTest completed.")