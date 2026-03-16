from __future__ import annotations
import json
import zmq

class ZmqSubscriber:
    def __init__(self, connect: str, topics: list[str] | None = None):
        self.ctx = zmq.Context.instance()
        self.sock = self.ctx.socket(zmq.SUB)
        self.sock.connect(connect)
        if not topics:
            topics = ["reading", "event"]
        for t in topics:
            self.sock.setsockopt_string(zmq.SUBSCRIBE, t)

    def recv(self, timeout_ms: int = 200):
        self.sock.RCVTIMEO = timeout_ms
        try:
            msg = self.sock.recv_string()
        except zmq.error.Again:
            return None, None
        topic, payload = msg.split(" ", 1)
        return topic, json.loads(payload)

    def close(self):
        try:
            self.sock.close(0)
        except Exception:
            pass
