# Final Fix Report — Scene-settable chase speed endpoints + firmware clamp

## What changed

Closed the spec-vs-implementation gap in `docs/spec.md` §5: the comet chase's
BPM→speed mapping is now scene-settable, clamped by a firmware max, and
slew-limited. Previously the firmware hardcoded `speed = bpm/30.0` with no clamp
or slew, and `render_scene` computed a dead `rpm` variable that was never used.

### Firmware

- **`firmware/wireclaw/include/disco_config.h`** — added chase safety clamps:
  `DISCO_CHASE_MAX_SPEED 8.0f` (max chase speed, LEDs/sec) and
  `DISCO_CHASE_SLEW 4.0f` (max speed change per second).
- **`firmware/wireclaw/include/disco_chase.h`** — `discoChaseSet` now accepts
  the BPM→speed endpoints:
  `(color, direction, slow_bpm, fast_bpm, slow_speed,
  fast_speed)`.
- **`firmware/wireclaw/src/disco_chase.cpp`** — added static endpoint state and
  a slew-limited `s_current_speed`. `discoChaseSet` stores the endpoints,
  clamping slow/fast speed to `DISCO_CHASE_MAX_SPEED`. `discoChasePoll` now
  linearly interpolates BPM between `(slow_bpm -> slow_speed)` and
  `(fast_bpm ->
  fast_speed)`, clamps to `[0, DISCO_CHASE_MAX_SPEED]`,
  slew-limits `s_current_speed` toward the target using `DISCO_CHASE_SLEW * dt`,
  and uses `s_current_speed` for the step advance. The direction-aware trail
  logic was left unchanged.
- **`firmware/wireclaw/src/tools.cpp`** — `ring_chase` tool schema now accepts
  optional `slow_bpm`, `fast_bpm`, `slow_speed`, `fast_speed` (defaults 60, 180,
  2, 8). `tool_ring_chase` reads them and passes them to `discoChaseSet`.
- **`firmware/wireclaw/src/devices.cpp`** — the `DEV_ACTUATOR_RING_CHASE` rule
  action path now calls `discoChaseSet((uint32_t)value, 1, 60, 180, 2, 8)`.

### Python

- **`analysis/scenes.py`** — `render_scene` now reads the scene's
  `bpm_endpoints` and passes `slow_bpm`/`fast_bpm`/`slow_speed`/`fast_speed` to
  the `ring_chase` call (interpreting `slow_rpm`/`fast_rpm` as chase speeds in
  LEDs/sec). Removed the dead `rpm` variable.

### Tests

- **`tests/test_scenes.py`** — `test_render_scene_ring_chase_has_color_and_dir`
  now also asserts the `slow_bpm`/`fast_bpm`/`slow_speed`/`fast_speed` keys are
  present and match the scene's `bpm_endpoints`.

## Build result

`platformio run -e esp32-s3` from `firmware/wireclaw/` → **SUCCESS** (67s). RAM
60.9%, Flash 47.4%.

## Test result

`.\.venv\Scripts\python -m pytest -q` from repo root → **55 passed**.

## Files changed

- `firmware/wireclaw/include/disco_config.h`
- `firmware/wireclaw/include/disco_chase.h`
- `firmware/wireclaw/src/disco_chase.cpp`
- `firmware/wireclaw/src/tools.cpp`
- `firmware/wireclaw/src/devices.cpp`
- `analysis/scenes.py`
- `tests/test_scenes.py`
