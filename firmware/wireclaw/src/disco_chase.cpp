#include "disco_chase.h"

#include <Arduino.h>
#include <math.h>

#include "disco_ring.h"

static uint32_t s_color = 0xFF0000;
static int8_t s_direction = 1;
static float s_pos = 0.0f;
static unsigned long s_last_ms = 0;

/* BPM->speed endpoints (linear interpolation). */
static float s_slow_bpm = 60.0f;
static float s_fast_bpm = 180.0f;
static float s_slow_speed = 2.0f;
static float s_fast_speed = 8.0f;

/* Slew-limited current speed (LEDs/sec). */
static float s_current_speed = 2.0f;

void discoChaseInit(void) {
    s_last_ms = millis();
}

void discoChaseSet(uint32_t color, int8_t direction,
                   float slow_bpm, float fast_bpm,
                   float slow_speed, float fast_speed) {
    s_color = color;
    s_direction = (direction > 0) ? 1 : (direction < 0) ? -1 : 0;

    /* Clamp the endpoint speeds to the firmware safety max. */
    if (slow_speed < 0.0f) slow_speed = 0.0f;
    if (slow_speed > DISCO_CHASE_MAX_SPEED) slow_speed = DISCO_CHASE_MAX_SPEED;
    if (fast_speed < 0.0f) fast_speed = 0.0f;
    if (fast_speed > DISCO_CHASE_MAX_SPEED) fast_speed = DISCO_CHASE_MAX_SPEED;

    s_slow_bpm = slow_bpm;
    s_fast_bpm = fast_bpm;
    s_slow_speed = slow_speed;
    s_fast_speed = fast_speed;
}

void discoChasePoll(float bpm) {
    unsigned long now = millis();
    float dt = (float)(now - s_last_ms) / 1000.0f;
    if (dt <= 0.0f) dt = 0.001f;
    s_last_ms = now;

    if (s_direction == 0) {
        discoRingFill(0, 0, 0);
        discoRingShow();
        return;
    }

    /* Speed: linear interpolation of BPM between the scene-settable endpoints,
     * clamped to [0, DISCO_CHASE_MAX_SPEED], then slew-limited. */
    float target = s_slow_speed;
    if (s_fast_bpm > s_slow_bpm) {
        float t = (bpm - s_slow_bpm) / (s_fast_bpm - s_slow_bpm);
        if (t < 0.0f) t = 0.0f;
        if (t > 1.0f) t = 1.0f;
        target = s_slow_speed + (s_fast_speed - s_slow_speed) * t;
    }
    if (target < 0.0f) target = 0.0f;
    if (target > DISCO_CHASE_MAX_SPEED) target = DISCO_CHASE_MAX_SPEED;

    /* Slew-limit the current speed toward the target. */
    float max_delta = DISCO_CHASE_SLEW * dt;
    float diff = target - s_current_speed;
    if (diff > max_delta) diff = max_delta;
    if (diff < -max_delta) diff = -max_delta;
    s_current_speed += diff;

    s_pos += s_current_speed * dt * s_direction;

    /* Wrap position into [0, 8). */
    s_pos = fmodf(s_pos, (float)DISCO_RING_LEDS);
    if (s_pos < 0.0f) s_pos += (float)DISCO_RING_LEDS;

    uint8_t r = (s_color >> 16) & 0xFF;
    uint8_t g = (s_color >> 8) & 0xFF;
    uint8_t b = s_color & 0xFF;

    /* Head at s_pos, fading trail of 3 LEDs behind it. */
    const float trail_len = 3.0f;
    for (int i = 0; i < DISCO_RING_LEDS; i++) {
        float behind = fmodf((s_pos - (float)i) * s_direction, (float)DISCO_RING_LEDS);
        if (behind < 0.0f) behind += (float)DISCO_RING_LEDS;
        float brightness = (behind < trail_len) ? (1.0f - behind / trail_len) : 0.0f;
        discoRingSetPixel((uint8_t)i,
                          (uint8_t)(r * brightness),
                          (uint8_t)(g * brightness),
                          (uint8_t)(b * brightness));
    }
    discoRingShow();
}
