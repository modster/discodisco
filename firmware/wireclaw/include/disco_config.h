/**
 * @file disco_config.h
 * @brief Disco ball controller configuration (pins, clamps, LED count)
 *
 * All disco-specific hardware settings live here. Pins are chosen to be safe
 * on both ESP32-S3 and ESP32-C3 "super mini" boards (GPIO 0-15 only, avoiding
 * strapping pins). Override per board if needed.
 */

#ifndef DISCO_CONFIG_H
#define DISCO_CONFIG_H

/* --- WS2812B ring --- */
#define DISCO_RING_PIN        4    /* RMT data line to WS2812B DIN */
#define DISCO_RING_LEDS       8    /* number of LEDs in the ring */
#define DISCO_RING_MAX_BRIGHT 255  /* safety clamp: max per-channel brightness */

/* --- 28BYJ-48 stepper (via ULN2003) --- */
#define DISCO_STEPPER_IN1     5
#define DISCO_STEPPER_IN2     6
#define DISCO_STEPPER_IN3     7
#define DISCO_STEPPER_IN4     8
#define DISCO_STEPPER_MAX_RPM 15   /* safety clamp: max rotation speed (RPM) */
#define DISCO_STEPPER_SLEW    60   /* safety clamp: max RPM change per second */

/* 28BYJ-48: 2048 half-steps per revolution (64:1 gearbox, 4-phase half-step) */
#define DISCO_STEPPER_STEPS_PER_REV 2048

#endif /* DISCO_CONFIG_H */
