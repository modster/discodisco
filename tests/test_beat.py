import numpy as np
import pytest

from analysis.beat import BeatTracker


def _click_track(bpm, sample_rate=44100, seconds=4.0):
    n = int(sample_rate * seconds)
    t = np.arange(n) / sample_rate
    beat_interval = 60.0 / bpm
    clicks = np.zeros(n, dtype=np.float32)
    for start in np.arange(0, seconds, beat_interval):
        i = int(start * sample_rate)
        clicks[i : i + 200] = 0.9
    return clicks


def test_tracker_reports_bpm_near_ground_truth():
    tracker = BeatTracker(sample_rate=44100)
    samples = _click_track(120)
    for i in range(0, len(samples), 512):
        tracker.process(samples[i : i + 512])
    assert tracker.bpm == pytest.approx(120, abs=8)


def test_tracker_detects_beats():
    tracker = BeatTracker(sample_rate=44100)
    samples = _click_track(120)
    beats = 0
    for i in range(0, len(samples), 512):
        if tracker.process(samples[i : i + 512]):
            beats += 1
    assert beats >= 3


def test_tracker_silence_no_beats():
    tracker = BeatTracker(sample_rate=44100)
    silence = np.zeros(44100 * 2, dtype=np.float32)
    beats = 0
    for i in range(0, len(silence), 512):
        if tracker.process(silence[i : i + 512]):
            beats += 1
    assert beats == 0
