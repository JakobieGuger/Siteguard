from __future__ import annotations
from collections import deque
from typing import Deque, Dict

class RollingMedian:
    def __init__(self, window: int = 5):
        self.window = window
        self.buf: Deque[float] = deque(maxlen=window)

    def update(self, x: float) -> float:
        self.buf.append(x)
        s = sorted(self.buf)
        return s[len(s)//2]

class FilterBank:
    def __init__(self):
        self.med: Dict[str, RollingMedian] = {}

    def median(self, key: str, x: float, window: int = 5) -> float:
        if key not in self.med:
            self.med[key] = RollingMedian(window=window)
        return self.med[key].update(x)
