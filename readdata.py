# read_csv_data.py

import csv
import time

csv_file = 'sensor_data.csv'

def read_latest_data():
    try:
        with open(csv_file, 'r') as f:
            reader = list(csv.reader(f))
            if len(reader) > 1:
                print("Last distance:", reader[-1][0])
            else:
                print("No data yet.")
    except FileNotFoundError:
        print("CSV file not found.")

while True:
    read_latest_data()
    time.sleep(1)
