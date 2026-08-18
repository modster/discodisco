import pytest

from analysis.scenes import Scene, SEED_PALETTE, render_scene


def test_seed_palette_has_named_scenes():
    assert len(SEED_PALETTE) >= 3
    assert all(isinstance(s, Scene) for s in SEED_PALETTE)
    assert all(s.name for s in SEED_PALETTE)


def test_scene_has_required_fields():
    s = Scene(
        name="pulse",
        band_colors={"low": (255, 0, 0), "mid": (0, 255, 0), "high": (0, 0, 255)},
        bpm_endpoints={"slow_bpm": 60, "fast_bpm": 180, "slow_rpm": 1, "fast_rpm": 8},
        direction="cw",
        beat_flash={"color": (255, 255, 255), "threshold": 0.5, "duration_ms": 200},
    )
    assert s.name == "pulse"
    assert s.direction == "cw"
    assert s.bpm_endpoints["fast_rpm"] == 8


def test_render_scene_produces_ring_chase():
    s = SEED_PALETTE[0]
    calls = render_scene(s)
    tools = [c["tool"] for c in calls]
    assert "ring_chase" in tools
    assert "stepper_set" not in tools


def test_render_scene_ring_chase_has_color_and_dir():
    s = Scene(
        name="test",
        band_colors={"low": (255, 0, 0), "mid": (0, 255, 0), "high": (0, 0, 255)},
        bpm_endpoints={"slow_bpm": 60, "fast_bpm": 180, "slow_rpm": 1, "fast_rpm": 8},
        direction="ccw",
        beat_flash={"color": (255, 255, 255), "threshold": 0.5, "duration_ms": 200},
    )
    calls = render_scene(s)
    chase = next(c for c in calls if c["tool"] == "ring_chase")
    # color comes from the low band
    assert chase["color"] == 0xFF0000
    # direction follows the scene
    assert chase["dir"] == -1
    # BPM->speed endpoints come from the scene's bpm_endpoints
    assert chase["slow_bpm"] == s.bpm_endpoints["slow_bpm"]
    assert chase["fast_bpm"] == s.bpm_endpoints["fast_bpm"]
    assert chase["slow_speed"] == s.bpm_endpoints["slow_rpm"]
    assert chase["fast_speed"] == s.bpm_endpoints["fast_rpm"]


def test_palette_scenes_are_distinct():
    names = {s.name for s in SEED_PALETTE}
    assert len(names) == len(SEED_PALETTE)
