"""
Ultrasonic Sensor Module
Handles distance detection, obstacle warnings, and CSV data logging
Compatible with HC-SR04 ultrasonic sensors on Raspberry Pi
"""

import time
import csv
import threading
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List, Dict
from dataclasses import dataclass

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logging.warning("RPi.GPIO not available - using ultrasonic sensor simulation mode")

@dataclass
class DistanceReading:
    """Data class for distance readings"""
    timestamp: str
    distance_cm: float
    is_obstacle: bool
    obstacle_level: str  # "close", "medium", "far", "clear"

class UltrasonicSensor:
    """Manages ultrasonic sensor for obstacle detection and distance measurement"""
    
    def __init__(self, trigger_pin: int = 23, echo_pin: int = 24, 
                 obstacle_threshold_cm: float = 100.0, csv_file: str = "distance_log.csv"):
        self.logger = logging.getLogger(__name__)
        
        # GPIO pins for HC-SR04 sensor
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        
        # Distance thresholds (in centimeters)
        self.obstacle_threshold_cm = obstacle_threshold_cm
        self.close_threshold_cm = 30.0      # Very close obstacle
        self.medium_threshold_cm = 60.0     # Medium distance obstacle
        self.far_threshold_cm = 100.0       # Far obstacle
        
        # CSV logging
        self.csv_file = Path(csv_file)
        self.readings_buffer = []
        
        # Sensor state
        self.monitoring = False
        self.monitor_thread = None
        self.last_distance = None
        self.last_reading_time = None
        
        # Callbacks
        self.obstacle_callback = None
        self.distance_callback = None
        
        # Simulation mode
        self.simulation_mode = not GPIO_AVAILABLE
        self.simulation_distance = 150.0  # Default simulated distance
        
        # Initialize hardware
        self.initialize_sensor()
        
        # Initialize CSV file
        self.initialize_csv()
    
    def initialize_sensor(self):
        """Initialize the ultrasonic sensor hardware"""
        if not GPIO_AVAILABLE:
            self.logger.warning("Running in ultrasonic sensor simulation mode")
            return
        
        try:
            # Set GPIO mode
            GPIO.setmode(GPIO.BCM)
            
            # Set up pins
            GPIO.setup(self.trigger_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)
            
            # Ensure trigger is low
            GPIO.output(self.trigger_pin, False)
            time.sleep(0.1)
            
            self.logger.info(f"Ultrasonic sensor initialized - Trigger: {self.trigger_pin}, Echo: {self.echo_pin}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ultrasonic sensor: {str(e)}")
            self.simulation_mode = True
    
    def initialize_csv(self):
        """Initialize CSV file for distance logging"""
        try:
            # Create CSV file with headers if it doesn't exist
            if not self.csv_file.exists():
                with open(self.csv_file, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        'timestamp', 'distance_cm', 'is_obstacle', 
                        'obstacle_level', 'trigger_pin', 'echo_pin'
                    ])
                self.logger.info(f"Created CSV log file: {self.csv_file}")
            else:
                self.logger.info(f"Using existing CSV log file: {self.csv_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize CSV file: {str(e)}")
    
    def measure_distance(self) -> Optional[float]:
        """Measure distance using ultrasonic sensor"""
        if self.simulation_mode:
            return self._simulate_distance()
        
        try:
            # Send trigger pulse
            GPIO.output(self.trigger_pin, True)
            time.sleep(0.00001)  # 10 microseconds
            GPIO.output(self.trigger_pin, False)
            
            # Wait for echo start
            pulse_start = time.time()
            timeout_start = pulse_start
            while GPIO.input(self.echo_pin) == 0:
                pulse_start = time.time()
                if pulse_start - timeout_start > 0.5:  # 500ms timeout
                    self.logger.warning("Ultrasonic sensor timeout - no echo start")
                    return None
            
            # Wait for echo end
            pulse_end = time.time()
            timeout_end = pulse_end
            while GPIO.input(self.echo_pin) == 1:
                pulse_end = time.time()
                if pulse_end - timeout_end > 0.5:  # 500ms timeout
                    self.logger.warning("Ultrasonic sensor timeout - no echo end")
                    return None
            
            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            distance_cm = (pulse_duration * 34300) / 2  # Speed of sound = 343 m/s
            
            # Validate reading (HC-SR04 range: 2cm to 400cm)
            if 2.0 <= distance_cm <= 400.0:
                return round(distance_cm, 2)
            else:
                self.logger.warning(f"Invalid distance reading: {distance_cm}cm")
                return None
                
        except Exception as e:
            self.logger.error(f"Error measuring distance: {str(e)}")
            return None
    
    def _simulate_distance(self) -> float:
        """Simulate distance readings for testing without hardware"""
        # Create realistic distance simulation with some obstacles
        current_time = time.time()
        
        # Simulate movement and obstacles
        base_distance = 150 + 50 * math.sin(current_time * 0.1)  # Slow walking simulation
        
        # Add random obstacles occasionally
        if random.random() < 0.05:  # 5% chance of obstacle
            obstacle_distance = random.uniform(20, 80)  # Close obstacle
            self.simulation_distance = obstacle_distance
        else:
            # Gradual return to normal distance
            self.simulation_distance = 0.9 * self.simulation_distance + 0.1 * base_distance
        
        # Add some noise
        noise = random.uniform(-5, 5)
        return round(max(10, self.simulation_distance + noise), 2)
    
    def analyze_distance(self, distance_cm: float) -> Dict[str, any]:
        """Analyze distance reading and determine obstacle status"""
        if distance_cm is None:
            return {
                'is_obstacle': False,
                'level': 'unknown',
                'warning': 'Sensor reading error',
                'urgency': 'low'
            }
        
        # Determine obstacle level and warning
        if distance_cm <= self.close_threshold_cm:
            return {
                'is_obstacle': True,
                'level': 'close',
                'warning': f'URGENT: Very close obstacle at {distance_cm}cm! Stop immediately!',
                'urgency': 'critical'
            }
        elif distance_cm <= self.medium_threshold_cm:
            return {
                'is_obstacle': True,
                'level': 'medium',
                'warning': f'Caution: Obstacle ahead at {distance_cm}cm. Slow down.',
                'urgency': 'high'
            }
        elif distance_cm <= self.far_threshold_cm:
            return {
                'is_obstacle': True,
                'level': 'far',
                'warning': f'Obstacle detected {distance_cm}cm ahead. Be aware.',
                'urgency': 'medium'
            }
        else:
            return {
                'is_obstacle': False,
                'level': 'clear',
                'warning': f'Path clear, {distance_cm}cm ahead.',
                'urgency': 'low'
            }
    
    def log_to_csv(self, reading: DistanceReading):
        """Log distance reading to CSV file"""
        try:
            with open(self.csv_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    reading.timestamp,
                    reading.distance_cm,
                    reading.is_obstacle,
                    reading.obstacle_level,
                    self.trigger_pin,
                    self.echo_pin
                ])
                
        except Exception as e:
            self.logger.error(f"Failed to log to CSV: {str(e)}")
    
    def set_obstacle_callback(self, callback: Callable):
        """Set callback function for obstacle detection"""
        self.obstacle_callback = callback
        self.logger.info("Obstacle detection callback set")
    
    def set_distance_callback(self, callback: Callable):
        """Set callback function for distance updates"""
        self.distance_callback = callback
        self.logger.info("Distance update callback set")
    
    def start_monitoring(self, reading_interval: float = 0.5):
        """Start continuous distance monitoring"""
        if self.monitoring:
            self.logger.warning("Distance monitoring already started")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_distance, 
            args=(reading_interval,), 
            daemon=True
        )
        self.monitor_thread.start()
        
        mode = "simulation" if self.simulation_mode else "hardware"
        self.logger.info(f"Started ultrasonic sensor monitoring in {mode} mode (interval: {reading_interval}s)")
    
    def stop_monitoring(self):
        """Stop distance monitoring"""
        self.monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        self.logger.info("Ultrasonic sensor monitoring stopped")
    
    def _monitor_distance(self, reading_interval: float):
        """Continuous distance monitoring thread"""
        self.logger.info("🔍 Ultrasonic sensor monitoring started")
        
        while self.monitoring:
            try:
                # Measure distance
                distance = self.measure_distance()
                
                if distance is not None:
                    # Analyze reading
                    analysis = self.analyze_distance(distance)
                    
                    # Create reading object
                    reading = DistanceReading(
                        timestamp=datetime.now().isoformat(),
                        distance_cm=distance,
                        is_obstacle=analysis['is_obstacle'],
                        obstacle_level=analysis['level']
                    )
                    
                    # Log to CSV
                    self.log_to_csv(reading)
                    
                    # Update state
                    self.last_distance = distance
                    self.last_reading_time = datetime.now()
                    
                    # Call distance callback
                    if self.distance_callback:
                        self.distance_callback(reading, analysis)
                    
                    # Call obstacle callback for obstacles
                    if analysis['is_obstacle'] and self.obstacle_callback:
                        self.obstacle_callback(reading, analysis)
                    
                    # Log significant readings
                    if analysis['is_obstacle']:
                        self.logger.info(f"🚨 Obstacle: {distance}cm ({analysis['level']})")
                    
                time.sleep(reading_interval)
                
            except Exception as e:
                self.logger.error(f"Error in distance monitoring: {str(e)}")
                time.sleep(1)
        
        self.logger.info("🔍 Ultrasonic sensor monitoring stopped")
    
    def get_sensor_status(self) -> Dict[str, any]:
        """Get current sensor status"""
        return {
            'monitoring': self.monitoring,
            'simulation_mode': self.simulation_mode,
            'trigger_pin': self.trigger_pin,
            'echo_pin': self.echo_pin,
            'obstacle_threshold_cm': self.obstacle_threshold_cm,
            'last_distance_cm': self.last_distance,
            'last_reading_time': self.last_reading_time.isoformat() if self.last_reading_time else None,
            'csv_file': str(self.csv_file),
            'gpio_available': GPIO_AVAILABLE
        }
    
    def get_recent_readings(self, count: int = 10) -> List[Dict[str, any]]:
        """Get recent readings from CSV file"""
        try:
            readings = []
            with open(self.csv_file, 'r') as file:
                reader = csv.DictReader(file)
                all_readings = list(reader)
                recent_readings = all_readings[-count:] if len(all_readings) > count else all_readings
                
                for row in recent_readings:
                    readings.append({
                        'timestamp': row['timestamp'],
                        'distance_cm': float(row['distance_cm']),
                        'is_obstacle': row['is_obstacle'].lower() == 'true',
                        'obstacle_level': row['obstacle_level']
                    })
                    
            return readings
            
        except Exception as e:
            self.logger.error(f"Error reading recent readings: {str(e)}")
            return []
    
    def cleanup(self):
        """Clean up sensor resources"""
        self.logger.info("Cleaning up ultrasonic sensor...")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Clean up GPIO
        if GPIO_AVAILABLE and not self.simulation_mode:
            try:
                GPIO.cleanup([self.trigger_pin, self.echo_pin])
                self.logger.info("GPIO pins cleaned up")
            except Exception as e:
                self.logger.error(f"Error cleaning up GPIO: {str(e)}")
        
        self.logger.info("Ultrasonic sensor cleanup complete")

