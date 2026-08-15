import json

from analysis.scenes import SceneController


class SceneRunner:
    """Subscribes to disco.event and applies scenes to the controller.

    Bridges NATS to the SceneController: on each musical event, it selects a
    scene and pushes the scene's tool_exec calls to the controller via
    <device>.tool_exec. This is the autonomous improvisation loop (OpenClaw
    may also drive scenes directly, but this keeps the show moving even without
    an LLM in the loop).
    """

    def __init__(self, nc, device, palette):
        self._nc = nc
        self._device = device
        self._controller = SceneController(client=self, device=device, palette=palette)

    async def start(self):
        await self._nc.subscribe("disco.event", cb=self._on_event)

    async def _on_event(self, msg):
        try:
            payload = json.loads(msg.data.decode())
        except (ValueError, UnicodeDecodeError):
            return
        event_type = payload.get("type")
        if event_type:
            await self._controller.handle_event(event_type)

    async def tool_exec(self, device, tool, params):
        payload = json.dumps({"tool": tool, **params}).encode()
        await self._nc.request(f"{device}.tool_exec", payload, timeout=10)
