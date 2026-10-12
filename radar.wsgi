"""mod_wsgi entry point. Apache loads this file and serves the `application` object."""
import os
import sys

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)
# lgpio writes small helper files to the working directory, so it must be writable by www-data
os.chdir(APP_DIR)

# ---- settings (see radar/config.py for the full list) ----
os.environ.setdefault("RADAR_SIMULATE", "0")          # "1" = demo without hardware
os.environ.setdefault("RADAR_LED_ENABLED", "0")       # "1" = turn on the proximity LED
os.environ.setdefault("RADAR_LED_THRESHOLD_CM", "30") # LED lights below this distance
# os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")  # force a pin library if needed

from app import app as application  # noqa: E402
