import numpy as np

LOW = (20, 250)
MID = (250, 2000)
HIGH = (2000, 20000)


class Normalizer:
    def __init__(self):
        self._peak = 0.0

    def normalize(self, value):
        self._peak = max(self._peak, value)
        if self._peak == 0.0:
            return 0.0
        return value / self._peak


def compute_band_levels(samples, sample_rate):
    fft = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)
    power = np.abs(fft) ** 2
    levels = {}
    for name, (lo, hi) in (("low", LOW), ("mid", MID), ("high", HIGH)):
        mask = (freqs >= lo) & (freqs < hi)
        levels[name] = float(np.sum(power[mask]))
    return levels
