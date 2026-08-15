import asyncio

import pyaudiowpatch as pyaudio

from analysis.pipeline import Pipeline


class Capture:
    def __init__(self, pipeline, sample_rate=44100, frames_per_buffer=1024):
        self._pipeline = pipeline
        self._sample_rate = sample_rate
        self._frames_per_buffer = frames_per_buffer

    async def run(self):
        with pyaudio.PyAudio() as p:
            loopback = p.get_default_wasapi_loopback()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=loopback["maxInputChannels"],
                rate=int(loopback["defaultSampleRate"]),
                frames_per_buffer=self._frames_per_buffer,
                input=True,
                input_device_index=loopback["index"],
            )
            try:
                while True:
                    data = stream.read(self._frames_per_buffer)
                    samples = _to_float32(data, loopback["maxInputChannels"])
                    await self._pipeline.process(samples)
            finally:
                stream.stop_stream()
                stream.close()


def _to_float32(data, channels):
    import numpy as np

    raw = np.frombuffer(data, dtype=np.int16)
    if channels > 1:
        raw = raw[::channels]
    return raw.astype(np.float32) / 32768.0
