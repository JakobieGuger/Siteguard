from __future__ import annotations
import json
import zmq

class ZmqPublisher:
    def __init__(self, bind: str):
        self.ctx = zmq.Context.instance()
        self.sock = self.ctx.socket(zmq.PUB)
        self.sock.bind(bind)

    def publish(self, topic: str, payload: dict) -> None:
        msg = f"{topic} {json.dumps(payload)}"
        self.sock.send_string(msg)

    def close(self) -> None:
        try:
            self.sock.close(0)
        except Exception:
            pass
