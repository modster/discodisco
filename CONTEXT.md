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

**LED ring**: The ring of 8 WS2812B addressable RGB LEDs mounted on the disco
ball.

**Stepper**: The 28BYJ-48 stepper motor (driven via a ULN2003 board) that
rotates the disco ball.
