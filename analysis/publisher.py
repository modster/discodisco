import json

import nats


class Publisher:
    def __init__(self, url="nats://127.0.0.1:4222"):
        self._url = url
        self._nc = None

    async def connect(self):
        self._nc = await nats.connect(self._url)

    async def close(self):
        if self._nc:
            await self._nc.close()

    async def publish_bands(self, levels):
        for name in ("low", "mid", "high"):
            await self._nc.publish(f"disco.band.{name}", f"{levels[name]:.1f}".encode())

    async def publish_bpm(self, bpm):
        await self._nc.publish("disco.bpm", f"{bpm:.1f}".encode())

    async def publish_beat(self, ts, bpm):
        await self._nc.publish(
            "disco.beat", json.dumps({"ts": ts, "bpm": bpm}).encode()
        )

    async def publish_event(self, event_type, ts):
        await self._nc.publish(
            "disco.event", json.dumps({"type": event_type, "ts": ts}).encode()
        )
