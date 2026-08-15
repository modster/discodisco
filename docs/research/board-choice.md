# Research: Choose the controller board — ESP32-S3 vs ESP32-C3

**Ticket:** #5 — Research: Choose the controller board — ESP32-S3 vs ESP32-C3
**Status:** Resolved **Date:** 2026-08-14

## Recommendation

Use the **ESP32-S3** as the controller.

## Why

The actuator path (see wireclaw-actuator-paths research) is to **extend the
WireClaw firmware** with a WS2812B ring (via the **RMT** peripheral) and a
stepper (4-phase GPIO sequencing). The board must run the WireClaw rule engine
_and_ drive these peripherals concurrently.

- **RMT channels**: the WS2812B ring needs RMT. The ESP32-S3 has **8 RMT
  channels** (4 TX + 4 RX); the ESP32-C3 has **4** (2 TX + 2 RX). More headroom
  for the LED ring plus any future channels.
- **CPU**: the S3 is **dual-core Xtensa LX7**; the C3 is **single-core RISC-V**.
  Driving RMT + stepper sequencing + the WireClaw rule loop concurrently is
  safer with two cores.
- **GPIO**: both have ample GPIO for 1 LED data pin + 4 ULN2003 pins; not a
  differentiator.
- **WireClaw support**: both are officially supported (README lists ESP32-C6,
  ESP32-S3, ESP32-C3). Not a differentiator.

The C3 would _work_ for a minimal build, but the S3's extra RMT channels and
dual-core headroom make it the robust choice for a realtime light + motion show.

## Sources

- WireClaw README (supported chips): https://github.com/M64GitHub/WireClaw
- ESP32-S3 / ESP32-C3 RMT channel counts: ESP-IDF `soc_caps.h` (RMT_TX_CHANNELS
  / RMT_RX_CHANNELS)
