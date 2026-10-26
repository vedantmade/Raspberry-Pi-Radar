# Raspberry Pi Radar — Arduino Uno Edition

A browser-based radar visualization using an **Arduino Uno**, **HC-SR04 ultrasonic sensor**, and **SG90 servo**. The Arduino sweeps the sensor and sends angle/distance readings over USB serial to a Python Flask bridge on your computer. The bridge serves data to the project's browser interface.

> This is an Arduino alternative to the original Raspberry Pi GPIO backend. It does not require a Raspberry Pi, but it does require an Arduino Uno connected to your computer by USB.

## Features

- Servo sweep from approximately 0° to 180° and back
- HC-SR04 distance measurements
- Live readings over USB serial
- Existing browser-based radar visualization, where the frontend API matches
- Start/stop and sweep-step controls
- Can run on a laptop without Raspberry Pi hardware

## Hardware required

- Arduino Uno (or compatible board)
- HC-SR04 ultrasonic sensor
- SG90 micro servo
- USB data cable
- Breadboard and jumper wires
- Recommended: separate regulated 5 V supply for the servo
- Computer with Python 3

## Wiring

| Component | Pin | Arduino Uno |
|---|---|---|
| SG90 servo | Signal (orange/yellow) | D9 |
| SG90 servo | VCC (red) | Regulated 5 V supply |
| SG90 servo | GND (brown/black) | GND |
| HC-SR04 | TRIG | D10 |
| HC-SR04 | ECHO | D11 |
| HC-SR04 | VCC | 5V |
| HC-SR04 | GND | GND |

### Power notes

- Connect the external servo supply's GND to Arduino GND (common ground).
- Do not power the servo from an Arduino I/O pin. A separate regulated 5 V supply is recommended.
- Check polarity and voltage before powering the circuit.
- Keep wires clear of the servo's moving arm.

## Software required

- Arduino IDE
- Python 3.9+ recommended
- Flask
- pySerial

## 1. Upload the Arduino firmware

1. Open `arduino/arduino_radar.ino` in Arduino IDE.
2. Connect the Arduino Uno over USB.
3. Select **Tools → Board → Arduino Uno** (or your compatible board).
4. Select the correct port under **Tools → Port**.
5. Upload the sketch and leave the Arduino connected.

Firmware pin assignments: servo signal D9, HC-SR04 TRIG D10, ECHO D11. Serial speed is **115200 baud**. Close Arduino IDE Serial Monitor before running the bridge because it may lock the serial port.

## 2. Install Python dependencies

Run these commands from the project folder containing `arduino_app.py`.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-arduino.txt
```

If PowerShell blocks environment activation, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-arduino.txt
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-arduino.txt
```

## 3. Run the bridge

```bash
python arduino_app.py
```

The bridge attempts to detect the Arduino port automatically. If needed, set the port explicitly.

### Windows PowerShell example

```powershell
$env:RADAR_SERIAL_PORT="COM3"
python arduino_app.py
```

Replace `COM3` with the port shown in Arduino IDE.

### macOS / Linux example

```bash
RADAR_SERIAL_PORT=/dev/ttyACM0 python arduino_app.py
```

Your port may instead look like `/dev/ttyUSB0` or `/dev/cu.usbmodem...`; use the actual device name.

Open the local URL printed by Flask, typically `http://127.0.0.1:5000`. The bridge is intended for local access; do not expose it directly to an untrusted network.

## Serial protocol

Arduino sends each reading as:

```text
angle,distance_cm
```

Example: `45,32.4`

The bridge can send these commands:

| Command | Purpose |
|---|---|
| `START` | Resume sweep |
| `STOP` | Pause sweep |
| `STEP:1` through `STEP:10` | Set sweep step size |

Distance is reported in centimetres. Accuracy depends on target size, angle, surface, and environment.

## Browser interface

The bridge is intended to provide the main routes used by the browser frontend:

- `/api/scan` — latest radar data
- `/api/control` — start, stop, and speed/step controls
- `/api/health` — bridge health

Reuse the original frontend files (`templates/index.html`, `static/style.css`, and `static/radar.js`) if present. If the frontend expects a different API response or control payload, compare it with `arduino_app.py` and adjust the bridge as needed.

## Current limitations

- Arduino handles servo movement and sensing; Python is the serial-to-web bridge.
- A physical proximity LED or buzzer is **not included** in this firmware yet.
- LED/buzzer alerts can be added later. Use a resistor with a standard LED, and a driver circuit for loads that exceed Arduino pin current limits.
- The software has not been physically tested against your hardware here. Test the wiring and serial readings before your demo.

## Troubleshooting

### No serial port detected
1. Check that the USB cable supports data.
2. Check the port in Arduino IDE.
3. Set `RADAR_SERIAL_PORT` explicitly.
4. Close Serial Monitor and other serial tools.
5. Try another cable or USB port.

### Serial port is busy
Close Arduino IDE Serial Monitor and any other serial terminal, then restart `arduino_app.py`.

### Servo jitters or Arduino resets
Use a separate regulated 5 V supply sized for the servo. Connect its ground to Arduino GND. Do not connect an external supply's positive rail to the Arduino 5 V pin unless you understand the board's power arrangement.

### Distance readings are zero or unstable
- Confirm TRIG → D10 and ECHO → D11.
- Confirm sensor VCC → 5V and GND → GND.
- Aim at a broad, flat target.
- Avoid soft fabric, angled surfaces, very close targets, and noisy environments.
- Ensure the sensor is not blocked by the servo mount.

### Web page does not update
- Confirm the sketch uploaded successfully.
- Confirm `arduino_app.py` is running and using the correct port.
- Check the terminal for serial or Flask errors.
- Ensure the browser frontend is compatible with the bridge API.

## Project structure

A typical Arduino-enabled checkout includes these files:

```text
Raspberry-Pi-Radar/
├── arduino/
│   └── arduino_radar.ino
├── arduino_app.py
├── requirements-arduino.txt
├── templates/
├── static/
└── README_ARDUINO.md
```

Your exact layout may differ depending on how the Arduino files are copied into the original repository.

## Original Raspberry Pi version

The original project targets Raspberry Pi GPIO. This Arduino edition is an alternative for setups where an Uno is available. Use the matching README and backend for the hardware connected to your system.

## License

Follow the license terms in the original repository. Retain its license and attribution notices when redistributing this adaptation.
