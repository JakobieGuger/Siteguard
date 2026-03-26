from __future__ import annotations
from .base import SensorBase, Reading, iso_ts

class MicNoise(SensorBase):
    name = "mic_noise"

    def __init__(self, gpio_pin: int = 17, period_s: float = 0.5):
        self.gpio_pin = gpio_pin
        self.period_s = period_s
        self._fallback = False
        self.device = None

    def init(self) -> None:
        try:
            from gpiozero import DigitalInputDevice
            # pull_up depends on wiring; False is usually safer for these modules
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

        # HW-484 digital output acts like a threshold trigger, not a real dBA meter.
        detected = 1.0 if self.device.value else 0.0

        return [
            Reading(
                ts=ts,
                sensor="noise_dba",
                value=detected,
                unit="trigger",
                status="ok",
                meta={
                    "source": f"hw484_gpio_{self.gpio_pin}",
                    "meaning": "1 = sound threshold exceeded, 0 = below threshold",
                },
            )
        ]
