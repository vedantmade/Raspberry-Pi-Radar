"""Flask backend for the Raspberry Pi radar.

Run locally:        python3 app.py              (falls back to simulation if no GPIO)
Force simulation:   RADAR_SIMULATE=1 python3 app.py
Under Apache:       loaded by radar.wsgi through mod_wsgi
Settings:           radar/config.py
"""
from flask import Flask, jsonify, render_template, request

from radar import config
from radar.scanner import RadarScanner

app = Flask(__name__)

scanner = RadarScanner(simulate=config.SIMULATE)
scanner.start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan")
def api_scan():
    """Current angle, current distance, LED state and the latest reading at every angle."""
    return jsonify(scanner.snapshot())


@app.route("/api/control", methods=["POST"])
def api_control():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    try:
        if action == "start":
            scanner.start()
        elif action == "stop":
            scanner.stop()
        elif action == "speed":
            scanner.set_speed(data.get("step", config.STEP_DEG))
        elif action == "led":
            scanner.configure_led(enabled=data.get("enabled"), threshold=data.get("threshold"))
        else:
            return jsonify({"error": "action must be start, stop, speed or led"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "step and threshold must be numbers"}), 400
    return jsonify({
        "ok": True,
        "running": scanner.running,
        "step": scanner.step,
        "led": {"enabled": scanner.led_enabled, "threshold": scanner.led_threshold},
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "simulated": scanner.simulated,
        "pin_factory": scanner.hw.pin_factory,
    })


if __name__ == "__main__":
    # threaded=True so the page can poll while the sweep thread runs;
    # use_reloader=False so only ONE sweep thread drives the servo.
    app.run(host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
