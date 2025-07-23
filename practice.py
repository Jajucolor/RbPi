import serial
import time
import csv

port = '/dev/ttyUSB0'  # 아두이노 연결 포트 (환경에 맞게 바꿔줘)
baudrate = 9600

try:
    ser = serial.Serial(port, baudrate, timeout=1)
    time.sleep(2)  # 시리얼 연결 안정화 대기
    print("Serial port opened.")
    
    with open('sensor_data.csv', mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Distance(cm)', 'ButtonState'])  # 헤더 작성
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').rstrip()
                print(f"Received: {line}")
                
                if ',' in line:
                    distance_str, button_str = line.split(',')
                    try:
                        distance = float(distance_str)
                        button_state = int(button_str)
                        csv_writer.writerow([distance, button_state])
                    except ValueError:
                        print("Parsing error, skipping line.")
                else:
                    print("Invalid data format.")

except KeyboardInterrupt:
    print("Stopped by user.")

except serial.SerialException as e:
    print(f"Serial error: {e}")

finally:
    if ser.is_open:
        ser.close()
        print("Serial port closed.")