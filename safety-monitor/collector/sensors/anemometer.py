from __future__ import annotations
import time
from .base import SensorBase, Reading, iso_ts

class Anemometer(SensorBase):
    name = "anemometer"

    def __init__(self, gpio_pin: int, factor_mps_per_hz: float, sample_window_s: float = 2.0, period_s: float = 2.0):
        self.gpio_pin = gpio_pin
        self.factor = factor_mps_per_hz
        self.sample_window_s = sample_window_s
        self.period_s = period_s
        self._fallback = False
        self._pulses = 0

    def init(self) -> None:
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self._pulses = 0

            def cb(_pin):
                self._pulses += 1

            GPIO.add_event_detect(self.gpio_pin, GPIO.FALLING, callback=cb, bouncetime=5)
        except Exception:
            self._fallback = True

    def close(self) -> None:
        if not self._fallback:
            try:
                self.GPIO.remove_event_detect(self.gpio_pin)
                self.GPIO.cleanup(self.gpio_pin)
            except Exception:
                pass

    def read(self) -> list[Reading]:
        ts = iso_ts()
        if self._fallback:
            # Simulate wind for pipeline testing
            v = 2.0 + (time.time() % 5) * 0.4
            return [Reading(ts=ts, sensor="wind_speed", value=float(v), unit="m/s", meta={"source": "fallback_anemo"})]

        self._pulses = 0
        start = time.time()
        while time.time() - start < self.sample_window_s:
            time.sleep(0.01)

        hz = self._pulses / self.sample_window_s
        wind_mps = hz * self.factor
        return [Reading(ts=ts, sensor="wind_speed", value=float(wind_mps), unit="m/s",
                        meta={"source": f"anemometer_gpio_{self.gpio_pin}", "hz": hz})]
