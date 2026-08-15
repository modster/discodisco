/**
 * @file disco_ring.cpp
 * @brief WS2812B LED ring driver via the ESP-IDF RMT peripheral.
 *
 * Drives an 8-LED WS2812B ring on a single data GPIO. Uses the new RMT driver
 * API (ESP-IDF 5.x) with a bytes encoder. Holds the 8 LED colors; a single
 * rmt_transmit pushes the whole frame. Brightness is clamped to
 * DISCO_RING_MAX_BRIGHT (a safety clamp, not LLM-settable).
 */

#include "disco_ring.h"

#include <driver/rmt_encoder.h>
#include <driver/rmt_tx.h>
#include <esp_log.h>
#include <freertos/FreeRTOS.h>
#include <string.h>

static const char *TAG = "disco_ring";

static rmt_channel_handle_t s_chan = NULL;
static rmt_encoder_handle_t s_encoder = NULL;
static uint8_t s_pixels[DISCO_RING_LEDS * 3]; /* GRB per LED */

/* WS2812B timing (ns): T0H=350, T0L=900, T1H=900, T1L=350 */
#define RMT_RES_HZ 10 * 1000 * 1000 /* 10 MHz -> 100ns resolution */

bool discoRingInit(void) {
    rmt_tx_channel_config_t tx_cfg = {
        .gpio_num = (gpio_num_t)DISCO_RING_PIN,
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .resolution_hz = RMT_RES_HZ,
        .mem_block_symbols = 64,
        .trans_queue_depth = 4,
    };
    if (rmt_new_tx_channel(&tx_cfg, &s_chan) != ESP_OK) {
        ESP_LOGE(TAG, "rmt_new_tx_channel failed");
        return false;
    }

    rmt_bytes_encoder_config_t enc_cfg = {};
    enc_cfg.bit0.duration0 = 3;
    enc_cfg.bit0.level0 = 1;
    enc_cfg.bit0.duration1 = 9;
    enc_cfg.bit0.level1 = 0;
    enc_cfg.bit1.duration0 = 9;
    enc_cfg.bit1.level0 = 1;
    enc_cfg.bit1.duration1 = 3;
    enc_cfg.bit1.level1 = 0;
    enc_cfg.flags.msb_first = 1;
    if (rmt_new_bytes_encoder(&enc_cfg, &s_encoder) != ESP_OK) {
        ESP_LOGE(TAG, "rmt_new_bytes_encoder failed");
        return false;
    }
    if (rmt_enable(s_chan) != ESP_OK) {
        ESP_LOGE(TAG, "rmt_enable failed");
        return false;
    }
    memset(s_pixels, 0, sizeof(s_pixels));
    return true;
}

void discoRingSetPixel(uint8_t index, uint8_t r, uint8_t g, uint8_t b) {
    if (index >= DISCO_RING_LEDS) return;
    r = (uint8_t)((r * DISCO_RING_MAX_BRIGHT) / 255);
    g = (uint8_t)((g * DISCO_RING_MAX_BRIGHT) / 255);
    b = (uint8_t)((b * DISCO_RING_MAX_BRIGHT) / 255);
    s_pixels[index * 3 + 0] = g; /* GRB order */
    s_pixels[index * 3 + 1] = r;
    s_pixels[index * 3 + 2] = b;
}

void discoRingFill(uint8_t r, uint8_t g, uint8_t b) {
    for (int i = 0; i < DISCO_RING_LEDS; i++) {
        discoRingSetPixel(i, r, g, b);
    }
}

void discoRingShow(void) {
    if (!s_chan || !s_encoder) return;
    rmt_transmit_config_t tx_cfg = {.loop_count = 0};
    rmt_transmit(s_chan, s_encoder, s_pixels, sizeof(s_pixels), &tx_cfg);
    /* Wait for the frame to be sent before returning */
    rmt_tx_wait_all_done(s_chan, portMAX_DELAY);
}
