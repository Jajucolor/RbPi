import serial
import time

def get_distance():
    """
    Connects to the Arduino via serial, reads one line of distance
    data, and returns it as an integer.
    """
    try:
        # Connect to the serial port.
        # On Linux (like Raspberry Pi OS), this is often /dev/ttyACM0 or /dev/ttyUSB0.
        # Make sure the baud rate (9600) matches the Arduino sketch.
        # The timeout is important to prevent the script from hanging.
        ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        ser.flush() # Clears the input buffer to get the most recent data.

        # Read one line of data from the Arduino.
        line = ser.readline().decode('utf-8').strip()
        
        # Check if a line was actually read
        if line:
            # Convert the string data to an integer.
            distance = int(line)
            print(f"Obstacle detected at: {distance} cm")
            return distance
        else:
            print("No data received from Arduino.")
            return None

    except serial.SerialException as e:
        print(f"Error: Could not connect to the Arduino. {e}")
        return None
    except ValueError:
        print(f"Error: Could not convert data to integer. Received: {line}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# --- Example of how to integrate this into your main script ---

# This would be your main loop or function that listens for voice commands.
# For now, we'll simulate a command.
user_command = "I need help walking"

navigation_commands = [
    "i need help walking",
    "is it safe to walk forward",
    "what's the path like",
    "help me navigate"
]

if user_command.lower() in navigation_commands:
    print("Navigation assistance requested. Checking for obstacles...")
    
    # Call the function to get the distance from the Arduino.
    current_distance = get_distance()

    # Use the distance data to provide feedback to the user.
    if current_distance is not None:
        if current_distance < 50:
            # This is where you would trigger your text-to-speech output.
            feedback = f"Warning! Obstacle very close, at {current_distance} centimeters."
        elif current_distance < 150:
            feedback = f"Caution, an object is ahead at about {current_distance} centimeters."
        else:
            feedback = "The path ahead appears to be clear."
        
        print(feedback) # In your project, you'd speak this text.

class SensorMonitor:
    """
    Continuously reads distance data from Arduino in a background thread.
    Use get_latest_distance() to get the most recent value.
    """
    def __init__(self, port='/dev/ttyACM0', baudrate=9600, poll_interval=0.1):
        self.port = port
        self.baudrate = baudrate
        self.poll_interval = poll_interval
        self._distance = None
        self._running = False
        self._thread = None
        self._lock = None
        import threading
        self._lock = threading.Lock()

    def start(self):
        if self._running:
            return
        self._running = True
        import threading
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self):
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=1)
            ser.flush()
            while self._running:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        distance = int(line)
                        with self._lock:
                            self._distance = distance
                    time.sleep(self.poll_interval)
                except Exception:
                    continue
            ser.close()
        except Exception as e:
            print(f"SensorMonitor error: {e}")

    def get_latest_distance(self):
        with self._lock:
            return self._distance

# Singleton instance for use in other modules
sensor_monitor = SensorMonitor()