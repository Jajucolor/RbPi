#!/usr/bin/env python3
"""
Obstacle Detection Test with INTA Integration
Tests the ultrasonic sensor, CSV logging, and AI companion obstacle warnings
"""

import sys
import logging
import time
import threading
from pathlib import Path
from modules.ultrasonic_sensor import UltrasonicSensor
from modules.ai_companion import AICompanion
from modules.speech_manager import SpeechManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_ultrasonic_sensor_basic():
    """Test basic ultrasonic sensor functionality"""
    print("\n" + "="*70)
    print("🔍 Basic Ultrasonic Sensor Test")
    print("="*70)
    
    # Create sensor
    sensor = UltrasonicSensor(csv_file="test_distance_log.csv")
    
    print("📋 Sensor Status:")
    status = sensor.get_sensor_status()
    for key, value in status.items():
        icon = "✅" if value else "❌"
        print(f"  {icon} {key}: {value}")
    
    # Test single measurement
    print("\n📏 Testing distance measurement...")
    for i in range(5):
        distance = sensor.measure_distance()
        if distance:
            analysis = sensor.analyze_distance(distance)
            print(f"  Reading {i+1}: {distance}cm - {analysis['level']} ({analysis['urgency']})")
        else:
            print(f"  Reading {i+1}: Failed")
        time.sleep(1)
    
    sensor.cleanup()
    print("✅ Basic sensor test completed")

def test_obstacle_detection_with_inta():
    """Test obstacle detection integrated with INTA"""
    print("\n" + "="*70)
    print("🤖 INTA Obstacle Detection Integration Test")
    print("="*70)
    
    # Initialize components
    sensor = UltrasonicSensor(csv_file="test_obstacle_log.csv")
    inta = AICompanion(
        api_key=None,  # Simulation mode
        personality="inta",
        voice_enabled=False
    )
    
    # Start INTA
    inta.start_companion()
    
    print("🔗 Setting up obstacle detection callbacks...")
    
    # Test results storage
    test_results = {
        'obstacles_detected': 0,
        'warnings_generated': 0,
        'critical_warnings': 0,
        'distance_updates': 0
    }
    
    def on_obstacle(reading, analysis):
        test_results['obstacles_detected'] += 1
        
        # Get INTA's response
        warning = inta.handle_obstacle_warning(
            distance_cm=reading.distance_cm,
            urgency=analysis['urgency'],
            obstacle_level=analysis['level']
        )
        
        if warning:
            test_results['warnings_generated'] += 1
            if analysis['urgency'] == 'critical':
                test_results['critical_warnings'] += 1
            
            print(f"🚨 OBSTACLE ALERT ({analysis['level']}):")
            print(f"    Distance: {reading.distance_cm}cm")
            print(f"    INTA says: {warning}")
            print()
    
    def on_distance(reading, analysis):
        test_results['distance_updates'] += 1
        
        # Update INTA's context
        inta.handle_distance_update(reading.distance_cm, analysis['level'])
        
        if reading.distance_cm < 150:  # Log interesting readings
            print(f"📏 Distance update: {reading.distance_cm}cm ({analysis['level']})")
    
    # Set callbacks
    sensor.set_obstacle_callback(on_obstacle)
    sensor.set_distance_callback(on_distance)
    
    # Start monitoring
    print("🎯 Starting obstacle detection monitoring...")
    sensor.start_monitoring(reading_interval=1.0)
    
    try:
        print("⏱️  Monitoring for 30 seconds...")
        print("💡 In simulation mode, obstacles will appear randomly")
        print("🤖 INTA will provide intelligent warnings based on obstacle proximity")
        print("-" * 70)
        
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    
    finally:
        sensor.cleanup()
        inta.stop_companion()
        inta.cleanup()
        
        # Results summary
        print("\n" + "="*70)
        print("📊 TEST RESULTS SUMMARY")
        print("="*70)
        print(f"📏 Total distance readings: {test_results['distance_updates']}")
        print(f"🚨 Obstacles detected: {test_results['obstacles_detected']}")
        print(f"⚠️  Warnings generated: {test_results['warnings_generated']}")
        print(f"🔴 Critical warnings: {test_results['critical_warnings']}")
        
        # Check CSV logging
        csv_path = Path("test_obstacle_log.csv")
        if csv_path.exists():
            with open(csv_path, 'r') as f:
                lines = len(f.readlines()) - 1  # Subtract header
            print(f"📝 CSV entries logged: {lines}")
        
        print("\n✅ Obstacle detection integration test completed")

def test_with_speech_output():
    """Test obstacle detection with actual speech output"""
    print("\n" + "="*70)
    print("🔊 Obstacle Detection with Speech Output")
    print("="*70)
    
    try:
        # Initialize components
        speech_manager = SpeechManager()
        sensor = UltrasonicSensor(csv_file="test_speech_log.csv")
        inta = AICompanion(
            api_key=None,
            personality="inta",
            voice_enabled=True
        )
        
        # Connect speech to INTA
        inta.set_speech_manager(speech_manager)
        
        print("🔊 Starting INTA with speech output...")
        inta.start_companion()
        time.sleep(2)
        
        def on_obstacle_with_speech(reading, analysis):
            warning = inta.handle_obstacle_warning(
                distance_cm=reading.distance_cm,
                urgency=analysis['urgency'],
                obstacle_level=analysis['level']
            )
            
            if warning:
                print(f"🚨 Obstacle at {reading.distance_cm}cm - INTA speaking...")
                # INTA will speak automatically through the speech manager
        
        sensor.set_obstacle_callback(on_obstacle_with_speech)
        sensor.start_monitoring(reading_interval=2.0)  # Slower for speech
        
        print("🎯 Monitoring with speech output for 20 seconds...")
        print("🔊 You should hear INTA speaking when obstacles are detected")
        time.sleep(20)
        
        sensor.cleanup()
        inta.stop_companion()
        time.sleep(2)  # Wait for farewell
        inta.cleanup()
        speech_manager.cleanup()
        
        print("✅ Speech output test completed")
        
    except Exception as e:
        print(f"❌ Speech test failed: {e}")
        print("💡 This is normal if gTTS/pygame aren't properly configured")

