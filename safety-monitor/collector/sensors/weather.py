from __future__ import annotations
from typing import Any, Dict
import time
from .base import SensorBase, Reading, iso_ts

class WeatherBME280(SensorBase):
    name = "weather_bme280"

    def __init__(self, i2c_bus: int, i2c_addr: int, period_s: float = 2.0):
        self.i2c_bus = i2c_bus
        self.i2c_addr = i2c_addr
        self.period_s = period_s
        self._bme = None
        self._fallback = False

    def init(self) -> None:
        # Try to init BME280 via smbus2 + minimal register reads.
        # If not found, we fall back to dummy data (so your pipeline is testable).
        try:
            from smbus2 import SMBus
            self._bus = SMBus(self.i2c_bus)
            # Quick probe: read chip id register 0xD0 (BME280 should be 0x60)
            chip_id = self._bus.read_byte_data(self.i2c_addr, 0xD0)
            if chip_id != 0x60:
                self._fallback = True
            else:
                self._fallback = True  # KEEP fallback unless you implement full compensation math
        except Exception:
            self._fallback = True

    def close(self) -> None:
        try:
            self._bus.close()
        except Exception:
            pass

    def read(self) -> list[Reading]:
        if self._fallback:
            # Fallback values for pipeline testing
            # Replace with real BME280 logic later (compensation formulas).
            t = 22.0 + (time.time() % 10) * 0.05
            rh = 40.0 + (time.time() % 10) * 0.1
            p = 1013.0 + (time.time() % 10) * 0.2
            ts = iso_ts()
            return [
                Reading(ts=ts, sensor="temperature", value=float(t), unit="C", meta={"source": "fallback_bme280"}),
                Reading(ts=ts, sensor="humidity", value=float(rh), unit="%", meta={"source": "fallback_bme280"}),
                Reading(ts=ts, sensor="pressure", value=float(p), unit="hPa", meta={"source": "fallback_bme280"}),
            ]

        # If you later add real BME280 readings, return them here
        ts = iso_ts()
        return [Reading(ts=ts, sensor="weather", value=0.0, unit="unitless", status="error",
                        meta={"error": "BME280 reading not implemented"})]
