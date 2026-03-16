from __future__ import annotations
import sqlite3
import time
from typing import Any, Dict, Iterable, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  sensor TEXT NOT NULL,
  value REAL NOT NULL,
  unit TEXT NOT NULL,
  status TEXT NOT NULL,
  meta_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings(ts);
CREATE INDEX IF NOT EXISTS idx_readings_sensor_ts ON readings(sensor, ts);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  type TEXT NOT NULL,
  severity TEXT NOT NULL,
  rule TEXT NOT NULL,
  message TEXT NOT NULL,
  context_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
"""

class SqliteStore:
    def __init__(self, path: str):
        self.path = path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def insert_reading(self, r: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO readings(ts, sensor, value, unit, status, meta_json) VALUES(?,?,?,?,?,?)",
            (r["ts"], r["sensor"], float(r["value"]), r["unit"], r.get("status","ok"), r.get("meta_json")),
        )
        self.conn.commit()

    def insert_event(self, e: Dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO events(ts, type, severity, rule, message, context_json) VALUES(?,?,?,?,?,?)",
            (e["ts"], e["type"], e["severity"], e["rule"], e["message"], e.get("context_json")),
        )
        self.conn.commit()

    def prune_older_than_hours(self, hours: float) -> None:
        # For demo: based on insertion time approximation. If you want exact, store epoch too.
        # We'll keep it simple: delete by rowid age using ts compare is messy w/ offsets.
        # A practical approach: just keep a max row count or store epoch seconds.
        # Here we do a row count fallback:
        max_rows = 200000  # adjust
        cur = self.conn.execute("SELECT COUNT(*) FROM readings")
        n = cur.fetchone()[0]
        if n > max_rows:
            # delete oldest 20%
            del_n = int(n * 0.2)
            self.conn.execute(
                "DELETE FROM readings WHERE id IN (SELECT id FROM readings ORDER BY id ASC LIMIT ?)",
                (del_n,),
            )
            self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
