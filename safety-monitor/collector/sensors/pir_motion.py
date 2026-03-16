from __future__ import annotations
from .base import SensorBase, Reading, iso_ts

class PIRMotion(SensorBase):
    name = "pir_motion"

    def __init__(self, gpio_pin: int, period_s: float = 1.0):
        self.gpio_pin = gpio_pin
        self.period_s = period_s
        self._fallback = False

    def init(self) -> None:
        try:
            import RPi.GPIO as GPIO
            self.GPIO = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.IN)
        except Exception:
            self._fallback = True

    def close(self) -> None:
        if not self._fallback:
            try:
                self.GPIO.cleanup(self.gpio_pin)
            except Exception:
                pass

    def read(self) -> list[Reading]:
        ts = iso_ts()
        if self._fallback:
            return [Reading(ts=ts, sensor="motion", value=0.0, unit="bool", status="ok",
                            meta={"source": "fallback_pir"})]

        val = 1.0 if self.GPIO.input(self.gpio_pin) else 0.0
        return [Reading(ts=ts, sensor="motion", value=val, unit="bool",
                        meta={"source": f"pir_gpio_{self.gpio_pin}"})]
