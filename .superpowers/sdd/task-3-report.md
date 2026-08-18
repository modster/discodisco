# Task 3 Report — Docs: spec + glossary

## Status

DONE

## What I changed

**`docs/spec.md`** — updated to reflect the light-only rotation (comet chase):

- Intro paragraph: replaced the 28BYJ-48 stepper with a light-only **comet
  chase** (bright head LED with a fading trail).
- §1 Architecture diagram: removed the `stepper (4-phase GPIO)` controller line
  and the Stepper box; the controller now drives `ring_chase (RMT comet)` into
  the LED ring.
- §3 OpenClaw control: `tool_exec (rule_create / ring_set / stepper_set)` →
  `tool_exec (rule_create / ring_chase)`.
- §4 Scene definition: `beat→stepper mapping` → `chase→speed mapping`.
- §5 Mapping laws:
  - Safety clamp line: `max RPM` → `max chase speed`; device-type clamp noted as
    `ring_chase`.
  - Scene-rewritable param: `BPM→RPM endpoints (within the RPM clamp)` →
    `BPM→chase speed endpoints`.
  - Replaced the **BPM → stepper** law with a **BPM → chase speed** law (linear
    BPM→speed map, LEDs/second, slew-limited, clamped by firmware max).
  - Direction law notes the comet head follows direction and trail fades behind.
- §8 build order step 6: added a note that rotation is now the light-only comet
  chase (`render_scene` drives a single `ring_chase` from the low band, not a
  stepper), so the ball stays static.

I deliberately left §6 (wiring/pinout/power budget) and build step 1 (firmware
device types) referencing the stepper unchanged: the design keeps the stepper
firmware/hardware in place but unused, so those sections remain factually
accurate.

**`CONTEXT.md`** — glossary updates:

- Intro paragraph: replaced "ring and a 28BYJ-48 stepper (the ball's rotation)"
  with "ring with a light-only comet chase (rotation)".
- Beat: BPM now drives "the comet chase's speed".
- Controller: "Owns the LED ring and its comet chase".
- Scene: `beat→stepper mapping` → `chase→speed mapping`.
- Safety clamp: `max motor speed/duty` → `max chase speed`.
- Mapping law: `BPM→RPM endpoints` → `BPM→chase speed endpoints`.
- LED ring: noted the ball is static; all rotation is the comet chase.
- Replaced the `Stepper` term with a `Comet chase` term (color from the scene's
  low band, direction follows the scene, replaces the stepper).

## Files changed

- `docs/spec.md`
- `CONTEXT.md`

## Commit

- `dec9b51` docs: document light-only rotation (comet chase)

## Consistency check

Edits were cross-checked against `analysis/scenes.py:79` (`render_scene` drives
a single `ring_chase`; color from `scene.band_colors["low"]`; `dir` from the
scene's `direction`), so the docs match the code.

## Issues / concerns

- None blocking. §6 wiring and build step 1 still reference the stepper because
  the firmware/hardware remains (unused); this is intentional and matches the
  design doc.