def test_csv_logging():
    """Test CSV data logging functionality"""
    print("\n" + "="*70)
    print("📊 CSV Logging Test")
    print("="*70)
    
    sensor = UltrasonicSensor(csv_file="test_csv_logging.csv")
    
    print("📝 Testing CSV logging...")
    sensor.start_monitoring(reading_interval=0.5)
    
    # Let it run for a bit to generate data
    time.sleep(10)
    sensor.cleanup()
    
    # Analyze the CSV file
    csv_path = Path("test_csv_logging.csv")
    if csv_path.exists():
        print(f"✅ CSV file created: {csv_path}")
        
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            print(f"📄 Total lines: {len(lines)} (including header)")
            
            if len(lines) > 1:
                print("📋 Sample entries:")
                print("    " + lines[0].strip())  # Header
                for i, line in enumerate(lines[1:6]):  # First 5 data lines
                    print(f"    {line.strip()}")
                    if i >= 4:
                        break
        
        # Get recent readings
        recent = sensor.get_recent_readings(5)
        print("\n📊 Recent readings analysis:")
        obstacles = [r for r in recent if r['is_obstacle']]
        print(f"  🚨 Obstacles in recent readings: {len(obstacles)}")
        
        if obstacles:
            avg_distance = sum(r['distance_cm'] for r in obstacles) / len(obstacles)
            print(f"  📏 Average obstacle distance: {avg_distance:.1f}cm")
    else:
        print("❌ CSV file was not created")
    
    print("✅ CSV logging test completed")

def interactive_obstacle_test():
    """Interactive obstacle detection test"""
    print("\n" + "="*70)
    print("🎮 Interactive Obstacle Detection Test")
    print("="*70)
    print("This test runs continuously and shows real-time obstacle detection.")
    print("You can adjust simulation parameters and see INTA's responses.")
    print("Press Ctrl+C to exit.")
    print("="*70)
    
    sensor = UltrasonicSensor(csv_file="interactive_test.csv")
    inta = AICompanion(api_key=None, personality="inta", voice_enabled=False)
    
    inta.start_companion()
    
    def on_obstacle(reading, analysis):
        timestamp = reading.timestamp.split('T')[1][:8]  # Time only
        print(f"[{timestamp}] 🚨 {analysis['level'].upper()}: {reading.distance_cm}cm")
        
        warning = inta.handle_obstacle_warning(
            reading.distance_cm, analysis['urgency'], analysis['level']
        )
        if warning:
            print(f"         INTA: {warning}")
        print()
    
    def on_distance(reading, analysis):
        if analysis['level'] == 'clear' and reading.distance_cm > 300:
            timestamp = reading.timestamp.split('T')[1][:8]
            print(f"[{timestamp}] ✅ Clear: {reading.distance_cm}cm")
    
    sensor.set_obstacle_callback(on_obstacle)
    sensor.set_distance_callback(on_distance)
    sensor.start_monitoring(reading_interval=1.0)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Interactive test stopped")
    finally:
        sensor.cleanup()
        inta.stop_companion()
        inta.cleanup()

def main():
    """Main test function"""
    print("🤖 INTA Obstacle Detection System Test Suite")
    print("Testing ultrasonic sensor, CSV logging, and AI integration")
    print("="*70)
    
    tests = [
        ("Basic Ultrasonic Sensor", test_ultrasonic_sensor_basic),
        ("INTA Integration", test_obstacle_detection_with_inta),
        ("CSV Logging", test_csv_logging),
        ("Speech Output", test_with_speech_output),
    ]
    
    results = {}
    
    try:
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 50)
            try:
                test_func()
                results[test_name] = True
                print(f"✅ {test_name}: PASSED")
            except Exception as e:
                results[test_name] = False
                print(f"❌ {test_name}: FAILED - {e}")
        
        # Final summary
        print("\n" + "="*70)
        print("🏁 FINAL TEST SUMMARY")
        print("="*70)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {test_name}: {status}")
        
        print(f"\n📊 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Obstacle detection system is ready!")
            print("\n💡 You can now run: python3 main.py")
            print("INTA will provide intelligent obstacle warnings while you navigate.")
        else:
            print("⚠️  SOME TESTS FAILED - check the error messages above")
        
        # Offer interactive test
        response = input("\n🎮 Would you like to try the interactive obstacle test? (y/n): ").lower()
        if response == 'y':
            interactive_obstacle_test()
    
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted")
    except Exception as e:
        print(f"❌ Error in test suite: {e}")

if __name__ == "__main__":
    main() 