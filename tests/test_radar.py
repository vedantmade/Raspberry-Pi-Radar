"""Tests that run on any computer, using gpiozero's mock pins instead of a real Pi.

    python3 -m unittest discover -s tests -v
"""
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gpiozero import Device  # noqa: E402
from gpiozero.pins.mock import MockFactory, MockPWMPin  # noqa: E402

from radar import config  # noqa: E402
from radar.hardware import RealHardware, SimHardware  # noqa: E402
from radar.scanner import RadarScanner  # noqa: E402


class MockPinTestCase(unittest.TestCase):
    def setUp(self):
        Device.pin_factory = MockFactory(pin_class=MockPWMPin)

    def tearDown(self):
        Device.pin_factory.reset()


class RealHardwareTest(MockPinTestCase):
    """The gpiozero code path that runs on the Pi, with the pins mocked."""

    def test_servo_angle_maps_to_pulse_width(self):
        hw = RealHardware()
        servo_pin = Device.pin_factory.pin(config.SERVO_PIN)
        for angle, pulse in ((0, config.SERVO_MIN_PULSE), (180, config.SERVO_MAX_PULSE)):
            hw.move_to(angle)
            # duty cycle = pulse width / 20 ms frame
            self.assertAlmostEqual(servo_pin.state, pulse / 0.02, places=4)
        hw.close()

    def test_no_echo_reads_as_max_distance(self):
        hw = RealHardware()
        time.sleep(0.2)
        self.assertEqual(hw.read_distance_cm(), config.MAX_DISTANCE_CM)
        hw.close()

    def test_scanner_sweeps_with_gpio_hardware(self):
        scanner = RadarScanner(simulate=False, settle_s=0.001)
        self.assertFalse(scanner.simulated, "should use gpiozero, not fall back to simulation")
        scanner.set_speed(10)
        scanner.start()
        time.sleep(1.0)
        scanner.stop()
        self.assertGreater(len(scanner.snapshot()["points"]), 5, "sweep thread stalled")
        scanner.close()

    def test_led_pin_untouched_until_enabled(self):
        hw = RealHardware()
        hw.set_led(False)
        self.assertIsNone(hw.led)
        hw.set_led(True)
        self.assertTrue(Device.pin_factory.pin(config.LED_PIN).state)
        hw.set_led(False)
        self.assertFalse(Device.pin_factory.pin(config.LED_PIN).state)
        hw.close()


class FakeHardware(SimHardware):
    """Returns a fixed distance so the LED logic can be checked exactly."""

    def __init__(self, distance):
        super().__init__()
        self.distance = distance

    def read_distance_cm(self):
        return self.distance


class ScannerLedTest(unittest.TestCase):
    def make_scanner(self, distance):
        scanner = RadarScanner(simulate=True)
        scanner.hw = FakeHardware(distance)
        return scanner

    def sweep(self, scanner, seconds=0.3):
        scanner.start()
        time.sleep(seconds)
        scanner.stop()

    def test_led_off_by_default_even_when_close(self):
        scanner = self.make_scanner(10)
        self.sweep(scanner)
        self.assertFalse(scanner.hw.led_on)
        self.assertFalse(scanner.snapshot()["led"]["on"])

    def test_led_on_when_enabled_and_closer_than_threshold(self):
        scanner = self.make_scanner(10)
        scanner.configure_led(enabled=True, threshold=30)
        self.sweep(scanner)
        self.assertTrue(scanner.hw.led_on)

    def test_led_off_when_object_beyond_threshold(self):
        scanner = self.make_scanner(80)
        scanner.configure_led(enabled=True, threshold=30)
        self.sweep(scanner)
        self.assertFalse(scanner.hw.led_on)
        scanner.configure_led(threshold=100)
        self.assertTrue(scanner.hw.led_on)
        scanner.configure_led(enabled=False)
        self.assertFalse(scanner.hw.led_on)

    def test_sweep_stays_within_0_to_180(self):
        scanner = self.make_scanner(50)
        scanner.set_speed(10)
        self.sweep(scanner, seconds=1.5)
        angles = [p["angle"] for p in scanner.snapshot()["points"]]
        self.assertEqual(min(angles), 0)
        self.assertEqual(max(angles), 180)


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["RADAR_SIMULATE"] = "1"
        import importlib
        importlib.reload(config)
        import app as app_module
        cls.client = app_module.app.test_client()

    def test_scan_has_led_block(self):
        data = self.client.get("/api/scan").get_json()
        self.assertIn("led", data)
        self.assertEqual(set(data["led"]), {"enabled", "threshold", "on"})

    def test_led_control(self):
        res = self.client.post("/api/control", json={"action": "led", "enabled": True, "threshold": 45})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["led"], {"enabled": True, "threshold": 45})

    def test_bad_input_is_400(self):
        self.assertEqual(self.client.post("/api/control", json={"action": "fly"}).status_code, 400)
        res = self.client.post("/api/control", json={"action": "speed", "step": "fast"})
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
