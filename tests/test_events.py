import numpy as np
import pytest

from analysis.events import EventDetector


def _sine(freq, sample_rate=44100, seconds=0.5):
    t = np.arange(int(sample_rate * seconds)) / sample_rate
    return np.sin(2 * np.pi * freq * t).astype(np.float32)


def test_silence_detected_after_quiet():
    d = EventDetector(sample_rate=44100)
    for _ in range(20):
        d.process(np.zeros(4410, dtype=np.float32))
    assert d.silence


def test_no_silence_during_loud():
    d = EventDetector(sample_rate=44100)
    for _ in range(20):
        d.process(_sine(440))
    assert not d.silence


def test_song_change_detected_on_spectral_shift():
    d = EventDetector(sample_rate=44100)
    for _ in range(10):
        d.process(_sine(200))
    changed = d.process(_sine(8000))
    assert changed


def test_no_song_change_on_stable_input():
    d = EventDetector(sample_rate=44100)
    for _ in range(10):
        d.process(_sine(200))
    changed = d.process(_sine(200))
    assert not changed
