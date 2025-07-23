# save_serial_data.py

import serial
import time
import csv

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)

with open('sensor_data.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Distance'])  # 헤더 한 줄 추가

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                print(f"Received: {line}")
                try:
                    distance = float(line)
                    writer.writerow([distance])
                    csvfile.flush()  # 실시간으로 디스크에 저장
                except ValueError:
                    print("Invalid float value")
    except KeyboardInterrupt:
        print("Stopped")
    finally:
        ser.close()
