import asyncio

from analysis.commands import CommandController, RESERVED_COMMANDS


class FakeClient:
    def __init__(self):
        self.sent = []

    async def tool_exec(self, device, tool, params):
        self.sent.append((device, tool, params))
        return {"ok": True}


def test_reserved_commands_defined():
    assert "stop" in RESERVED_COMMANDS
    assert "off" in RESERVED_COMMANDS
    assert "calm" in RESERVED_COMMANDS
    assert "wild" in RESERVED_COMMANDS


def test_off_turns_everything_off():
    client = FakeClient()
    ctrl = CommandController(client=client, device="w")
    asyncio.run(ctrl.handle("off"))
    tools = {t for _, t, _ in client.sent}
    assert "ring_set" in tools
    assert "stepper_set" in tools
    # off: ring black, stepper stopped
    ring = next(p for _, t, p in client.sent if t == "ring_set")
    stepper = next(p for _, t, p in client.sent if t == "stepper_set")
    assert (ring["r"], ring["g"], ring["b"]) == (0, 0, 0)
    assert stepper["rpm"] == 0


def test_stop_stops_stepper():
    client = FakeClient()
    ctrl = CommandController(client=client, device="w")
    asyncio.run(ctrl.handle("stop"))
    stepper = next(p for _, t, p in client.sent if t == "stepper_set")
    assert stepper["rpm"] == 0


def test_calm_applies_calm_scene():
    client = FakeClient()
    ctrl = CommandController(client=client, device="w")
    asyncio.run(ctrl.handle("calm"))
    tools = {t for _, t, _ in client.sent}
    assert "ring_set" in tools
    assert "stepper_set" in tools


def test_wild_applies_wild_scene():
    client = FakeClient()
    ctrl = CommandController(client=client, device="w")
    asyncio.run(ctrl.handle("wild"))
    tools = {t for _, t, _ in client.sent}
    assert "ring_set" in tools
    assert "stepper_set" in tools


def test_unknown_command_is_noop():
    client = FakeClient()
    ctrl = CommandController(client=client, device="w")
    asyncio.run(ctrl.handle("dance"))
    assert client.sent == []
