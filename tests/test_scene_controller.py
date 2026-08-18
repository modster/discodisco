import asyncio
import json

import pytest

from analysis.scenes import Scene, SEED_PALETTE, SceneController


class FakeClient:
    """Fake NATS-like client recording tool_exec requests."""

    def __init__(self):
        self.sent = []

    async def tool_exec(self, device, tool, params):
        self.sent.append((device, tool, params))
        return {"ok": True}


def test_picks_scene_on_event():
    ctrl = SceneController(
        client=FakeClient(), device="wireclaw-01", palette=SEED_PALETTE
    )
    asyncio.run(ctrl.handle_event("song_change"))
    assert ctrl.current_scene in [s.name for s in SEED_PALETTE]


def test_applies_scene_as_tool_calls():
    client = FakeClient()
    ctrl = SceneController(client=client, device="wireclaw-01", palette=SEED_PALETTE)
    asyncio.run(ctrl.handle_event("drop"))
    tools = {t for _, t, _ in client.sent}
    assert "ring_chase" in tools
    assert "stepper_set" not in tools
    # every call targets the controller device
    assert all(d == "wireclaw-01" for d, _, _ in client.sent)


def test_calmer_scene_for_silence():
    client = FakeClient()
    ctrl = SceneController(client=client, device="w", palette=SEED_PALETTE)
    asyncio.run(ctrl.handle_event("silence"))
    # silence should settle toward a calm scene, not rage
    assert ctrl.current_scene != "rage"
