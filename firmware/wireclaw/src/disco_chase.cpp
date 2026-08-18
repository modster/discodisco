#include "disco_chase.h"

#include <Arduino.h>
#include <math.h>

#include "disco_ring.h"

static uint32_t s_color = 0xFF0000;
static int8_t s_direction = 1;
static float s_pos = 0.0f;
static unsigned long s_last_ms = 0;

void discoChaseInit(void) {
    s_last_ms = millis();
}

void discoChaseSet(uint32_t color, int8_t direction) {
    s_color = color;
    s_direction = (direction > 0) ? 1 : (direction < 0) ? -1 : 0;
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

    /* Speed: LEDs/sec from BPM (120 BPM -> 4 LEDs/sec, 60 BPM -> 2). */
    float speed = (bpm > 0.0f) ? (bpm / 30.0f) : 2.0f;
    s_pos += speed * dt * s_direction;

    /* Wrap position into [0, 8). */
    s_pos = fmodf(s_pos, (float)DISCO_RING_LEDS);
    if (s_pos < 0.0f) s_pos += (float)DISCO_RING_LEDS;

    uint8_t r = (s_color >> 16) & 0xFF;
    uint8_t g = (s_color >> 8) & 0xFF;
    uint8_t b = s_color & 0xFF;

    /* Head at s_pos, fading trail of 3 LEDs behind it. */
    const float trail_len = 3.0f;
    for (int i = 0; i < DISCO_RING_LEDS; i++) {
        float behind = fmodf(s_pos - (float)i, (float)DISCO_RING_LEDS);
        if (behind < 0.0f) behind += (float)DISCO_RING_LEDS;
        float brightness = (behind < trail_len) ? (1.0f - behind / trail_len) : 0.0f;
        discoRingSetPixel((uint8_t)i,
                          (uint8_t)(r * brightness),
                          (uint8_t)(g * brightness),
                          (uint8_t)(b * brightness));
    }
    discoRingShow();
}
