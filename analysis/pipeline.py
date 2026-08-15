import time

from analysis.bands import Normalizer, compute_band_levels
from analysis.beat import BeatTracker
from analysis.events import EventDetector


class Pipeline:
    def __init__(self, publisher, sample_rate=44100, hop_s=512):
        self._publisher = publisher
        self._sample_rate = sample_rate
        self._hop_s = hop_s
        self._normalizers = {name: Normalizer() for name in ("low", "mid", "high")}
        self._beat = BeatTracker(sample_rate=sample_rate, hop_s=hop_s)
        self._events = EventDetector(sample_rate=sample_rate, buffer_size=hop_s)
        self._last_bpm_pub = 0.0

    async def process(self, samples):
        raw = compute_band_levels(samples, self._sample_rate)
        levels = {name: self._normalizers[name].normalize(raw[name]) for name in raw}
        await self._publisher.publish_bands(levels)

        for i in range(0, len(samples) - self._hop_s + 1, self._hop_s):
            if self._beat.process(samples[i : i + self._hop_s]):
                await self._publisher.publish_beat(
                    ts=int(time.time() * 1000), bpm=self._beat.bpm
                )

        now = time.time()
        if now - self._last_bpm_pub >= 1.0:
            await self._publisher.publish_bpm(self._beat.bpm)
            self._last_bpm_pub = now

        if self._events.process(samples):
            await self._publisher.publish_event(
                "song_change", ts=int(time.time() * 1000)
            )
        elif self._events.silence:
            await self._publisher.publish_event("silence", ts=int(time.time() * 1000))
