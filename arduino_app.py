"""Laptop Flask bridge for the Arduino Uno radar variant.

Run from the project root after installing Flask and pyserial:
    python arduino_app.py
Optional serial port override:
    RADAR_SERIAL_PORT=COM3 python arduino_app.py   (Windows)
    RADAR_SERIAL_PORT=/dev/ttyACM0 python arduino_app.py (Linux)
    RADAR_SERIAL_PORT=/dev/cu.usbmodemXXXX python arduino_app.py (macOS)
"""
import serial
import threading
import time
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Shared data object for frontend API
latest_data = {"angle": 90, "distance": 0}

# Set this to your Arduino's assigned port (e.g., 'COM3' or 'COM4')
SERIAL_PORT = 'COM6'  
BAUD_RATE = 9600

def read_from_arduino():
    global latest_data
    ser = None
    while True:
        try:
            print(f"Connecting to Arduino on {SERIAL_PORT}...")
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)  # Allow reset time after establishing serial link
            ser.reset_input_buffer()
            print("Serial connection established successfully!")

            while True:
                # If serial buffer is backed up, flush old stale data to stay real-time
                if ser.in_waiting > 64:
                    ser.reset_input_buffer()

                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    parts = line.split(',')
                    if len(parts) == 2:
                        try:
                            angle = int(parts[0])
                            distance = int(parts[1])
                            latest_data["angle"] = angle
                            latest_data["distance"] = distance
                        except ValueError:
                            pass
                else:
                    time.sleep(0.002)
        except serial.SerialException as e:
            print(f"Serial port error: {e}. Retrying in 3 seconds...")
            time.sleep(3)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 3 seconds...")
            time.sleep(3)
        finally:
            if ser is not None:
                try:
                    ser.close()
                except Exception:
                    pass
                ser = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan')
def get_scan():
    return jsonify(latest_data)

if __name__ == '__main__':
    # Start serial reading thread only when run directly
    thread = threading.Thread(target=read_from_arduino, daemon=True)
    thread.start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)