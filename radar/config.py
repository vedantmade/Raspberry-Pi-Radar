"""All settings in one place. Each can be overridden with an environment variable.

Under Apache, set them in radar.wsgi (Apache's SetEnv does not reach os.environ).
"""
import os


def _bool(name, default):
    return os.environ.get(name, "1" if default else "0").strip().lower() in ("1", "true", "yes", "on")


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _float(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


# Force fake hardware (laptop, or a demo without the sensor attached)
SIMULATE = _bool("RADAR_SIMULATE", False)

# BCM pin numbers (physical header pin in brackets)
SERVO_PIN = _int("RADAR_SERVO_PIN", 18)   # pin 12, servo signal (orange wire)
TRIG_PIN = _int("RADAR_TRIG_PIN", 23)     # pin 16, HC-SR04 TRIG
ECHO_PIN = _int("RADAR_ECHO_PIN", 24)     # pin 18, HC-SR04 ECHO (through the 1k/2k divider!)
LED_PIN = _int("RADAR_LED_PIN", 17)       # pin 11, LED + 330 ohm resistor to GND

# Servo pulse range: SG90 is roughly 0.5 ms (0 deg) to 2.4 ms (180 deg).
# Tune these if your servo does not reach the full sweep or buzzes at the ends.
SERVO_MIN_PULSE = _float("RADAR_SERVO_MIN_PULSE", 0.0005)
SERVO_MAX_PULSE = _float("RADAR_SERVO_MAX_PULSE", 0.0024)

# HC-SR04 works to ~400 cm; 200 cm is reliable indoors
MAX_DISTANCE_CM = _int("RADAR_MAX_DISTANCE_CM", 200)

# Sweep
STEP_DEG = _int("RADAR_STEP_DEG", 2)
# Wait after each move so the servo arrives and the sensor takes a fresh ping
# (gpiozero pings about every 60 ms in the background).
SETTLE_S = _float("RADAR_SETTLE_S", 0.08)

# Proximity LED (off by default; turn on here, in radar.wsgi, or from the web page)
LED_ENABLED = _bool("RADAR_LED_ENABLED", False)
LED_THRESHOLD_CM = _int("RADAR_LED_THRESHOLD_CM", 30)
