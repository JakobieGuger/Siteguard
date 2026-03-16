from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import time

@dataclass
class Event:
    ts: str
    type: str
    severity: str
    rule: str
    message: str
    context: Dict[str, Any]

class RuleEngine:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self._noise_over_since: Optional[float] = None
        self._last_seen: Dict[str, float] = {}

    def update_last_seen(self, sensor_key: str) -> None:
        self._last_seen[sensor_key] = time.time()

    def check_sensor_missing(self) -> list[Event]:
        now = time.time()
        missing_s = float(self.cfg.get("sensor_missing_s", 10))
        events: list[Event] = []
        for k, last in list(self._last_seen.items()):
            if now - last > missing_s:
                events.append(Event(
                    ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    type="alert",
                    severity="warning",
                    rule="sensor_missing",
                    message=f"Sensor '{k}' missing for > {missing_s:.0f}s",
                    context={"sensor": k, "missing_s": now - last},
                ))
                # prevent spam: bump last_seen forward
                self._last_seen[k] = now
        return events

    def check_noise(self, noise_dba: float) -> list[Event]:
        warn = float(self.cfg.get("noise_dba_warning", 85))
        crit = float(self.cfg.get("noise_dba_critical", 95))
        dur = float(self.cfg.get("noise_duration_s", 10))

        now = time.time()
        events: list[Event] = []

        if noise_dba >= warn:
            if self._noise_over_since is None:
                self._noise_over_since = now
            if now - self._noise_over_since >= dur:
                sev = "critical" if noise_dba >= crit else "warning"
                events.append(Event(
                    ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    type="alert",
                    severity=sev,
                    rule=f"noise_over_{warn:.0f}dba_{dur:.0f}s",
                    message=f"Noise > {warn:.0f} dBA for {dur:.0f}s",
                    context={"noise_dba": noise_dba, "duration_s": now - self._noise_over_since},
                ))
                # reset to avoid spamming every tick; you can make this smarter later
                self._noise_over_since = now
        else:
            self._noise_over_since = None

        return events

    def check_wind(self, wind_mps: float) -> list[Event]:
        warn = float(self.cfg.get("wind_gust_warning_mps", 12))
        crit = float(self.cfg.get("wind_gust_critical_mps", 18))
        if wind_mps < warn:
            return []
        sev = "critical" if wind_mps >= crit else "warning"
        return [Event(
            ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            type="alert",
            severity=sev,
            rule="wind_gust",
            message=f"Wind speed high: {wind_mps:.1f} m/s",
            context={"wind_mps": wind_mps},
        )]
