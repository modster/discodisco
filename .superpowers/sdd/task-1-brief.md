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


