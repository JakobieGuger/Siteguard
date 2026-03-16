from __future__ import annotations
from .base import SensorBase, Reading, iso_ts

class MicNoise(SensorBase):
    name = "mic_noise"

    def __init__(self, device, sample_seconds: float = 1.0, period_s: float = 2.0):
        self.device = device
        self.sample_seconds = sample_seconds
        self.period_s = period_s
        self._fallback = False

    def init(self) -> None:
        try:
            import sounddevice as sd  # noqa
            import numpy as np        # noqa
        except Exception:
            self._fallback = True

    def close(self) -> None:
        pass

    def read(self) -> list[Reading]:
        ts = iso_ts()
        if self._fallback:
            return [Reading(ts=ts, sensor="noise_dba", value=45.0, unit="dBA", meta={"source": "fallback_mic"})]

        import sounddevice as sd
        import numpy as np
        fs = 44100
        audio = sd.rec(int(self.sample_seconds * fs), samplerate=fs, channels=1, dtype="float32", device=self.device)
        sd.wait()
        rms = float(np.sqrt(np.mean(np.square(audio))))
        # VERY rough: map RMS to dB-like scale for demo (not calibrated dBA).
        # For “real” dBA you'd calibrate with a known sound level meter.
        db = 20.0 * np.log10(max(rms, 1e-6)) + 90.0
        return [Reading(ts=ts, sensor="noise_dba", value=float(db), unit="dBA", meta={"source": "usb_mic_rms"})]
