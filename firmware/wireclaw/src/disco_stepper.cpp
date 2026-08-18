/**
 * @file disco_stepper.cpp
 * @brief 28BYJ-48 stepper driver (4-phase half-step, ULN2003)
 *
 * The 28BYJ-48 is a 5V unipolar stepper with a 64:1 gearbox; 2048 half-steps
 * per output revolution. We drive the 4 ULN2003 inputs with a half-step
 * sequence. Speed is slew-limited toward the target RPM (a safety clamp).
 */

#include "disco_stepper.h"

#include <Arduino.h>

static const uint8_t s_pins[4] = {
    DISCO_STEPPER_IN1, DISCO_STEPPER_IN2, DISCO_STEPPER_IN3, DISCO_STEPPER_IN4,
};

/* Half-step sequence: 8 states, each a 4-bit mask of which coils are on. */
static const uint8_t s_seq[8] = {
    0b0001, 0b0011, 0b0010, 0b0110,
    0b0100, 0b1100, 0b1000, 0b1001,
};

static float s_target_rpm = 0.0f;
static float s_current_rpm = 0.0f;
static int8_t s_direction = 0; /* 1 CW, -1 CCW, 0 stop */
static uint8_t s_phase = 0;
static unsigned long s_last_step_ms = 0;

void discoStepperInit(void) {
    for (int i = 0; i < 4; i++) {
        pinMode(s_pins[i], OUTPUT);
        digitalWrite(s_pins[i], LOW);
    }
    s_last_step_ms = millis();
}

void discoStepperSetSpeed(float rpm, int8_t direction) {
    if (rpm < 0.0f) rpm = 0.0f;
    if (rpm > DISCO_STEPPER_MAX_RPM) rpm = (float)DISCO_STEPPER_MAX_RPM;
    s_target_rpm = rpm;
    s_direction = (direction > 0) ? 1 : (direction < 0) ? -1 : 0;
}

void discoStepperPoll(void) {
    unsigned long now = millis();
    float dt = (float)(now - s_last_step_ms) / 1000.0f;
    if (dt <= 0.0f) dt = 0.001f;

    /* Slew-limit the current RPM toward the target. */
    float max_delta = (float)DISCO_STEPPER_SLEW * dt;
    if (s_current_rpm < s_target_rpm) {
        s_current_rpm += max_delta;
        if (s_current_rpm > s_target_rpm) s_current_rpm = s_target_rpm;
    } else if (s_current_rpm > s_target_rpm) {
        s_current_rpm -= max_delta;
        if (s_current_rpm < s_target_rpm) s_current_rpm = s_target_rpm;
    }

    if (s_direction == 0 || s_current_rpm <= 0.0f) {
        /* Stop: de-energize coils to save power and avoid holding torque. */
        for (int i = 0; i < 4; i++) digitalWrite(s_pins[i], LOW);
        s_last_step_ms = now;
        return;
    }

    /* Steps per second = RPM * steps_per_rev / 60. */
    float steps_per_sec = s_current_rpm * DISCO_STEPPER_STEPS_PER_REV / 60.0f;
    if (steps_per_sec <= 0.0f) return;
    float step_interval_ms = 1000.0f / steps_per_sec;

    /* Advance as many phases as the elapsed time calls for, so the step rate
     * is decoupled from how often loop() runs (WireClaw's loop does blocking
     * network/LLM work and can be slow). */
    int steps = (int)(dt * 1000.0f / step_interval_ms);
    if (steps < 1) steps = 1;
    if (steps > 64) steps = 64; /* cap so a long stall doesn't burst wildly */

    for (int s = 0; s < steps; s++) {
        if (s_direction > 0) {
            s_phase = (s_phase + 1) & 7;
        } else {
            s_phase = (s_phase + 7) & 7;
        }
    }
    uint8_t mask = s_seq[s_phase];
    for (int i = 0; i < 4; i++) {
        digitalWrite(s_pins[i], (mask >> i) & 1 ? HIGH : LOW);
    }
    s_last_step_ms = now;
}
