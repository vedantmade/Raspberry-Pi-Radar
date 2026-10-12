"""Background thread that sweeps the servo 0 -> 180 -> 0, records a reading per step
and drives the optional proximity LED."""
import atexit
import threading
import time

from . import config
from .hardware import SimHardware, make_hardware


class RadarScanner:
    def __init__(self, simulate=False, step=config.STEP_DEG, settle_s=config.SETTLE_S):
        self.hw = make_hardware(simulate)
        self.simulated = isinstance(self.hw, SimHardware)
        self.step = step            # degrees per move
        self.settle_s = 0.03 if self.simulated else settle_s
        self.angle = 0
        self.direction = 1
        self.readings = {}          # angle -> distance_cm (latest per angle)
        self.last = {"angle": 0, "distance": None}  # most recent ping
        self.led_enabled = config.LED_ENABLED
        self.led_threshold = config.LED_THRESHOLD_CM
        self.led_on = False
        self.running = False
        self._lock = threading.Lock()
        self._led_lock = threading.Lock()  # LED is updated by the sweep and by web requests
        self._thread = None
        atexit.register(self.close)

    # ---- control -------------------------------------------------------
    def start(self):
        self.running = True
        if not (self._thread and self._thread.is_alive()):
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.running = False

    def set_speed(self, step):
        self.step = max(1, min(10, int(step)))

    def configure_led(self, enabled=None, threshold=None):
        if threshold is not None:
            self.led_threshold = max(2, min(config.MAX_DISTANCE_CM, int(threshold)))
        if enabled is not None:
            self.led_enabled = bool(enabled)
        self._update_led()

    def close(self):
        self.running = False
        try:
            self.hw.set_led(False)
            self.hw.close()
        except Exception:
            pass

    # ---- worker --------------------------------------------------------
    def _loop(self):
        while True:
            if not self.running:
                time.sleep(0.1)
                continue
            try:
                self.hw.move_to(self.angle)
                time.sleep(self.settle_s)
                dist = self.hw.read_distance_cm()
            except Exception as exc:  # a glitch on one ping shouldn't kill the sweep
                print(f"[radar] read failed at {self.angle} deg: {exc}")
                time.sleep(0.5)
                continue
            with self._lock:
                self.readings[self.angle] = dist
                self.last = {"angle": self.angle, "distance": dist}
            self._update_led()
            nxt = self.angle + self.direction * self.step
            if nxt > 180 or nxt < 0:
                self.direction *= -1
                nxt = self.angle + self.direction * self.step
            self.angle = max(0, min(180, nxt))

    def _nearest(self, points):
        objects = [p for p in points if p["distance"] < config.MAX_DISTANCE_CM]
        return min(objects, key=lambda p: p["distance"]) if objects else None

    def _update_led(self):
        """LED is on while anything in the latest sweep is closer than the threshold."""
        with self._lock:
            near = any(d < self.led_threshold for d in self.readings.values())
        on = self.led_enabled and near
        with self._led_lock:
            if on != self.led_on:
                self.hw.set_led(on)
                self.led_on = on

    # ---- data for the API ---------------------------------------------
    def snapshot(self):
        with self._lock:
            points = [{"angle": a, "distance": d} for a, d in sorted(self.readings.items())]
            last = dict(self.last)
        return {
            "angle": last["angle"],
            "distance": last["distance"],
            "running": self.running,
            "simulated": self.simulated,
            "max_distance": config.MAX_DISTANCE_CM,
            "step": self.step,
            "points": points,
            "nearest": self._nearest(points),
            "led": {
                "enabled": self.led_enabled,
                "threshold": self.led_threshold,
                "on": self.led_on,
            },
            "timestamp": time.time(),
        }
