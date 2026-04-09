from __future__ import annotations
from .base import SensorBase, Reading, iso_ts

class MicNoise(SensorBase):
    name = "mic_noise"

    def __init__(self, channel: int = 0, threshold: float = 0.003, period_s: float = 0.2):
        self.channel = channel
        self.threshold = threshold
        self.period_s = period_s
        self.device = None
        self._fallback = False

    def init(self) -> None:
        try:
            from gpiozero import MCP3008
            self.device = MCP3008(channel=self.channel)
        except Exception:
            self._fallback = True

    def close(self) -> None:
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
                    meta={"error": "MCP3008 not initialized"},
                )
            ]

        raw = self.device.value  # 0.0 - 1.0
        detected = 1.0 if raw > self.threshold else 0.0

        return [
            Reading(
                ts=ts,
                sensor="noise_dba",
                value=detected,
                unit="trigger",
                status="ok",
                meta={
                    "raw": raw,
                    "threshold": self.threshold,
                },
            )
        ]
