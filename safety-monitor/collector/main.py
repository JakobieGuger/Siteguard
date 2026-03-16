from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, List
import yaml

from sensors.weather import WeatherBME280
from sensors.anemometer import Anemometer
from sensors.pir_motion import PIRMotion
from sensors.mic_noise import MicNoise

from processing.filters import FilterBank
from processing.derived import heat_index_c
from processing.rules import RuleEngine

from messaging.zmq_pub import ZmqPublisher
from storage.sqlite import SqliteStore

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_dir(p: str) -> None:
    os.makedirs(os.path.dirname(p), exist_ok=True)

def reading_to_dict(r) -> Dict[str, Any]:
    return {
        "ts": r.ts,
        "sensor": r.sensor,
        "value": r.value,
        "unit": r.unit,
        "status": r.status,
        "meta": r.meta or {},
    }

def main() -> None:
    cfg = load_config("/home/pi/safety-monitor/config/config.yaml")

    pub_bind = cfg["messaging"]["zmq_pub_bind"]
    db_path = cfg["storage"]["sqlite_path"]
    retention_h = float(cfg["storage"].get("retention_hours", 24))

    ensure_dir(db_path)
    store = SqliteStore(db_path)
    pub = ZmqPublisher(pub_bind)

    # Build sensors
    sensors = []
    scfg = cfg.get("sensors", {})

    if scfg.get("weather_bme280", {}).get("enabled", False):
        w = scfg["weather_bme280"]
        s = WeatherBME280(i2c_bus=int(w["i2c_bus"]), i2c_addr=int(w["i2c_addr"]), period_s=float(w["period_s"]))
        sensors.append(s)

    if scfg.get("anemometer", {}).get("enabled", False):
        a = scfg["anemometer"]
        s = Anemometer(gpio_pin=int(a["gpio_pin"]),
                       factor_mps_per_hz=float(a["factor_mps_per_hz"]),
                       sample_window_s=float(a["sample_window_s"]),
                       period_s=float(a["period_s"]))
        sensors.append(s)

    if scfg.get("pir_motion", {}).get("enabled", False):
        p = scfg["pir_motion"]
        s = PIRMotion(gpio_pin=int(p["gpio_pin"]), period_s=float(p["period_s"]))
        sensors.append(s)

    if scfg.get("mic_noise", {}).get("enabled", False):
        m = scfg["mic_noise"]
        s = MicNoise(device=m.get("device", None),
                     sample_seconds=float(m.get("sample_seconds", 1.0)),
                     period_s=float(m["period_s"]))
        sensors.append(s)

    for s in sensors:
        s.init()

    filters = FilterBank()
    rules = RuleEngine(cfg.get("rules", {}))

    # scheduling
    next_due: Dict[str, float] = {s.name: time.time() for s in sensors}

    # Cache last weather pieces to derive heat index
    last_temp_c = None
    last_rh = None

    print(f"[collector] publishing on {pub_bind}")
    while True:
        now = time.time()

        # read due sensors
        for s in sensors:
            if now < next_due[s.name]:
                continue
            next_due[s.name] = now + float(getattr(s, "period_s", 1.0))

            try:
                readings = s.read()
            except Exception as e:
                # hard safety: never crash loop
                readings = []

            for r in readings:
                d = reading_to_dict(r)
                rules.update_last_seen(d["sensor"])

                # Filtering example (only for numeric stuff)
                if d["status"] == "ok":
                    d["value"] = filters.median(d["sensor"], float(d["value"]), window=5)

                # Store weather fragments for derived metric example
                if d["sensor"] == "temperature" and d["unit"] == "C" and d["status"] == "ok":
                    last_temp_c = float(d["value"])
                if d["sensor"] == "humidity" and d["unit"] == "%" and d["status"] == "ok":
                    last_rh = float(d["value"])

                # Derived metric: heat index
                if last_temp_c is not None and last_rh is not None:
                    hi = heat_index_c(last_temp_c, last_rh)
                    derived = {
                        "ts": d["ts"],
                        "sensor": "heat_index",
                        "value": hi,
                        "unit": "C",
                        "status": "ok",
                        "meta": {"source": "derived"},
                    }
                    # publish + store derived occasionally (not every reading)
                    pub.publish("reading", derived)
                    store.insert_reading({
                        **derived,
                        "meta_json": json.dumps(derived.get("meta", {})),
                    })
                    last_temp_c = None
                    last_rh = None

                # Publish + store reading
                pub.publish("reading", d)
                store.insert_reading({
                    **d,
                    "meta_json": json.dumps(d.get("meta", {})),
                })

                # Run rules for relevant sensors
                events = []
                if d["sensor"] == "noise_dba" and d["status"] == "ok":
                    events += rules.check_noise(float(d["value"]))
                if d["sensor"] == "wind_speed" and d["status"] == "ok":
                    events += rules.check_wind(float(d["value"]))

                for ev in events:
                    evd = {
                        "ts": ev.ts,
                        "type": ev.type,
                        "severity": ev.severity,
                        "rule": ev.rule,
                        "message": ev.message,
                        "context": ev.context,
                    }
                    pub.publish("event", evd)
                    store.insert_event({**evd, "context_json": json.dumps(evd.get("context", {}))})

        # sensor missing checks
        for ev in rules.check_sensor_missing():
            evd = {
                "ts": ev.ts,
                "type": ev.type,
                "severity": ev.severity,
                "rule": ev.rule,
                "message": ev.message,
                "context": ev.context,
            }
            pub.publish("event", evd)
            store.insert_event({**evd, "context_json": json.dumps(evd.get("context", {}))})

        # pruning (simple row-count based)
        store.prune_older_than_hours(retention_h)

        time.sleep(0.05)

if __name__ == "__main__":
    main()
