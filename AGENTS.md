# AGENTS.md

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues (via the `gh` CLI). See
`docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: needs-triage, needs-info, ready-for-agent, ready-for-human,
wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root. See
`docs/agents/domain.md`.

## Project (early stages)

Disco ball controller: a ring of 8 WS2812B LEDs and a 28BYJ-48 stepper motor
(the ball's rotation). The stepper revolves faster/slower with the beat; the LED
ring reacts in real time to FFT frequency bands (low / mid / high). The light
show should be improvised by WireClaw (ESP32 agent), not a fixed loop, so it
differs every run.

**Repo status:** empty (git init, no commits). No language, layout, or commands
chosen yet — update this file as soon as code lands.

## Planned architecture

```
audio in -> FFT analysis -> band levels (low/mid/high) + BPM
        -> NATS subjects -> WireClaw (ESP32) -> WS2812B ring + stepper
```

- Language for the FFT/analysis side is **undecided: Python or Node.js** (user
  explicitly left this open). Pick one when the first code is written and record
  the choice + run commands here.
- NATS is the message bus between the analysis process and WireClaw.
- Improvisation goal: push band/beat data to WireClaw and let its on-device
  rules/logic decide the show, rather than streaming a scripted sequence.

## WireClaw essentials (verified against the installed `wireclaw` skill)

- All control is NATS **request/reply**, never plain pub:
  `nats req <device>.tool_exec '{"tool":"<name>", ...params}'` — the top-level
  key is `"tool"`, not `"name"`. Response: `{"ok":true,...}` /
  `{"ok":false,...}`.
- Wrapper script exists in the skill dir (not this repo):
  `C:\Users\User\.agents\skills\wireclaw\scripts\wc.sh` (`exec`, `caps`,
  `discover`, `sub`). Copy it into this repo if used often.
- Discovery: `nats req "_ion.discover" "" --replies=0 --timeout=3s`;
  capabilities: `nats req <device>.capabilities ""`. Always run `caps` before
  assuming what a device can drive.
- NATS server must run and be reachable by both this app and the ESP32 (default
  port 4222; `WIRECLAW_NATS_URL` overrides).
- Bridge pattern: register a `nats_value` sensor on the ESP32 bound to a NATS
  subject, publish band levels/BPM to that subject, and create persistent
  on-device `rule_create` rules that react to it (rules survive reboots and
  NATS/WiFi outages).

## Constraints that shape the design

- WireClaw rules (except `condition="always"`) are **edge-triggered**: they fire
  once per threshold crossing. They suit "bass drops -> change mode" events,
  **not** per-frame LED updates or continuous stepper stepping. Real-time
  stepping/LED frames need either direct streamed tool calls or support in the
  device firmware.
- One rule = one action type; two effects on one trigger = two rules.
- `led_set` drives only the ESP32 **onboard RGB LED**. Whether WireClaw can
  drive a WS2812B strip or a 28BYJ-48 (typically via ULN2003, 4 GPIO) is
  **unverified** — check `caps`/available actuator types first; if unsupported,
  plan for custom firmware or a different driver layer.

## Open decisions (resolve and update this file)

1. Python vs Node.js for FFT/beat analysis (e.g. librosa/aubio vs web-audio/ fft
   libs) and which NATS client.
2. How the WS2812B ring and stepper are physically driven (see constraint
   above).
3. Improvisation split: how much show logic lives in WireClaw rules vs the
   analysis process.
