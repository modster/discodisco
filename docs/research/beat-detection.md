# Research: Realtime beat/BPM detection on a live Python stream

**Ticket:** #4 — Research: Realtime beat/BPM detection on a live Python stream
**Status:** Resolved **Date:** 2026-08-14

## Recommendation

Use **`aubio-ledfx`** (the maintained fork of aubio) for realtime beat/tempo
detection on a live stream in Python 3.13 on Windows.

## Why

- **aubio** is the classic C library for realtime onset/beat/tempo tracking,
  with a Python interface that processes audio **incrementally** (frame by
  frame) — ideal for a live stream, not just offline files.
- The **original aubio is no longer actively maintained** and lacks recent
  Python wheels. The **`aubio-ledfx`** fork (maintained by the LedFx team)
  provides **pre-built wheels for Python 3.10–3.14 on Windows AMD64** (confirmed
  on PyPI), so `pip install aubio-ledfx` works on this machine's Python 3.13
  with no compiler.
- It exposes both **beat events** (via `aubio.tempo`) and **BPM** (tempo's
  `get_bpm()`), which maps cleanly to the two things the disco ball needs: beat
  _events_ for flashes, and a BPM _value_ for stepper speed.

## Why not the alternatives

- **librosa** — excellent for offline analysis, but its beat tracking is
  batch-oriented (whole-file); not the natural fit for a low-latency live
  stream. Heavier dependency tree.
- **essentia** — powerful but historically painful to install on Windows (large
  native build); not worth the friction here.
- **Custom onset/energy-flux** — viable as a fallback (simple spectral flux
  threshold), but aubio already implements this well and is battle-tested;
  prefer aubio unless it proves problematic.

## Streaming architecture sketch

- **Capture** (PyAudioWPatch, see loopback-capture research): read 512–1024
  frames per callback on a dedicated thread.
- **FFT / band levels**: compute low/mid/high magnitudes with NumPy on each
  buffer (e.g. 1024-sample FFT at 44.1 kHz ≈ 23 ms window). Publish band levels
  to NATS continuously (e.g. every buffer or every N buffers).
- **Beat/BPM** (aubio-ledfx): feed the same buffers into an `aubio.tempo` object
  (e.g. `win_s=1024`, `hop_s=512`). On each `tempo()` call, if a beat is
  detected, publish a **beat event** to NATS. Read `tempo.get_bpm()`
  periodically (e.g. every 1–2 s) and publish the **BPM value** to NATS.
- **Update rate to NATS**: band levels ~20–40 Hz; beat events as they occur; BPM
  value ~0.5–1 Hz (it's a slowly-moving average).

## Sources

- PyPI — aubio-ledfx: https://pypi.org/project/aubio-ledfx/
- GitHub — LedFx/aubio-ledfx: https://github.com/LedFx/aubio-ledfx
- aubio manual: https://aubio.org/manual/latest/
- Real-time beat prediction with aubio:
  https://www.maxhaesslein.de/notes/real-time-beat-prediction-with-aubio/
