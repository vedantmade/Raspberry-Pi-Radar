"""Laptop Flask bridge for the Arduino Uno radar variant.

Run from the project root after installing Flask and pyserial:
    python arduino_app.py
Optional serial port override:
    RADAR_SERIAL_PORT=COM3 python arduino_app.py   (Windows)
    RADAR_SERIAL_PORT=/dev/ttyACM0 python arduino_app.py (Linux)
    RADAR_SERIAL_PORT=/dev/cu.usbmodemXXXX python arduino_app.py (macOS)
"""
import os
import threading
import time

import serial
import serial.tools.list_ports
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
MAX_DISTANCE_CM = 200
BAUD_RATE = 115200
STEP_DEG = 2

class ArduinoRadarBridge:
    def __init__(self):
        self.lock = threading.Lock()
        self.ser = None
        self.serial_error = None
        self.running = True
        self.step = STEP_DEG
        self.points = {}
        self.last = {"angle": 0, "distance": None}
        self.started = False
        self.scanning = True
        self.port = os.environ.get("RADAR_SERIAL_PORT", "").strip() or None
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _choose_port(self):
        ports = list(serial.tools.list_ports.comports())
        if self.port:
            return self.port
        # Prefer common Uno USB serial identifiers; otherwise use the first available port.
        for p in ports:
            label = f"{p.device} {p.description} {p.manufacturer or ''}".lower()
            if any(k in label for k in ("arduino", "usb serial", "ch340", "wch", "usbmodem", "usb-serial")):
                return p.device
        return ports[0].device if ports else None

    def _connect(self):
        port = self._choose_port()
        if not port:
            raise RuntimeError("No serial port found. Connect the Uno or set RADAR_SERIAL_PORT.")
        self.ser = serial.Serial(port, BAUD_RATE, timeout=0.5, write_timeout=1)
        time.sleep(2.0)  # Uno resets when the serial port opens
        self.ser.reset_input_buffer()
        self.port = port
        self.serial_error = None

    def _reader(self):
        while self.running:
            try:
                if self.ser is None or not self.ser.is_open:
                    self._connect()
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 2:
                    continue
                angle, distance = int(parts[0]), float(parts[1])
                if not 0 <= angle <= 180 or not 0 <= distance <= MAX_DISTANCE_CM:
                    continue
                with self.lock:
                    self.last = {"angle": angle, "distance": distance}
                    self.points[angle] = distance
                    self.started = True
            except Exception as exc:
                self.serial_error = f"{type(exc).__name__}: {exc}"
                if self.ser is not None:
                    try:
                        self.ser.close()
                    except Exception:
                        pass
                    self.ser = None
                time.sleep(1.0)

    def command(self, text):
        if self.ser is None or not self.ser.is_open:
            return False
        try:
            self.ser.write((text + "\n").encode("ascii"))
            return True
        except Exception as exc:
            self.serial_error = f"{type(exc).__name__}: {exc}"
            return False

    def snapshot(self):
        with self.lock:
            points = [{"angle": a, "distance": d} for a, d in sorted(self.points.items())]
            last = dict(self.last)
        targets = [p for p in points if p["distance"] < MAX_DISTANCE_CM]
        nearest = min(targets, key=lambda p: p["distance"]) if targets else None
        return {
            "angle": last["angle"], "distance": last["distance"],
            "running": self.scanning, "simulated": False,
            "max_distance": MAX_DISTANCE_CM, "step": self.step,
            "points": points, "nearest": nearest,
            "led": {"enabled": False, "threshold": 30, "on": False},
            "timestamp": time.time(), "serial_port": self.port,
            "serial_error": self.serial_error,
        }

bridge = ArduinoRadarBridge()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/scan")
def api_scan():
    return jsonify(bridge.snapshot())

@app.route("/api/control", methods=["POST"])
def api_control():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action == "start":
        ok = bridge.command("START")
        if ok:
            bridge.scanning = True
    elif action == "stop":
        ok = bridge.command("STOP")
        if ok:
            bridge.scanning = False
    elif action == "speed":
        try:
            step = max(1, min(10, int(data.get("step", STEP_DEG))))
        except (TypeError, ValueError):
            return jsonify({"error": "step must be a number"}), 400
        bridge.step = step
        ok = bridge.command(f"STEP:{step}")
    elif action == "led":
        # The Arduino firmware does not implement a proximity LED.
        return jsonify({"ok": True, "led": {"enabled": False, "threshold": 30}})
    else:
        return jsonify({"error": "action must be start, stop, speed or led"}), 400
    if not ok:
        return jsonify({"ok": False, "error": bridge.serial_error or "Serial port not connected"}), 503
    return jsonify({"ok": True, "running": action != "stop", "step": bridge.step,
                    "led": {"enabled": False, "threshold": 30}})

@app.route("/api/health")
def health():
    state = bridge.snapshot()
    return jsonify({"status": "ok" if state["serial_error"] is None else "serial_error",
                    "simulated": False, "serial_port": state["serial_port"],
                    "serial_error": state["serial_error"]})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, threaded=True, use_reloader=False)
