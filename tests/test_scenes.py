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


def test_render_scene_produces_ring_and_stepper_calls():
    s = SEED_PALETTE[0]
    calls = render_scene(s)
    tools = [c["tool"] for c in calls]
    # a scene must control the ring and the stepper
    assert "ring_set" in tools
    assert "stepper_set" in tools


def test_render_scene_ring_set_has_color():
    s = SEED_PALETTE[0]
    calls = render_scene(s)
    ring = next(c for c in calls if c["tool"] == "ring_set")
    assert "r" in ring and "g" in ring and "b" in ring
    assert all(0 <= v <= 255 for v in (ring["r"], ring["g"], ring["b"]))


def test_render_scene_stepper_set_has_rpm_and_dir():
    s = SEED_PALETTE[0]
    calls = render_scene(s)
    stepper = next(c for c in calls if c["tool"] == "stepper_set")
    assert "rpm" in stepper
    assert stepper["rpm"] >= 0
    assert stepper["dir"] in (1, -1, 0)


def test_palette_scenes_are_distinct():
    names = {s.name for s in SEED_PALETTE}
    assert len(names) == len(SEED_PALETTE)
