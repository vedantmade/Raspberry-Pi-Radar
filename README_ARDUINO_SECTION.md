
## Arduino Uno alternative (laptop-hosted radar interface)

This is an **alternative implementation** for labs where a Raspberry Pi is unavailable. It does not replace or modify the Raspberry Pi setup above. The Uno controls the HC-SR04 and SG90; a laptop runs Flask and serves the existing browser radar UI.

### Requirements

**Hardware**
- Arduino Uno R3 (or compatible ATmega328P Uno)
- HC-SR04 ultrasonic sensor
- SG90 micro servo and a bracket/mount for the sensor
- USB data cable compatible with the Uno
- Breadboard and jumper wires
- Recommended: regulated external 5 V supply for the servo, rated for its current; connect external-supply GND to Arduino GND
- Laptop with a browser

**Software**
- Arduino IDE 2.x (or Arduino CLI)
- Python 3.10+ recommended
- Flask and pyserial: `python -m pip install -r requirements-arduino.txt`
- Existing repository files `templates/index.html`, `static/style.css`, and `static/radar.js`

### Arduino wiring

| Component | Pin on component | Arduino Uno pin |
|---|---|---|
| SG90 | Signal (orange/yellow) | D9 |
| SG90 | VCC (red) | regulated 5 V supply (external supply recommended) |
| SG90 | GND (brown/black) | GND; common ground with external supply |
| HC-SR04 | TRIG | D10 |
| HC-SR04 | ECHO | D11 |
| HC-SR04 | VCC | 5V |
| HC-SR04 | GND | GND |

The Uno uses 5 V logic, so the HC-SR04 Echo output can connect directly to D11. Do **not** connect a servo's power lead to a digital pin. If using external servo power, all grounds must be connected together. Disconnect power before changing wiring. Servo colours can vary; verify the labels on your actual module.

### Upload and run

1. Open `arduino/arduino_radar.ino` in Arduino IDE.
2. Select **Arduino Uno** and the correct USB/serial port.
3. Upload the sketch. Close Arduino IDE Serial Monitor before starting the Python bridge (only one program can use the port at a time).
4. From the repository root, install dependencies:
   ```bash
   python -m pip install -r requirements-arduino.txt
   ```
5. Connect the Uno to the laptop with a USB **data** cable. If auto-detection fails, set the serial port explicitly:
   - Windows PowerShell: `$env:RADAR_SERIAL_PORT="COM3"; python arduino_app.py`
   - macOS/Linux: `RADAR_SERIAL_PORT=/dev/ttyACM0 python arduino_app.py` (replace with the actual port; macOS commonly uses `/dev/cu.usbmodem...`)
   - Otherwise: `python arduino_app.py`
6. Open `http://127.0.0.1:5000` in the laptop browser.
7. Place an object at a few known distances and verify that the angle and distance update. Check `/api/health` if the page shows offline or stale readings.

### Serial protocol and interface notes

- Baud rate: **115200**.
- Arduino sends one line per reading: `angle,distance_cm`, for example `90,42`.
- Laptop sends `START`, `STOP`, or `STEP:2` followed by a newline to control scanning.
- The bridge uses the existing radar page and API shape. It runs locally on `127.0.0.1`; it is not intended to be exposed to a public network.
- The optional proximity LED is **not implemented** in this Arduino variant. Its UI control is intentionally a no-op; the physical scan and radar display are the core demo.
- Arduino serial opening may reset the Uno; the bridge waits briefly after connecting.

### Limitations / troubleshooting

- The Uno cannot run Flask or host the web page itself. The laptop must remain connected by USB and run `arduino_app.py` for the browser interface to work.
- Choose the correct serial port and close Arduino IDE Serial Monitor/Plotter first. If the port is busy, permission-denied, or missing, `/api/health` reports the serial error.
- If no serial port is auto-detected, explicitly set `RADAR_SERIAL_PORT` to the port shown in Arduino IDE.
- If the servo jitters or the Uno resets, use a separate regulated 5 V servo supply with common ground; avoid powering the servo from the Uno's 5 V pin during testing.
- Keep the HC-SR04 sensor facing forward and securely mounted on the servo horn. Avoid forcing the servo by hand.
- This branch is an alternative implementation; the Raspberry Pi deployment using `app.py`, GPIO, and Apache remains unchanged.
