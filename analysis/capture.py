import asyncio
import threading

import pyaudiowpatch as pyaudio

from analysis.pipeline import Pipeline


class Capture:
    def __init__(self, pipeline, sample_rate=44100, frames_per_buffer=1024):
        self._pipeline = pipeline
        self._sample_rate = sample_rate
        self._frames_per_buffer = frames_per_buffer
        self._queue = asyncio.Queue()

    async def run(self):
        # PyAudio's stream.read() is blocking; run it in a dedicated thread so
        # it never starves the asyncio event loop (which flushes NATS + handles
        # the scene runner's subscription).
        loop = asyncio.get_running_loop()
        reader = threading.Thread(target=self._read_loop, args=(loop,), daemon=True)
        reader.start()
        try:
            while True:
                samples = await self._queue.get()
                await self._pipeline.process(samples)
        finally:
            reader.join(timeout=1)

    def _read_loop(self, loop):
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
                    loop.call_soon_threadsafe(self._queue.put_nowait, samples)
            finally:
                stream.stop_stream()
                stream.close()


def _to_float32(data, channels):
    import numpy as np

    raw = np.frombuffer(data, dtype=np.int16)
    if channels > 1:
        raw = raw[::channels]
    return raw.astype(np.float32) / 32768.0
