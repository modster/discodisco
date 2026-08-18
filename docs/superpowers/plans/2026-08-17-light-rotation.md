# Light-Only Rotation (Comet Chase) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the stepper-driven ball rotation with a BPM-tracked comet
light chase around the 8-LED WS2812B ring, so the ball is static and "rotation"
is a purely visual effect.

**Architecture:** A new firmware device type `ring_chase` owns a comet animation
(bright head + fading trail) that advances every `loop()`, reading the `bpm`
nats_value sensor for speed. The Python `render_scene` emits a `ring_chase` tool
call (color from the scene's low band, direction from the scene) instead of
`stepper_set`. The stepper firmware stays but is unused.

**Tech Stack:** C++ (ESP32-S3, PlatformIO/Arduino, ESP-IDF RMT), Python 3.13
(nats-py), pytest.

## Global Constraints

- Firmware target: ESP32-S3 super mini, GPIO 0-15 only. Ring data on GPIO4.
- Safety clamps stay in firmware: `DISCO_RING_MAX_BRIGHT`,
  `DISCO_STEPPER_MAX_RPM`, `DISCO_STEPPER_SLEW`.
- The `bpm` nats_value sensor already exists on the device (provisioned).
- Python tests run with `.venv\Scripts\python -m pytest`.
- Firmware builds with `.venv\Scripts\python -m platformio run -e esp32-s3` from
  `firmware/wireclaw/`.
- TDD: write the failing test first, watch it fail, then implement.

---

### Task 1: Firmware — `ring_chase` driver

**Files:**

- Create: `firmware/wireclaw/include/disco_chase.h`
- Create: `firmware/wireclaw/src/disco_chase.cpp`
- Modify: `firmware/wireclaw/include/devices.h` (add `DEV_ACTUATOR_RING_CHASE`
  to enum)
- Modify: `firmware/wireclaw/src/devices.cpp` (kind name, kindFromString,
  deviceSetActuator case, auto-register)
- Modify: `firmware/wireclaw/src/tools.cpp` (tool schema, handler, dispatch)
- Modify: `firmware/wireclaw/src/main.cpp` (init + poll)

**Interfaces:**

- Produces: `discoChaseInit()`,
  `discoChaseSet(uint32_t color, int8_t direction)`, `discoChasePoll(float bpm)`
  — declared in `disco_chase.h`.
- Produces: `DEV_ACTUATOR_RING_CHASE` enum value; `ring_chase` tool name.

- [ ] **Step 1: Create `disco_chase.h`**

```c
#ifndef DISCO_CHASE_H
#define DISCO_CHASE_H

#include <stdint.h>
#include <stdbool.h>

#include "disco_config.h"

/* Initialize the chase state. Call once at boot. */
void discoChaseInit(void);

/* Set the comet color (0xRRGGBB) and direction (1 CW, -1 CCW, 0 stop). */
void discoChaseSet(uint32_t color, int8_t direction);

/* Advance the comet. Call from loop() each iteration. bpm drives the speed. */
void discoChasePoll(float bpm);

#endif /* DISCO_CHASE_H */
```

- [ ] **Step 2: Create `disco_chase.cpp`**

```c
#include "disco_chase.h"

#include <Arduino.h>
#include <math.h>

#include "disco_ring.h"

static uint32_t s_color = 0xFF0000;
static int8_t s_direction = 1;
static float s_pos = 0.0f;
static unsigned long s_last_ms = 0;

void discoChaseInit(void) {
    s_last_ms = millis();
}

void discoChaseSet(uint32_t color, int8_t direction) {
    s_color = color;
    s_direction = (direction > 0) ? 1 : (direction < 0) ? -1 : 0;
}

void discoChasePoll(float bpm) {
    unsigned long now = millis();
    float dt = (float)(now - s_last_ms) / 1000.0f;
    if (dt <= 0.0f) dt = 0.001f;
    s_last_ms = now;

    if (s_direction == 0) {
        discoRingFill(0, 0, 0);
        discoRingShow();
        return;
    }

    /* Speed: LEDs/sec from BPM (120 BPM -> 4 LEDs/sec, 60 BPM -> 2). */
    float speed = (bpm > 0.0f) ? (bpm / 30.0f) : 2.0f;
    s_pos += speed * dt * s_direction;

    /* Wrap position into [0, 8). */
    s_pos = fmodf(s_pos, (float)DISCO_RING_LEDS);
    if (s_pos < 0.0f) s_pos += (float)DISCO_RING_LEDS;

    uint8_t r = (s_color >> 16) & 0xFF;
    uint8_t g = (s_color >> 8) & 0xFF;
    uint8_t b = s_color & 0xFF;

    /* Head at s_pos, fading trail of 3 LEDs behind it. */
    const float trail_len = 3.0f;
    for (int i = 0; i < DISCO_RING_LEDS; i++) {
        float behind = fmodf(s_pos - (float)i, (float)DISCO_RING_LEDS);
        if (behind < 0.0f) behind += (float)DISCO_RING_LEDS;
        float brightness = (behind < trail_len) ? (1.0f - behind / trail_len) : 0.0f;
        discoRingSetPixel((uint8_t)i,
                          (uint8_t)(r * brightness),
                          (uint8_t)(g * brightness),
                          (uint8_t)(b * brightness));
    }
    discoRingShow();
}
```

- [ ] **Step 3: Add `DEV_ACTUATOR_RING_CHASE` to the enum in `devices.h`**

In `firmware/wireclaw/include/devices.h`, after `DEV_ACTUATOR_STEPPER`:

```c
    DEV_ACTUATOR_STEPPER,       /* disco: 28BYJ-48 stepper (4-phase) */
    DEV_ACTUATOR_RING_CHASE,    /* disco: comet chase on the LED ring */
};
```

- [ ] **Step 4: Wire the new kind into `devices.cpp`**

In `deviceKindName`, add a case:

```c
case DEV_ACTUATOR_RING_CHASE:    return "ring_chase";
```

In `kindFromString`, add:

```c
if (strcmp(s, "ring_chase") == 0) return DEV_ACTUATOR_RING_CHASE;
```

In `deviceSetActuator`, add a case (value packs 0xRRGGBB; direction defaults
CW):

```c
case DEV_ACTUATOR_RING_CHASE:
    discoChaseSet((uint32_t)value, 1);
    return true;
```

Add the include at the top of `devices.cpp`:

```c
#include "disco_chase.h"
```

Auto-register the device in both `devicesInit` and `devicesReload` (after the
`stepper` block):

```c
if (!deviceFind("ring_chase")) {
    deviceRegister("ring_chase", DEV_ACTUATOR_RING_CHASE, DISCO_RING_PIN, "", false);
    changed = true;
}
```

- [ ] **Step 5: Add the `ring_chase` tool to `tools.cpp`**

Add the include:

```c
#include "disco_chase.h"
```

Add the tool schema after the `stepper_set` schema:

```c
{"type":"function","function":{"name":"ring_chase","description":"Start a comet chase around the 8-LED ring. color: 0xRRGGBB, dir: 1=CW, -1=CCW, 0=stop. Speed tracks BPM.","parameters":{"type":"object","properties":{"color":{"type":"integer"},"dir":{"type":"integer"}},"required":["color"]}}},
```

Add the handler after `tool_stepper_set`:

```c
static void tool_ring_chase(const char *args, char *result, int result_len) {
    int color = jsonArgInt(args, "color", 0xFF0000);
    int dir = jsonArgInt(args, "dir", 1);
    if (dir > 1) dir = 1;
    if (dir < -1) dir = -1;
    discoChaseSet((uint32_t)color, (int8_t)dir);
    snprintf(result, result_len, "Chase set color=0x%06X dir=%d", color, dir);
}
```

Add the dispatch in `toolExecute`:

```c
} else if (strcmp(name, "ring_chase") == 0) {
    tool_ring_chase(args_json, result, result_len);
}
```

- [ ] **Step 6: Wire init + poll into `main.cpp`**

Add the include:

```c
#include "disco_chase.h"
```

In `setup()`, after `discoStepperInit();`:

```c
discoChaseInit();
```

In `loop()`, after `discoStepperPoll();`, read the bpm sensor and poll the
chase:

```c
float bpm = 0.0f;
Device *bpm_dev = deviceFind("bpm");
if (bpm_dev) bpm = deviceReadSensor(bpm_dev);
discoChasePoll(bpm);
```

- [ ] **Step 7: Build the firmware**

Run from `firmware/wireclaw/`:

```bash
C:\Users\User\discodisco\.venv\Scripts\python -m platformio run -e esp32-s3
```

Expected: `SUCCESS`. Fix any compile errors.

- [ ] **Step 8: Commit**

```bash
git add firmware/wireclaw/include/disco_chase.h firmware/wireclaw/src/disco_chase.cpp firmware/wireclaw/include/devices.h firmware/wireclaw/src/devices.cpp firmware/wireclaw/src/tools.cpp firmware/wireclaw/src/main.cpp
git commit -m "feat(firmware): add ring_chase comet driver"
```

---

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

### Task 3: Docs — spec + glossary

**Files:**

- Modify: `docs/spec.md`
- Modify: `CONTEXT.md`

- [ ] **Step 1: Update `docs/spec.md`**

In §1 Architecture, change the stepper line to reflect a static ball with a
comet chase. In §5 Mapping laws, replace the "BPM → stepper" law with a "BPM →
chase speed" law. In §8 build order step 6, note the light-rotation change.

- [ ] **Step 2: Update `CONTEXT.md`**

Add a term for the comet chase:

```markdown
**Comet chase**: The light-only rotation effect — a bright head LED with a
fading trail that chases around the LED ring, driven by BPM. Replaces the
stepper for rotation. _Avoid_: spinner, rotator
```

- [ ] **Step 3: Commit**

```bash
git add docs/spec.md CONTEXT.md
git commit -m "docs: document light-only rotation (comet chase)"
```