# Import math for simulation
import math

# Test function
def test_ultrasonic_sensor():
    """Test function for ultrasonic sensor"""
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 Testing Ultrasonic Sensor")
    print("=" * 50)
    
    # Create sensor instance
    sensor = UltrasonicSensor()
    
    def on_obstacle(reading, analysis):
        print(f"🚨 OBSTACLE ALERT: {analysis['warning']}")
    
    def on_distance(reading, analysis):
        if not analysis['is_obstacle']:
            print(f"📏 Distance: {reading.distance_cm}cm - {analysis['level']}")
    
    # Set callbacks
    sensor.set_obstacle_callback(on_obstacle)
    sensor.set_distance_callback(on_distance)
    
    # Start monitoring
    sensor.start_monitoring(reading_interval=1.0)
    
    try:
        print("\n🎯 Monitoring for obstacles... (30 seconds)")
        print("💡 In simulation mode, obstacles will appear randomly")
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        
    finally:
        sensor.cleanup()
        
        # Show recent readings
        print("\n📊 Recent readings:")
        recent = sensor.get_recent_readings(5)
        for reading in recent:
            print(f"  {reading['timestamp']}: {reading['distance_cm']}cm ({reading['obstacle_level']})")

if __name__ == "__main__":
    test_ultrasonic_sensor() 