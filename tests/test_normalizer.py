import numpy as np
import pytest

from analysis.bands import Normalizer


def _sine(freq, sample_rate=44100, seconds=0.5):
    t = np.arange(int(sample_rate * seconds)) / sample_rate
    return np.sin(2 * np.pi * freq * t).astype(np.float32)


def test_normalizer_starts_at_zero():
    n = Normalizer()
    assert n.normalize(0.0) == 0.0


def test_normalizer_scales_to_peak():
    n = Normalizer()
    n.normalize(0.5)
    n.normalize(1.0)
    assert n.normalize(1.0) == pytest.approx(1.0)


def test_normalizer_output_between_zero_and_one():
    n = Normalizer()
    for _ in range(100):
        v = n.normalize(np.random.rand())
        assert 0.0 <= v <= 1.0


def test_normalizer_tracks_rising_peak():
    n = Normalizer()
    assert n.normalize(0.5) == pytest.approx(1.0)
    assert n.normalize(1.0) == pytest.approx(1.0)
    assert n.normalize(0.5) == pytest.approx(0.5)
