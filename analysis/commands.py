from analysis.scenes import Scene, render_scene

# Reserved human-steering commands. These are the only words that override the
# autonomous improv; anything else is ignored.
RESERVED_COMMANDS = ("stop", "off", "calm", "wild")

# calm / wild map to scenes from the seed palette.
_CALM_SCENE = Scene(
    name="calm",
    band_colors={"low": (0, 60, 120), "mid": (40, 160, 220), "high": (200, 220, 255)},
    bpm_endpoints={"slow_bpm": 60, "fast_bpm": 150, "slow_rpm": 1, "fast_rpm": 4},
    direction="oscillate",
    beat_flash={"color": (255, 255, 255), "threshold": 0.9, "duration_ms": 120},
)
_WILD_SCENE = Scene(
    name="wild",
    band_colors={"low": (255, 0, 0), "mid": (255, 60, 0), "high": (255, 255, 0)},
    bpm_endpoints={"slow_bpm": 60, "fast_bpm": 180, "slow_rpm": 6, "fast_rpm": 15},
    direction="ccw",
    beat_flash={"color": (255, 255, 255), "threshold": 0.4, "duration_ms": 220},
)


class CommandController:
    """Handles reserved human-steering commands.

    These override the autonomous improv: 'off' turns everything off, 'stop'
    halts the stepper, 'calm' applies a calm scene, 'wild' applies a wild one.
    Unknown commands are ignored so stray words never yank the show around.
    """

    def __init__(self, client, device):
        self._client = client
        self._device = device

    async def handle(self, command):
        command = command.strip().lower()
        if command == "off":
            await self._apply_off()
        elif command == "stop":
            await self._client.tool_exec(
                self._device, "stepper_set", {"rpm": 0, "dir": 0}
            )
        elif command == "calm":
            await self._apply_scene(_CALM_SCENE)
        elif command == "wild":
            await self._apply_scene(_WILD_SCENE)

    async def _apply_off(self):
        await self._client.tool_exec(self._device, "ring_set", {"r": 0, "g": 0, "b": 0})
        await self._client.tool_exec(self._device, "stepper_set", {"rpm": 0, "dir": 0})

    async def _apply_scene(self, scene):
        for call in render_scene(scene):
            params = {k: v for k, v in call.items() if k != "tool"}
            await self._client.tool_exec(self._device, call["tool"], params)
