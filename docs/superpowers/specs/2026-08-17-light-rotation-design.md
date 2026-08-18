# Light-Only Rotation (Comet Chase) — Design

**Date:** 2026-08-17 **Status:** Approved

## Problem

The disco ball currently rotates via a 28BYJ-48 stepper motor. The user wants to
drop the motor entirely and get the same "rotation" by chasing a light pattern
around the 8-LED WS2812B ring. The ball becomes static; rotation is a purely
visual effect.

## Design

### Concept

A **comet** — one bright "head" LED with a fading trail — chases around the
8-LED ring, reading as the ball spinning. The chase speed tracks **BPM** so it
speeds up and slows down with the music, preserving the "in time with the beat"
feel the stepper provided.

### Where the chase runs

The chase must update per-frame (many times per second). WireClaw's rule engine
is edge-triggered and cannot drive per-frame animation, so the chase lives in
**firmware** as a new device type, `ring_chase`, that owns the comet animation
and advances it every `loop()`.

### Speed source

The analysis process already publishes `disco.bpm` → the `bpm` nats_value sensor
on the controller. The `ring_chase` driver reads that sensor each loop and maps
BPM → chase speed (LEDs/sec), so the comet speeds up/slows down with the music.

### Scene integration

A scene's `direction` (cw/ccw/oscillate) and `band_colors` still apply:

- The comet's color comes from the scene's **low** band color (the dominant
  visual; the head uses this color, the trail fades it toward off).
- The chase direction follows the scene's `direction`.
- `render_scene` emits a `ring_chase` call (speed from BPM, direction from
  scene) instead of `stepper_set`.

### Stepper

Keep the stepper firmware code in place but stop using it. The ball is static.
The stepper device type and driver remain for future use / reversibility.

## Changes

### Firmware

- New `ring_chase` device type + driver (`disco_chase.cpp/.h`): comet animation
  (head + fading trail), reads the `bpm` sensor for speed, advances every
  `loop()`.
- Register `ring_chase` device; add `ring_chase` tool + rule action.
- Rebuild + reflash.

### Python

- `render_scene` emits `ring_chase` (speed from BPM, direction from scene)
  instead of `stepper_set`.
- Tests updated.

### Docs

- Spec + glossary updated to reflect static ball + light rotation.

## Trade-off

The comet is a _visual_ rotation — it does not physically spin the ball. The
stepper code remains if real rotation is ever wanted again.
