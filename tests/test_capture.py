import numpy as np
import pytest

from analysis.capture import _to_float32


def test_mono_int16_to_float32():
    data = np.array([0, 16384, 32767, -32768], dtype=np.int16).tobytes()
    out = _to_float32(data, 1)
    assert out[0] == 0.0
    assert out[1] == pytest.approx(0.5)
    assert out[2] == pytest.approx(32767 / 32768.0)
    assert out[3] == pytest.approx(-1.0)


def test_stereo_takes_first_channel():
    interleaved = np.array([1000, 2000, 3000, 4000], dtype=np.int16).tobytes()
    out = _to_float32(interleaved, 2)
    assert len(out) == 2
    assert out[0] == pytest.approx(1000 / 32768.0)
    assert out[1] == pytest.approx(3000 / 32768.0)
