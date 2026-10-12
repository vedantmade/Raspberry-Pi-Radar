"""Hardware layer: a servo that rotates 0-180 degrees, an HC-SR04 ultrasonic sensor
and an optional warning LED.

Two implementations share the same interface:
  - RealHardware  uses gpiozero on a Raspberry Pi
  - SimHardware   fakes readings so the project runs on any laptop
"""
import math
import random
import time

from . import config


class RealHardware:
    def __init__(self):
        from gpiozero import AngularServo, Device, DistanceSensor

        # gpiozero picks a pin library automatically: lgpio on current Raspberry Pi OS
        # (the only one that works on a Pi 5), else RPi.GPIO / pigpio on older systems.
        # Override with GPIOZERO_PIN_FACTORY=lgpio|rpigpio|pigpio if needed.
        self.servo = AngularServo(
            config.SERVO_PIN,
            min_angle=0,
            max_angle=180,
            min_pulse_width=config.SERVO_MIN_PULSE,
            max_pulse_width=config.SERVO_MAX_PULSE,
        )
        # queue_len=1: use the newest ping only. The default averages the last 9 pings,
        # which would blend readings from several angles while sweeping.
        # partial=True: never block. Without it, reading .distance waits forever
        # if the sensor never answers (loose ECHO/TRIG wire), freezing the sweep.
        self.sensor = DistanceSensor(
            echo=config.ECHO_PIN,
            trigger=config.TRIG_PIN,
            max_distance=config.MAX_DISTANCE_CM / 100,  # gpiozero uses metres
            queue_len=1,
            partial=True,
        )
        self.led = None  # created on first use, so the pin is untouched unless the LED is enabled
        self.pin_factory = type(Device.pin_factory).__name__

    def move_to(self, angle):
        self.servo.angle = angle

    def read_distance_cm(self):
        # gpiozero returns metres, capped at max_distance. Exactly 0 means no ping has
        # come back yet (the HC-SR04 can't measure under ~2 cm), so report "nothing".
        cm = round(self.sensor.distance * 100, 1)
        return float(config.MAX_DISTANCE_CM) if cm <= 0 else cm

    def set_led(self, on):
        if self.led is None:
            if not on:
                return
            from gpiozero import LED
            self.led = LED(config.LED_PIN)
        self.led.value = bool(on)

    def close(self):
        for dev in (self.led, self.sensor):
            if dev is not None:
                dev.close()
        self.servo.detach()  # stop sending pulses so the servo doesn't buzz
        self.servo.close()


class SimHardware:
    """Pretends there are a few objects in the room."""

    pin_factory = None

    # (centre angle in degrees, width in degrees, distance in cm)
    OBJECTS = [(35, 12, 60), (95, 8, 140), (150, 15, 25)]

    def __init__(self):
        self.angle = 90
        self.led_on = False

    def move_to(self, angle):
        self.angle = angle

    def read_distance_cm(self):
        t = time.time()
        for centre, width, dist in self.OBJECTS:
            # objects drift slowly so the display looks alive
            centre = centre + 10 * math.sin(t / 7 + dist)
            if abs(self.angle - centre) <= width / 2:
                return round(dist + random.uniform(-3, 3), 1)
        return float(config.MAX_DISTANCE_CM)  # nothing in range

    def set_led(self, on):
        self.led_on = bool(on)

    def close(self):
        pass


def make_hardware(simulate):
    if simulate:
        return SimHardware()
    try:
        return RealHardware()
    except Exception as exc:  # not on a Pi, gpiozero missing, no GPIO permission...
        print(f"[radar] GPIO unavailable ({type(exc).__name__}: {exc}); falling back to simulation")
        return SimHardware()
