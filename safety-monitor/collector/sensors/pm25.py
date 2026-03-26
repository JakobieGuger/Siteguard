from __future__ import annotations
import serial
from .base import SensorBase, Reading, iso_ts

class PM25Sensor(SensorBase):
    name = "pm25"

    def __init__(self, port: str = "/dev/serial0", baudrate: int = 9600, period_s: float = 2.0):
        self.port = port
        self.baudrate = baudrate
        self.period_s = period_s
        self.ser = None
        self._fallback = False

    def init(self) -> None:
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=2)
            self.ser.reset_input_buffer()
        except Exception:
            self._fallback = True

    def close(self) -> None:
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass

    def _read_frame(self) -> bytes | None:
        if not self.ser:
            return None

        while True:
            first = self.ser.read(1)
            if not first:
                return None
            if first == b"\x42":
                second = self.ser.read(1)
                if second == b"\x4d":
                    rest = self.ser.read(30)
                    if len(rest) == 30:
                        return b"\x42\x4d" + rest

    def _parse_frame(self, frame: bytes) -> dict | None:
        if len(frame) != 32:
            return None

        # checksum: sum of first 30 bytes should equal last 2 bytes
        checksum = sum(frame[0:30]) & 0xFFFF
        received_checksum = (frame[30] << 8) | frame[31]
        if checksum != received_checksum:
            return None

        values = []
        for i in range(4, 30, 2):
            values.append((frame[i] << 8) | frame[i + 1])

        return {
            "pm1_0_cf1": values[0],
            "pm2_5_cf1": values[1],
            "pm10_cf1": values[2],
            "pm1_0_atm": values[3],
            "pm2_5_atm": values[4],
            "pm10_atm": values[5],
            "particles_0_3um": values[6],
            "particles_0_5um": values[7],
            "particles_1_0um": values[8],
            "particles_2_5um": values[9],
            "particles_5_0um": values[10],
            "particles_10um": values[11],
            "version": values[12],
        }

    def read(self) -> list[Reading]:
        ts = iso_ts()

        if self._fallback or self.ser is None:
            return [
                Reading(
                    ts=ts,
                    sensor="pm25",
                    value=0.0,
                    unit="ug/m3",
                    status="error",
                    meta={"error": "serial port not initialized"},
                )
            ]

        frame = self._read_frame()
        if frame is None:
            return [
                Reading(
                    ts=ts,
                    sensor="pm25",
                    value=0.0,
                    unit="ug/m3",
                    status="no_data",
                    meta={"source": self.port},
                )
            ]

        parsed = self._parse_frame(frame)
        if parsed is None:
            return [
                Reading(
                    ts=ts,
                    sensor="pm25",
                    value=0.0,
                    unit="ug/m3",
                    status="bad_frame",
                    meta={"source": self.port},
                )
            ]

        return [
            Reading(
                ts=ts,
                sensor="pm25",
                value=float(parsed["pm2_5_atm"]),
                unit="ug/m3",
                status="ok",
                meta={
                    "source": self.port,
                    "pm1_0_atm": parsed["pm1_0_atm"],
                    "pm10_atm": parsed["pm10_atm"],
                    "pm2_5_cf1": parsed["pm2_5_cf1"],
                },
            )
        ]
