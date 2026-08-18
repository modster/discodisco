from dataclasses import dataclass, field


@dataclass
class Scene:
    """A named bundle of show parameters.

    A scene defines how the LED ring and stepper should behave for a stretch of
    the show. OpenClaw owns the palette and swaps the active scene on musical
    events. All values are safe defaults; the firmware's safety clamps are the
    final authority regardless of what a scene requests.
    """

    name: str
    band_colors: dict = field(
        default_factory=lambda: {
            "low": (255, 0, 0),
            "mid": (0, 255, 0),
            "high": (0, 0, 255),
        }
    )
    bpm_endpoints: dict = field(
        default_factory=lambda: {
            "slow_bpm": 60,
            "fast_bpm": 180,
            "slow_rpm": 1,
            "fast_rpm": 8,
        }
    )
    direction: str = "cw"  # cw | ccw | oscillate
    beat_flash: dict = field(
        default_factory=lambda: {
            "color": (255, 255, 255),
            "threshold": 0.5,
            "duration_ms": 200,
        }
    )


SEED_PALETTE = [
    Scene(
        name="pulse",
        band_colors={"low": (255, 40, 0), "mid": (255, 180, 0), "high": (0, 200, 255)},
        bpm_endpoints={"slow_bpm": 60, "fast_bpm": 180, "slow_rpm": 2, "fast_rpm": 10},
        direction="cw",
        beat_flash={"color": (255, 255, 255), "threshold": 0.6, "duration_ms": 180},
    ),
    Scene(
        name="calm",
        band_colors={
            "low": (0, 60, 120),
            "mid": (40, 160, 220),
            "high": (200, 220, 255),
        },
        bpm_endpoints={"slow_bpm": 60, "fast_bpm": 150, "slow_rpm": 1, "fast_rpm": 4},
        direction="oscillate",
        beat_flash={"color": (255, 255, 255), "threshold": 0.9, "duration_ms": 120},
    ),
    Scene(
        name="rage",
        band_colors={"low": (255, 0, 0), "mid": (255, 60, 0), "high": (255, 255, 0)},
        bpm_endpoints={"slow_bpm": 60, "fast_bpm": 180, "slow_rpm": 6, "fast_rpm": 15},
        direction="ccw",
        beat_flash={"color": (255, 255, 255), "threshold": 0.4, "duration_ms": 220},
    ),
]

_DIR_MAP = {"cw": 1, "ccw": -1, "oscillate": 0}

# map a musical event type to a preferred scene mood
_EVENT_MOOD = {"song_change": "pulse", "drop": "rage", "silence": "calm"}


def _pack(rgb):
    r, g, b = rgb
    return (r << 16) | (g << 8) | b


def render_scene(scene):
    """Turn a scene into the tool_exec calls needed to apply it.

    Returns a list of flat tool_request dicts, one per actuator, that OpenClaw
    (or the SceneController) sends to the controller. The ring is driven by a
    single comet chase whose color comes from the scene's low band and whose
    direction follows the scene. The chase is the sole ring driver.
    """
    rpm = scene.bpm_endpoints["fast_rpm"]
    return [
        {
            "tool": "ring_chase",
            "color": _pack(scene.band_colors["low"]),
            "dir": _DIR_MAP.get(scene.direction, 1),
        },
    ]


class SceneController:
    """Swaps the active scene on musical events and applies it to the device.

    This is the autonomous improvisation engine. It subscribes to musical
    events (song_change / drop / silence), picks a scene from the palette, and
    pushes the scene's tool_exec calls to the controller. If a preferred scene
    for the event isn't in the palette, it falls back to the next available one.
    """

    def __init__(self, client, device, palette):
        self._client = client
        self._device = device
        self._palette = palette
        self._by_name = {s.name: s for s in palette}
        self.current_scene = None

    async def handle_event(self, event_type):
        preferred = _EVENT_MOOD.get(event_type)
        scene = self._by_name.get(preferred) or self._palette[0]
        self.current_scene = scene.name
        for call in render_scene(scene):
            params = {k: v for k, v in call.items() if k != "tool"}
            await self._client.tool_exec(self._device, call["tool"], params)
