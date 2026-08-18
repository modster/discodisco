import numpy as np

SILENCE_RMS = 0.01
SILENCE_BUFFERS = 10
CENTROID_SHIFT = 0.5
# Minimum number of buffers between song-change events, so a single spectral
# shift can't fire a constant stream of events (which would hammer the improv).
SONG_CHANGE_COOLDOWN = 20


class EventDetector:
    def __init__(self, sample_rate=44100, buffer_size=4410):
        self._sample_rate = sample_rate
        self._buffer_size = buffer_size
        self._silent_buffers = 0
        self._silence = False
        self._centroid_history = []
        self._since_change = SONG_CHANGE_COOLDOWN  # allow the first change

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
        if self._centroid_history and self._since_change >= SONG_CHANGE_COOLDOWN:
            baseline = float(np.mean(self._centroid_history))
            if baseline > 0 and abs(centroid - baseline) / baseline > CENTROID_SHIFT:
                changed = True
        self._centroid_history.append(centroid)
        if len(self._centroid_history) > 20:
            self._centroid_history.pop(0)
        if changed:
            self._since_change = 0
        else:
            self._since_change += 1
        return changed

    @property
    def silence(self):
        return self._silence
