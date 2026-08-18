import asyncio
import json

from analysis.improv import ImprovAgent
from analysis.scenes import Scene


class FakeNATS:
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


class FakePicker:
    """Deterministic stand-in for the OpenClaw LLM scene picker."""

    def __init__(self, scene):
        self.scene = scene
        self.calls = 0

    async def pick(self, event_type):
        self.calls += 1
        return self.scene


def make_agent(scene):
    nc = FakeNATS()
    agent = ImprovAgent(nc, device="wireclaw-01", picker=FakePicker(scene))
    asyncio.run(agent.start())
    return nc, agent


def test_agent_subscribes_to_disco_event():
    nc, _ = make_agent(Scene(name="pulse"))
    assert "disco.event" in nc._handlers


def test_agent_applies_picked_scene_on_event():
    scene = Scene(
        name="pulse",
        band_colors={"low": (10, 20, 30), "mid": (1, 2, 3), "high": (4, 5, 6)},
    )
    nc, agent = make_agent(scene)

    async def go():
        await nc.publish("disco.event", json.dumps({"type": "drop", "ts": 1}).encode())

    asyncio.run(go())
    tools = {t.get("tool") for _, t in nc.tool_calls}
    assert "ring_set" in tools
    assert "stepper_set" in tools
    # the picked scene's low color is applied to the low-band LEDs (0-2)
    ring = next(t for _, t in nc.tool_calls if t.get("tool") == "ring_set")
    assert ring["leds"][0] == (10 << 16) | (20 << 8) | 30


def test_agent_uses_picker_per_event():
    scene = Scene(name="pulse")
    nc, agent = make_agent(scene)

    async def go():
        await nc.publish(
            "disco.event", json.dumps({"type": "song_change", "ts": 1}).encode()
        )
        await nc.publish("disco.event", json.dumps({"type": "drop", "ts": 2}).encode())

    asyncio.run(go())
    assert agent._picker.calls == 2


def test_agent_ignores_malformed_event():
    scene = Scene(name="pulse")
    nc, agent = make_agent(scene)

    async def go():
        await nc.publish("disco.event", b"not json")

    asyncio.run(go())
    assert nc.tool_calls == []


def test_agent_survives_device_offline():
    """A NoRespondersError on tool_exec must not kill the subscription loop."""
    scene = Scene(name="pulse")

    class FlakyNATS(FakeNATS):
        def __init__(self):
            super().__init__()
            self.fail_next = True

        async def request(self, subject, payload, timeout=10):
            if self.fail_next:
                self.fail_next = False
                raise Exception("nats: no responders available for request")
            return await super().request(subject, payload, timeout)

    nc = FlakyNATS()
    agent = ImprovAgent(nc, device="wireclaw-01", picker=FakePicker(scene))
    asyncio.run(agent.start())

    async def go():
        # first event: device offline (request raises) -> must not crash
        await nc.publish("disco.event", json.dumps({"type": "drop", "ts": 1}).encode())
        # second event: device back -> must still apply
        await nc.publish("disco.event", json.dumps({"type": "drop", "ts": 2}).encode())

    asyncio.run(go())
    tools = [t.get("tool") for _, t in nc.tool_calls]
    assert "ring_set" in tools  # the second event still applied a scene
