import time
import sys

try:
    import modules.sensor_manager as sensor_manager
except ImportError:
    import sensor_manager

if __name__ == "__main__":
    print("--- SensorManager Test ---")
    port = input("Enter your Arduino COM port (e.g., COM3): ").strip()
    if not port:
        print("No port specified. Exiting.")
        sys.exit(0)
    # Recreate the monitor with the specified port
    sensor_monitor = sensor_manager.SensorMonitor(port=port, baudrate=9600, poll_interval=0.1)
    sensor_monitor.start()
    print(f"Reading distance from {port} (Ctrl+C to stop)...")
    try:
        while True:
            dist = sensor_monitor.get_latest_distance()
            if dist is not None:
                print(f"Distance: {dist} cm")
            else:
                print("No data or waiting for data...")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    finally:
        sensor_monitor.stop()
        print("Sensor monitor stopped.") 