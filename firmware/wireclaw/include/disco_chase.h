#ifndef DISCO_CHASE_H
#define DISCO_CHASE_H

#include <stdint.h>
#include <stdbool.h>

#include "disco_config.h"

/* Initialize the chase state. Call once at boot. */
void discoChaseInit(void);

/* Set the comet color (0xRRGGBB) and direction (1 CW, -1 CCW, 0 stop). */
void discoChaseSet(uint32_t color, int8_t direction);

/* Advance the comet. Call from loop() each iteration. bpm drives the speed. */
void discoChasePoll(float bpm);

#endif /* DISCO_CHASE_H */
