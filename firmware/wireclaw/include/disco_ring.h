/**
 * @file disco_ring.h
 * @brief WS2812B LED ring driver (RMT)
 */

#ifndef DISCO_RING_H
#define DISCO_RING_H

#include <stdint.h>
#include <stdbool.h>

#include "disco_config.h"

/* Initialize the RMT channel + encoder. Call once at boot. */
bool discoRingInit(void);

/* Set one LED's color (clamped to DISCO_RING_MAX_BRIGHT). */
void discoRingSetPixel(uint8_t index, uint8_t r, uint8_t g, uint8_t b);

/* Fill all LEDs with one color. */
void discoRingFill(uint8_t r, uint8_t g, uint8_t b);

/* Push the current pixel buffer to the ring. */
void discoRingShow(void);

#endif /* DISCO_RING_H */
