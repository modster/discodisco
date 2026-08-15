# Research: Windows loopback audio capture in Python

**Ticket:** #2 — Research: Windows loopback audio capture in Python **Status:**
Resolved **Date:** 2026-08-14

## Recommendation

Use **PyAudioWPatch** (`pip install PyAudioWPatch`) for WASAPI loopback capture
on Windows with Python 3.13.

## Why

- **PyAudioWPatch** is a maintained fork of PyAudio (PortAudio) that adds
  **WASAPI loopback** support — the only way to record the system's own audio
  output on Windows without a virtual cable.
- Ships **pre-built wheels for Windows, Python 3.7–3.13** (confirmed on PyPI),
  so `pip install` works on this machine's Python 3.13 with no compiler.
- Provides a first-class API: `get_default_wasapi_loopback()` returns the
  loopback device for the default speakers, and
  `get_wasapi_loopback_analogue_by_index()` for any output device. Loopback
  devices appear as virtual _input_ devices.
- API is drop-in compatible with classic PyAudio (`pyaudio.PyAudio()`,
  `p.open(...)`), so existing examples transfer.

## Why not the alternatives

- **sounddevice** (PortAudio bindings) — clean API and NumPy integration, but
  stock PortAudio's WASAPI host does **not** expose loopback devices. No
  loopback support out of the box.
- **Original PyAudio** — no WASAPI loopback at all (the reason PyAudioWPatch
  exists).
- **soundcard** — supports loopback but is less actively maintained and its API
  is less standard; PyAudioWPatch is the more battle-tested choice for this
  exact use case.

## Minimal working capture snippet

```python
import pyaudiowpatch as pyaudio

with pyaudio.PyAudio() as p:
    # Loopback device for the default speakers
    loopback = p.get_default_wasapi_loopback()
    with p.open(
        format=pyaudio.paInt16,
        channels=loopback["maxInputChannels"],
        rate=int(loopback["defaultSampleRate"]),
        frames_per_buffer=1024,
        input=True,
        input_device_index=loopback["index"],
    ) as stream:
        while True:
            data = stream.read(1024)   # bytes; feed to FFT / beat detector
            # ... process ...
```

## Latency characteristics to assume

- WASAPI loopback is a **shared-mode** capture; typical end-to-end latency is on
  the order of **tens of milliseconds** (buffer + WASAPI scheduling), well
  within the needs of a light show.
- Use a small `frames_per_buffer` (e.g. 512–1024) and a dedicated capture
  thread; the analysis process should be non-blocking on the audio callback.
- The pipeline should tolerate jitter: treat band levels as a continuous stream
  and BPM as a slowly-updating value, not a per-frame hard signal.

## Sources

- PyPI — PyAudioWPatch: https://pypi.org/project/PyAudioWPatch/
- GitHub — s0d3s/PyAudioWPatch: https://github.com/s0d3s/PyAudioWPatch
- PyPI — sounddevice: https://pypi.org/project/sounddevice/
