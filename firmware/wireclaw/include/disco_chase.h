#ifndef DISCO_CHASE_H
#define DISCO_CHASE_H

#include <stdint.h>
#include <stdbool.h>

#include "disco_config.h"

/* Initialize the chase state. Call once at boot. */
void discoChaseInit(void);

/* Set the comet color (0xRRGGBB), direction (1 CW, -1 CCW, 0 stop), and the
 * BPM->speed endpoints: at slow_bpm the chase runs slow_speed LEDs/sec, at
 * fast_bpm it runs fast_speed LEDs/sec (linear interpolation). */
void discoChaseSet(uint32_t color, int8_t direction,
                   float slow_bpm, float fast_bpm,
                   float slow_speed, float fast_speed);

/* Advance the comet. Call from loop() each iteration. bpm drives the speed. */
void discoChasePoll(float bpm);

#endif /* DISCO_CHASE_H */
