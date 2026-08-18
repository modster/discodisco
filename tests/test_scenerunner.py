import asyncio
import json

import pytest

from analysis.scenerunner import SceneRunner
from analysis.scenes import SEED_PALETTE


class FakeNATS:
    """Fake NATS connection capturing subscriptions and tool calls."""

    def __init__(self):
        self.tool_calls = []
        self._handlers = {}

    async def subscribe(self, subject, cb=None):
        self._handlers[subject] = cb
        return subject

    async def request(self, subject, payload, timeout=10):
        data = json.loads(payload.decode())
        self.tool_calls.append((subject, data))
        return type("Msg", (), {"data": json.dumps({"ok": True}).encode()})()

    async def publish(self, subject, payload):
        h = self._handlers.get(subject)
        if h:
            await h(type("Msg", (), {"data": payload})())

    async def close(self):
        pass


def make_runner():
    nc = FakeNATS()
    runner = SceneRunner(nc, device="wireclaw-01", palette=SEED_PALETTE)
    asyncio.run(runner.start())
    return nc, runner


def test_runner_subscribes_to_disco_event():
    nc, runner = make_runner()
    assert "disco.event" in nc._handlers


def test_runner_applies_scene_on_event():
    nc, runner = make_runner()

    async def go():
        await nc.publish("disco.event", json.dumps({"type": "drop", "ts": 1}).encode())

    asyncio.run(go())
    tools = {t.get("tool") for _, t in nc.tool_calls}
    assert "ring_chase" in tools
    assert "stepper_set" not in tools


def test_runner_targets_device_tool_exec():
    nc, runner = make_runner()

    async def go():
        await nc.publish(
            "disco.event", json.dumps({"type": "song_change", "ts": 1}).encode()
        )

    asyncio.run(go())
    assert all(s == "wireclaw-01.tool_exec" for s, _ in nc.tool_calls)
