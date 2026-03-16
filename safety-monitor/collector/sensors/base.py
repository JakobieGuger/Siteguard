from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import time

@dataclass
class Reading:
    ts: str
    sensor: str
    value: float
    unit: str
    status: str = "ok"
    meta: Optional[Dict[str, Any]] = None

class SensorBase:
    name: str = "base"
    period_s: float = 1.0

    def init(self) -> None:
        pass

    def close(self) -> None:
        pass

    def read(self) -> list[Reading]:
        """
        Return 1..N readings (e.g., weather returns temp+humidity+pressure).
        Must never raise; errors should return Reading with status="error".
        """
        raise NotImplementedError

def iso_ts() -> str:
    # Local time ISO w/ offset (good enough for demo; production would use timezone-aware datetime)
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")
