# Research: WireClaw paths for driving a WS2812B ring + 28BYJ-48

**Ticket:** #3 — Research: WireClaw paths for driving a WS2812B ring + 28BYJ-48
**Status:** Resolved **Date:** 2026-08-14

## Recommendation

**Extend the WireClaw firmware** with two new device types — a WS2812B ring
(driven via the ESP32 **RMT** peripheral) and a stepper (4-phase GPIO
sequencing). This is the only path that meets the realtime timing requirements.
The user is willing to write firmware, so this is on the table.

## What WireClaw can and cannot do today (from source)

WireClaw's device registry (`src/devices.cpp`) supports these actuator kinds
only:

- `digital_out` — single GPIO write
- `relay` — single GPIO write
- `pwm` — LEDC PWM on a pin
- `rgb_led` — the **single onboard** WS2812B LED (via `led(r,g,b)`)

There is **no** WS2812B strip/ring type and **no** stepper type. The NATS HAL
(`src/nats_hal.cpp`) exposes raw `gpio.{pin}.set`, `pwm.{pin}.set`,
`adc.{pin}.read`, `uart`, `system` — one `digitalWrite` per request.

## Why the alternatives fail the timing budget

- **WS2812B** needs a ~800 kHz bit stream, ~1.25 µs per bit with ±150 ns
  tolerance, driven continuously. The NATS HAL does one `digitalWrite` per
  network request/reply — round-trip latency is milliseconds, **orders of
  magnitude too slow**. PWM can't encode the WS2812B protocol either. Only the
  **RMT peripheral** (or a tight bit-bang ISR) can do this, and that requires
  firmware code.
- **28BYJ-48 stepper** needs sequenced 4-phase stepping (half-step ~1–2 ms per
  step). Driving it via per-step NATS requests would be jittery and slow, and
  the rule engine is edge-triggered (fires once per threshold crossing), not
  suited to continuous stepping. A firmware stepper device that owns the phase
  sequence is the right shape.

## Paths compared

| Path                                                                          | Feasibility | Effort | Notes                                                                                                                                        |
| ----------------------------------------------------------------------------- | ----------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **(a) Extend WireClaw firmware** with `ws2812b_ring` + `stepper` device types | ✅          | Medium | Add `DeviceKind` entries + handlers; WS2812B via RMT, stepper via GPIO sequencing. WireClaw keeps NATS/rules; new types become rule actions. |
| **(b) NATS HAL raw GPIO/PWM**                                                 | ❌          | —      | Infeasible for WS2812B (µs timing over network); too slow/jittery for smooth stepper stepping.                                               |
| **(c) Hybrid: custom firmware module alongside WireClaw**                     | ✅          | Medium | Custom code owns RMT/stepper; WireClaw handles NATS + rules. Workable, but (a) is cleaner — one firmware, one rule surface.                  |

## Recommended path detail

Extend WireClaw (path a):

1. Add `DEV_ACTUATOR_WS2812B_RING` and `DEV_ACTUATOR_STEPPER` to the
   `DeviceKind` enum and `deviceKindName`/`kindFromString` in `src/devices.cpp`.
2. WS2812B ring: drive via the ESP-IDF **RMT** driver (or `rmt_encoder` for
   WS2812B) on a single data GPIO. Expose a `ring_set` action (e.g. 8 RGB
   values) callable from rules.
3. Stepper: a device that owns the 4 ULN2003 GPIOs and a phase sequence; expose
   a `stepper_set` action (target speed / steps) callable from rules. The rule
   engine's `condition="always"` periodic rules can drive continuous rotation at
   a speed derived from BPM.
4. Register the new types so OpenClaw's rule-rewriting can target them.

## Sources

- WireClaw repo: https://github.com/M64GitHub/WireClaw
- `src/devices.cpp` — device registry / kinds:
  https://github.com/M64GitHub/WireClaw/blob/main/src/devices.cpp
- `src/nats_hal.cpp` — NATS HAL (raw GPIO/PWM):
  https://github.com/M64GitHub/WireClaw/blob/main/src/nats_hal.cpp
- Local wireclaw skill: `C:\Users\User\.agents\skills\wireclaw`
