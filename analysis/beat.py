import aubio


class BeatTracker:
    def __init__(self, sample_rate=44100, win_s=1024, hop_s=512):
        self._tempo = aubio.tempo("default", win_s, hop_s, sample_rate)
        self._hop_s = hop_s
        self._bpm = 0.0

    def process(self, samples):
        if len(samples) < self._hop_s:
            return False
        beat = self._tempo(samples)
        self._bpm = self._tempo.get_bpm()
        return bool(beat)

    @property
    def bpm(self):
        return self._bpm
