from __future__ import annotations

import os
import sqlite3
import threading
from typing import Any, Dict, List

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .messaging.zmq_sub import ZmqSubscriber

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "config.yaml")


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


cfg = load_config(CONFIG_PATH)
db_path = cfg["storage"]["sqlite_path"]
zmq_connect = cfg["messaging"]["zmq_sub_connect"]

app = FastAPI(title="SiteGuard Dashboard")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

LATEST: Dict[str, Dict[str, Any]] = {}
EVENTS: List[Dict[str, Any]] = []
LOCK = threading.Lock()


def db_conn():
    return sqlite3.connect(db_path, check_same_thread=False)


def subscriber_thread():
    sub = ZmqSubscriber(zmq_connect)
    while True:
        topic, payload = sub.recv(timeout_ms=500)
        if topic is None:
            continue

        with LOCK:
            if topic == "reading":
                LATEST[payload["sensor"]] = payload
            elif topic == "event":
                EVENTS.append(payload)
                if len(EVENTS) > 200:
                    EVENTS.pop(0)


threading.Thread(target=subscriber_thread, daemon=True).start()


@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "site_name": cfg.get("site", {}).get("name", "SiteGuard"),
        },
    )


@app.get("/api/latest")
def api_latest():
    with LOCK:
        return JSONResponse(
            {
                "latest": LATEST,
                "events": EVENTS[-50:],
            }
        )


@app.get("/api/history")
def api_history(sensor: str, limit: int = 300):
    conn = db_conn()
    cur = conn.execute(
        """
        SELECT ts, value, unit, status
        FROM readings
        WHERE sensor=?
        ORDER BY id DESC
        LIMIT ?
        """,
        (sensor, limit),
    )
    rows = cur.fetchall()
    conn.close()

    rows.reverse()

    return JSONResponse(
        {
            "sensor": sensor,
            "points": [
                {
                    "ts": r[0],
                    "value": r[1],
                    "unit": r[2],
                    "status": r[3],
                }
                for r in rows
            ],
        }
    )


@app.get("/api/events")
def api_events(limit: int = 200):
    conn = db_conn()
    cur = conn.execute(
        """
        SELECT ts, type, severity, rule, message, context_json
        FROM events
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    rows.reverse()

    return JSONResponse(
        {
            "events": [
                {
                    "ts": r[0],
                    "type": r[1],
                    "severity": r[2],
                    "rule": r[3],
                    "message": r[4],
                    "context_json": r[5],
                }
                for r in rows
            ]
        }
    )