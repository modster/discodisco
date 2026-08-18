### Task 2: Python — `render_scene` emits `ring_chase`

**Files:**

- Modify: `analysis/scenes.py` (`render_scene`)
- Modify: `tests/test_scenes.py`
- Modify: `tests/test_improv.py`

**Interfaces:**

- Consumes: `Scene` dataclass (`band_colors`, `direction`), `_DIR_MAP`, `_pack`.
- Produces: `render_scene(scene)` returns
  `[{"tool":"ring_chase","color":int,"dir":int}]`.

- [ ] **Step 1: Write the failing test**

In `tests/test_scenes.py`, replace `test_render_scene_ring_set_has_color` and
`test_render_scene_ring_maps_bands_to_led_groups` with:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_scenes.py -v` Expected: FAIL — `render_scene` still
returns `stepper_set`, no `ring_chase`.

- [ ] **Step 3: Update `render_scene` in `analysis/scenes.py`**

Replace the return of `render_scene`:

```python
rpm = scene.bpm_endpoints["fast_rpm"]
return [
    {"tool": "ring_chase", "color": _pack(scene.band_colors["low"]),
     "dir": _DIR_MAP.get(scene.direction, 1)},
]
```

(Remove the `leds`/`ring_set` and `stepper_set` construction; the comet is the
sole ring driver.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_scenes.py -v` Expected: PASS.

- [ ] **Step 5: Update `tests/test_improv.py`**

In `test_agent_applies_picked_scene_on_event`, the ring assertion now checks the
chase color. Replace:

```python
ring = next(t for _, t in nc.tool_calls if t.get("tool") == "ring_set")
assert ring["leds"][0] == (10 << 16) | (20 << 8) | 30
```

with:

```python
chase = next(t for _, t in nc.tool_calls if t.get("tool") == "ring_chase")
assert chase["color"] == (10 << 16) | (20 << 8) | 30
```

- [ ] **Step 6: Run the full Python suite**

Run: `pytest -q` Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add analysis/scenes.py tests/test_scenes.py tests/test_improv.py
git commit -m "feat(analysis): render_scene emits ring_chase instead of stepper_set"
```

---


