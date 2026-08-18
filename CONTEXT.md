# Disco Ball Controller

A disco ball device: an ESP32 drives an 8-LED WS2812B ring and a 28BYJ-48
stepper (the ball's rotation), reacting in real time to music captured on a PC,
with the performance improvised so no two runs match.

## Language

**Show**: The real-time light-and-motion performance the device produces while
music plays. Improvised, never identical between runs. _Avoid_: animation,
sequence, loop

**Band levels**: Real-time magnitudes of three FFT frequency ranges — low, mid,
high — computed from the captured audio stream. _Avoid_: channels, EQ bands

**Beat**: A detected musical pulse event; its tracked rate (BPM) drives the
stepper's rotation speed. _Avoid_: onset, kick

**Analysis process**: The Python program on the PC that captures system loopback
audio, computes band levels and BPM, and publishes them to NATS. _Avoid_:
server, backend

**Controller**: The ESP32 running WireClaw firmware. Owns the LED ring and
stepper; reacts to NATS-fed values through its on-device rule engine. _Avoid_:
device, board

**Rule-rewriting**: OpenClaw's live improvisation mechanism: during a show it
periodically creates and modifies rules on the controller so the show evolves.
_Avoid_: scripting, programming the show

**Scene**: A named bundle of rules and parameters — band→ring mapping,
beat→stepper mapping, active patterns, and beat-event thresholds — that the
controller runs as a unit. OpenClaw owns the palette of scenes and improvises by
swapping the active scene. _Avoid_: mode, preset, effect

**Scene palette**: The set of named scenes the improvisation engine draws from.
A seed palette ships with the system; OpenClaw can invent new scenes and reuse
or evolve existing ones. _Avoid_: preset list, effect bank

**Reserved command**: A human-steering word that overrides the autonomous improv
— `stop`, `off`, `calm`, `wild`. Only these words affect the show; anything else
is ignored. _Avoid_: voice command, hotkey

**Improv agent**: The OpenClaw layer that improvises the show live. On each
musical event it asks the LLM to choose a scene, then applies it to the
controller, so no two runs match. _Avoid_: DJ, autopilot

**Musical event**: A structural change in the music — song change, drop, or
silence — detected by the analysis process and published to NATS. OpenClaw
reacts to musical events by choosing a new scene. _Avoid_: trigger, cue

**Safety clamp**: A hard limit enforced in firmware — max brightness, max motor
speed/duty, and thermal shutdown — that no rule or scene can exceed. _Avoid_:
limit, cap

**Mapping law**: A rule that turns music into hardware output. Fixed laws are
hardcoded in firmware (LED group assignment, safety clamps); rewritable laws are
parameters a scene sets (colors, brightness curve, BPM→RPM endpoints, direction,
beat flash). _Avoid_: mapping, transform

**Beat flash**: A brief, scene-defined LED flash fired on each beat, layered on
top of the continuous level-tracking brightness. _Avoid_: strobe, pulse

**NATS subject**: A named channel on the NATS bus carrying one signal — a band
level, BPM, a beat event, or a musical event. Continuous values are plain
numeric strings; events are JSON. _Avoid_: topic, channel

**LED ring**: The ring of 8 WS2812B addressable RGB LEDs mounted on the disco
ball.

**Stepper**: The 28BYJ-48 stepper motor (driven via a ULN2003 board) that
rotates the disco ball.
