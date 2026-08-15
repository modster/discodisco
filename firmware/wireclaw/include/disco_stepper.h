/**
 * @file disco_stepper.h
 * @brief 28BYJ-48 stepper driver (4-phase half-step, ULN2003)
 */

#ifndef DISCO_STEPPER_H
#define DISCO_STEPPER_H

#include <stdint.h>
#include <stdbool.h>

#include "disco_config.h"

/* Initialize the 4 GPIO pins. Call once at boot. */
void discoStepperInit(void);

/* Set target speed in RPM (clamped to DISCO_STEPPER_MAX_RPM) and direction.
 * direction: 1 = CW, -1 = CCW, 0 = stop. */
void discoStepperSetSpeed(float rpm, int8_t direction);

/* Advance the phase toward the target speed. Call from loop() each iteration. */
void discoStepperPoll(void);

#endif /* DISCO_STEPPER_H */
