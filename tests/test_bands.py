import numpy as np
import pytest

from analysis.bands import compute_band_levels


def _sine(freq, sample_rate=44100, seconds=0.5):
    t = np.arange(int(sample_rate * seconds)) / sample_rate
    return np.sin(2 * np.pi * freq * t).astype(np.float32)


def test_low_tone_dominates_low_band():
    samples = _sine(100)
    levels = compute_band_levels(samples, 44100)
    assert levels["low"] > levels["high"]


def test_high_tone_dominates_high_band():
    samples = _sine(5000)
    levels = compute_band_levels(samples, 44100)
    assert levels["high"] > levels["low"]


def test_mid_tone_dominates_mid_band():
    samples = _sine(1000)
    levels = compute_band_levels(samples, 44100)
    assert levels["mid"] > levels["low"]
    assert levels["mid"] > levels["high"]


def test_silence_is_near_zero():
    samples = np.zeros(44100, dtype=np.float32)
    levels = compute_band_levels(samples, 44100)
    assert levels["low"] < 1e-6
    assert levels["mid"] < 1e-6
    assert levels["high"] < 1e-6


def test_returns_three_bands():
    samples = _sine(100)
    levels = compute_band_levels(samples, 44100)
    assert set(levels.keys()) == {"low", "mid", "high"}
