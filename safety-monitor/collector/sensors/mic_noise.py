from __future__ import annotations
from .base import SensorBase, Reading, iso_ts

class MicNoise(SensorBase):
    name = "mic_noise"

    def __init__(self, gpio_pin: int = 7, period_s: float = 0.2):
        self.gpio_pin = gpio_pin
        self.period_s = period_s
        self._fallback = False
        self.device = None

    def init(self) -> None:
        try:
            from gpiozero import DigitalInputDevice
            self.device = DigitalInputDevice(self.gpio_pin, pull_up=False)
        except Exception:
            self._fallback = True

    def close(self) -> None:
        try:
            if self.device is not None:
                self.device.close()
        except Exception:
            pass

    def read(self) -> list[Reading]:
        ts = iso_ts()

        if self._fallback or self.device is None:
            return [
                Reading(
                    ts=ts,
                    sensor="noise_dba",
                    value=0.0,
                    unit="trigger",
                    status="error",
                    meta={"error": "gpiozero not available or sensor not initialized"},
                )
            ]

        # Many HW-484 style modules behave as active-low on DO:
        # 0 = threshold exceeded, 1 = quiet
        raw_gpio = self.device.value
        detected = 1.0 if not raw_gpio else 0.0

        return [
            Reading(
                ts=ts,
                sensor="noise_dba",
                value=detected,
                unit="trigger",
                status="ok",
                meta={
                    "source": f"hw484_gpio_{self.gpio_pin}",
                    "raw_gpio_value": raw_gpio,
                    "meaning": "1 = sound threshold exceeded, 0 = below threshold",
                },
            )
        ]
