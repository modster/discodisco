import numpy as np
import pytest

from analysis.pipeline import Pipeline


class FakePublisher:
    def __init__(self):
        self.bands = []
        self.bpm = []
        self.beats = []
        self.events = []

    async def publish_bands(self, levels):
        self.bands.append(levels)

    async def publish_bpm(self, bpm):
        self.bpm.append(bpm)

    async def publish_beat(self, ts, bpm):
        self.beats.append((ts, bpm))

    async def publish_event(self, event_type, ts):
        self.events.append((event_type, ts))


def _sine(freq, sample_rate=44100, seconds=0.5):
    t = np.arange(int(sample_rate * seconds)) / sample_rate
    return np.sin(2 * np.pi * freq * t).astype(np.float32)


@pytest.mark.asyncio
async def test_pipeline_publishes_bands_and_bpm():
    pub = FakePublisher()
    p = Pipeline(publisher=pub, sample_rate=44100)
    for _ in range(10):
        await p.process(_sine(440))
    assert len(pub.bands) == 10
    assert set(pub.bands[0].keys()) == {"low", "mid", "high"}
    assert all(0.0 <= v <= 1.0 for v in pub.bands[0].values())


@pytest.mark.asyncio
async def test_pipeline_publishes_beat_events():
    pub = FakePublisher()
    p = Pipeline(publisher=pub, sample_rate=44100)
    samples = _click_track(120)
    for i in range(0, len(samples), 512):
        await p.process(samples[i : i + 512])
    assert len(pub.beats) >= 3


@pytest.mark.asyncio
async def test_pipeline_publishes_silence_event():
    pub = FakePublisher()
    p = Pipeline(publisher=pub, sample_rate=44100)
    for _ in range(30):
        await p.process(np.zeros(4410, dtype=np.float32))
    assert any(t == "silence" for t, _ in pub.events)


def _click_track(bpm, sample_rate=44100, seconds=4.0):
    n = int(sample_rate * seconds)
    t = np.arange(n) / sample_rate
    beat_interval = 60.0 / bpm
    clicks = np.zeros(n, dtype=np.float32)
    for start in np.arange(0, seconds, beat_interval):
        i = int(start * sample_rate)
        clicks[i : i + 200] = 0.9
    return clicks
