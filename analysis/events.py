import numpy as np

SILENCE_RMS = 0.01
SILENCE_BUFFERS = 10
CENTROID_SHIFT = 0.5


class EventDetector:
    def __init__(self, sample_rate=44100, buffer_size=4410):
        self._sample_rate = sample_rate
        self._buffer_size = buffer_size
        self._silent_buffers = 0
        self._silence = False
        self._centroid_history = []

    def _centroid(self, samples):
        fft = np.abs(np.fft.rfft(samples))
        freqs = np.fft.rfftfreq(len(samples), 1.0 / self._sample_rate)
        total = fft.sum()
        if total == 0:
            return 0.0
        return float((freqs * fft).sum() / total)

    def process(self, samples):
        rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
        if rms < SILENCE_RMS:
            self._silent_buffers += 1
        else:
            self._silent_buffers = 0
        self._silence = self._silent_buffers >= SILENCE_BUFFERS

        centroid = self._centroid(samples)
        changed = False
        if self._centroid_history:
            baseline = float(np.mean(self._centroid_history))
            if baseline > 0 and abs(centroid - baseline) / baseline > CENTROID_SHIFT:
                changed = True
        self._centroid_history.append(centroid)
        if len(self._centroid_history) > 20:
            self._centroid_history.pop(0)
        return changed

    @property
    def silence(self):
        return self._silence
