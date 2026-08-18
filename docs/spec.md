# Disco Ball Controller — Locked Spec

The destination of the wayfinder map (issue #1). This spec is the agreed design
for a disco ball controller: a Python **analysis process** on a PC captures
system loopback audio, computes **band levels** and **BPM**, and publishes them
to NATS; an ESP32 **controller** running extended WireClaw firmware drives an
8-LED WS2812B **LED ring** with a light-only **comet chase** (a bright head LED
with a fading trail); OpenClaw improvises the **show** by live
**rule-rewriting**, so no two runs match.

Decisions are recorded on the map's tickets (#2–#8) and in `docs/research/`.
This document is the assembled whole.

---

## 1. Architecture

```
system audio (WASAPI loopback)
        │
        ▼
┌─────────────────────────────┐
│  Analysis process (Python)  │  PC
│  PyAudioWPatch capture       │
│  NumPy FFT → band levels     │
│  aubio-ledfx → beat + BPM    │
│  musical-event detection     │
└──────────────┬──────────────┘
               │  NATS (local nats-server)
               ▼
┌─────────────────────────────┐
│  Controller (ESP32-S3)      │  WireClaw firmware (extended)
│  nats_value sensors          │
│  rule engine (offline)       │
│  ring_chase (RMT comet)      │
└────────────┬─────────────────┘
             │
             ▼
        LED ring
        (8× WS2812B)
        comet chase around the ring
```

- **Analysis process** runs on the PC, publishes to NATS.
- **Controller** runs the show in realtime from NATS-fed values; the rule loop
  runs 24/7 with no LLM and no network.
- **OpenClaw** (on the PC) subscribes to musical events and improvises by
  swapping scenes via WireClaw `tool_exec`.

## 2. Component choices

| Concern            | Choice                                                                                         | Source |
| ------------------ | ---------------------------------------------------------------------------------------------- | ------ |
| Loopback capture   | **PyAudioWPatch** (WASAPI loopback, wheels for Py3.13)                                         | #2     |
| Beat/BPM detection | **`aubio-ledfx`** (maintained aubio fork)                                                      | #4     |
| FFT band levels    | NumPy FFT (low/mid/high)                                                                       | #4     |
| Controller board   | **ESP32-S3** (8 RMT channels, dual-core)                                                       | #5     |
| Actuator path      | **Extend WireClaw firmware** with `ws2812b_ring` (RMT) + `stepper` (4-phase GPIO) device types | #3     |
| Message bus        | NATS (local `nats-server` v2.10.25)                                                            | —      |
| Improvising agent  | OpenClaw (installed, `openclaw@2026.7.1-2`)                                                    | —      |

## 3. NATS subject schema

All under the `disco.` namespace. Continuous values are **plain numeric
strings**; events are **JSON**. Plain pub/sub, no persistence.

| Subject           | Payload                                                     | Type           | Publish rate  |
| ----------------- | ----------------------------------------------------------- | -------------- | ------------- |
| `disco.band.low`  | `0.0`–`1.0`                                                 | numeric string | ~20–30 Hz     |
| `disco.band.mid`  | `0.0`–`1.0`                                                 | numeric string | ~20–30 Hz     |
| `disco.band.high` | `0.0`–`1.0`                                                 | numeric string | ~20–30 Hz     |
| `disco.bpm`       | e.g. `128.0`                                                | numeric string | ~1 Hz         |
| `disco.beat`      | `{"ts":<epoch_ms>,"bpm":<float>}`                           | JSON           | on each beat  |
| `disco.event`     | `{"type":"song_change"\|"drop"\|"silence","ts":<epoch_ms>}` | JSON           | on occurrence |

**WireClaw sensor mapping:** one `nats_value` sensor per continuous subject —
`band_low` ← `disco.band.low`, `band_mid` ← `disco.band.mid`, `band_high` ←
`disco.band.high`, `bpm` ← `disco.bpm`. Rules read these directly. The JSON
events (`disco.beat`, `disco.event`) are consumed by OpenClaw, not by
`nats_value` sensors.

**Provisioning:** `python scripts/disco_provision.py <device>` registers the
four sensors on the controller (idempotent; `--discover` lists devices; `--demo`
adds a bass-drop demo rule).

**OpenClaw control:** OpenClaw pushes scene changes via the existing WireClaw
`tool_exec` (rule_create / ring_chase) over NATS — no new control subject. It
subscribes to `disco.event` to pick a new scene.

## 4. Improv design

- **Scene** = a named bundle of rules + parameters: band→ring mapping,
  chase→speed mapping, active patterns, beat-event thresholds.
- OpenClaw owns a **palette of scenes** (seed palette + invents new ones) and
  swaps the **active scene on musical events** (song change, drop, silence).
- The controller runs the scene's rules in realtime between interventions.
- **Randomness is LLM-only** — OpenClaw picks/invents scenes; the controller
  executes deterministically.
- **Fully autonomous** during a show, with reserved commands ('stop', 'off',
  'calm', 'wild') via OpenClaw chat for human steering.
- **Transitions are abrupt** — scene change replaces the rule set immediately.
- **Failure mode:** if OpenClaw is down/slow at a musical event, the controller
  keeps running the current scene; the next event retries.

## 5. Mapping laws

**Fixed laws (firmware, not scene-settable):**

- LED group assignment: low→LEDs 0–2, mid→3–5, high→6–7.
- Safety clamps: max brightness, max chase speed, max slew (acceleration),
  thermal shutdown. Enforced at the device-type level (`ring_chase` clamps its
  input).

**Scene-rewritable parameters:**

- Per-band colors (low/mid/high).
- Brightness curve per band (how brightness tracks band level, e.g. linear or
  sqrt), clamped by firmware max.
- BPM→chase speed endpoints (the linear map's slow/fast endpoints), clamped by
  the firmware max.
- Direction: CW, CCW, or oscillate.
- Beat-flash params + threshold (color, which LEDs, duration, threshold).

**The laws:**

- **BPM → chase speed:** linear map from BPM to chase speed (LEDs per second),
  endpoints scene-settable, clamped by firmware max. The comet head chases
  around the ring at the current BPM-derived speed; BPM updates smoothly change
  speed (with slew limiting).
- **Direction:** scene-settable (CW / CCW / oscillate); the comet head follows
  it and the trail fades behind it.
- **Band levels → LED ring:** fixed LED groups; each band's brightness tracks
  its band level via the scene's curve, clamped by firmware max.
- **Beat events → LEDs:** a scene-defined beat flash fires on each beat, layered
  on top of the level-tracking brightness.

## 6. Pinout and wiring

### 6.1 Controller pin assignment (ESP32-S3 super mini)

> **Super-mini constraint:** the ESP32-S3 and ESP32-C3 super-mini boards expose
> only **GPIO 0–15**. Pins are chosen within that range, avoiding strapping pins
> and flash pins. On the S3 Super Mini, **IO10 is the flash chip-select
> (FSPICS0) and cannot be used as GPIO** — so the stepper uses IO8 instead. Pins
> are configurable in `firmware/wireclaw/include/disco_config.h`.

| Signal       | Pin      | Notes                 |
| ------------ | -------- | --------------------- |
| WS2812B data | GPIO4    | RMT channel           |
| Stepper IN1  | GPIO5    | ULN2003 input 1       |
| Stepper IN2  | GPIO6    | ULN2003 input 2       |
| Stepper IN3  | GPIO7    | ULN2003 input 3       |
| Stepper IN4  | GPIO8    | ULN2003 input 4       |
| 5V in        | 5V / VIN | from shared 5V supply |
| GND          | GND      | common ground         |

> Pin numbers are configurable in `disco_config.h`; confirm against the specific
> board and the WireClaw firmware's GPIO configuration before wiring.

### 6.2 WS2812B ring wiring

WS2812B is a 5V-logic device; the ESP32-S3 is 3.3V-logic. A **level shifter** is
required on the data line.

```
ESP32-S3 GPIO4 ──► 74AHCT125 (level shifter) ──► 330Ω ──► WS2812B DIN
                                                          │
                                                          ▼
                                                     WS2812B ring
                                                     5V ──► +5V
                                                     GND ──► GND
```

- **Level shifter:** 74AHCT125 (or 74HCT125) — 3.3V in, 5V out, fast enough for
  the ~800 kHz WS2812B signal. (A 74AHCT125 is the common choice; a 74LVC245
  also works.)
- **Series resistor:** 330Ω on the data line between the shifter and the ring's
  DIN, to damp ringing and protect the first LED.
- **Bulk capacitance:** a **1000 µF electrolytic capacitor** across the 5V/GND
  at the ring's power input, to absorb current spikes when LEDs switch. Add a
  **0.1 µF ceramic** close to the ring's power pins.
- **Power:** the ring draws up to 8 × 60 mA = 480 mA at full white. The 5V
  supply must handle the ring + the ULN2003/stepper together (see power budget).

### 6.3 Stepper wiring (28BYJ-48 + ULN2003)

The 28BYJ-48 is a 5V unipolar stepper driven by the ULN2003 driver board.

```
ESP32-S3 GPIO5 ──► ULN2003 IN1
ESP32-S3 GPIO6 ──► ULN2003 IN2
ESP32-S3 GPIO7 ──► ULN2003 IN3
ESP32-S3 GPIO8 ──► ULN2003 IN4
ULN2003 + ────────► +5V
ULN2003 GND ──────► GND
ULN2003 motor ────► 28BYJ-48 (5-wire connector)
```

> **Note:** GPIO4 is the WS2812B ring data line — do not use it for the stepper.
> Stepper pins (IN1–IN4) are GPIO5/6/7/8 per `disco_config.h`.

- The ULN2003 board has its own onboard resistors and the motor connector; wire
  the four control inputs from the ESP32 and power from the shared 5V rail.
- **Flyback protection** is built into the ULN2003 (Darlington array with clamp
  diodes) — no external diodes needed.
- **Power:** the 28BYJ-48 draws ~150–250 mA when stepping. The ULN2003 board
  should be powered from the same 5V rail as the ring.

### 6.4 Power budget

| Load                              | Typical current      |
| --------------------------------- | -------------------- |
| WS2812B ring (8 LEDs, full white) | ~480 mA              |
| 28BYJ-48 stepper (stepping)       | ~150–250 mA          |
| ESP32-S3                          | ~80–250 mA (WiFi on) |
| **Total**                         | **~0.7–1.0 A**       |

- Use a **5V supply rated ≥ 2 A** to leave headroom for LED spikes and WiFi
  bursts.
- **Common ground** between the ESP32, the ring, and the ULN2003 is mandatory.
- If the ESP32-S3 dev board is powered over USB, do **not** draw the ring +
  stepper from the USB 5V — power them from the external 5V supply and share
  ground.

## 7. Open items (fog)

- Whether OpenClaw also **DJs** — reacting to song changes vs pure pattern
  improv.
- Show safety rails detail: exact max brightness / motor duty / temperature
  values (to be set during firmware bring-up).
- Behaviour when the PC or NATS drops mid-show (the rule loop keeps the current
  scene; exact fallback to be confirmed in firmware).
- Testing the show without music playing (test tones / recorded loopback / a
  simulator subject).

## 8. Build order (suggested)

1. **Firmware:** extend WireClaw with `ws2812b_ring` (RMT) + `stepper` device
   types and the safety clamps. Bring up on the ESP32-S3.
2. **Analysis process:** PyAudioWPatch capture → NumPy FFT band levels →
   aubio-ledfx beat/BPM → musical-event detection → publish to NATS.
3. **NATS schema:** register the `nats_value` sensors; verify subjects flow.
4. **Scenes:** seed palette; OpenClaw scene-swap on `disco.event`.
   - Implemented: `analysis/scenes.py` (Scene model + seed palette `pulse` /
     `calm` / `rage` + `render_scene` + `SceneController`),
     `analysis/scenerunner.py` (`SceneRunner` — subscribes to `disco.event` and
     applies scenes via `tool_exec`). Wired into `main.py --device`.
5. **Wiring:** assemble per §6; verify power budget and level shifter.
6. **Improv:** OpenClaw rule-rewriting; reserved commands; safety rails.
   - **Light-rotation change:** rotation is now the light-only **comet chase** —
     `render_scene` drives a single `ring_chase` (color from the scene's low
     band, direction from the scene) instead of a stepper, so the ball stays
     static.
   - Implemented: `analysis/commands.py` (`CommandController` — reserved
     commands `stop`/`off`/`calm`/`wild` via `disco.command`),
     `analysis/improv.py` (`ImprovAgent` + `OpenClawPicker` — LLM scene choice
     on `disco.event`). Wired into `main.py --device [--improv]`.
