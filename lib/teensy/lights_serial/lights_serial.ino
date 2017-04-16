/* USB to Serial - Teensy becomes a USB to Serial converter
   http://dorkbotpdx.org/blog/paul/teensy_as_benito_at_57600_baud

   You must select Serial from the "Tools > USB Type" menu

   This example code is in the public domain.
*/

#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>
#include <OctoWS2811.h>

#define LEDS_PER_STRIP 100
#define LEDS_LAST_STRIP 0
#define NUM_STRIPS 4
//#define TOTAL_LEDS (LEDS_PER_STRIP * (NUM_STRIPS-1) + LEDS_LAST_STRIP)
#define TOTAL_LEDS (LEDS_PER_STRIP * NUM_STRIPS)
#define BAUD 115200

DMAMEM int displayMemory[LEDS_PER_STRIP*6];
int drawingMemory[LEDS_PER_STRIP*6];
const int config = WS2811_GRB | WS2811_800kHz;
OctoWS2811 leds(LEDS_PER_STRIP, displayMemory, drawingMemory, config);

// set this to the hardware serial port you wish to use
#define HWSERIAL Serial1

unsigned long baud = 19200;

void setup()
{
  Serial.begin(BAUD);
  leds.begin();
}

// lower the RGB values of a color by a constant factor
int dim_color(int color, float value) {
  int r = (int)((color >> 16 & 0xFF) * value);
  int g = (int)((color >> 8 & 0xFF) * value);
  int b = (int)((color & 0xFF) * value);

  return (r << 16) | (g << 8) | b;
}

int led_location(int i) {
  // prevent overflows
  if (i >= TOTAL_LEDS)
    return -1;

  // no idea why these two pairs of addresses are switched, but they are...
  if (i == 499 || i == 500)
    i -= 499;
  else if (i <= 500)
    i += 2;

  int strip = i / LEDS_PER_STRIP;
  int base = strip * LEDS_PER_STRIP;

  if (strip == 0) {
    i += LEDS_PER_STRIP;
    base = LEDS_PER_STRIP;
    return base + (base + LEDS_PER_STRIP - i + 1);
  } else if (strip == 1) {
    i -= LEDS_PER_STRIP;
    return i;
  }

  if (strip % 2 == 0) {
    return base + (base + LEDS_PER_STRIP - i + 1);
  } else {
    return i;
  }
}

// void loop()
// {
//   uint8_t r, g, b, i0, i1;
//   uint16_t i;
//   uint32_t color;
//
//   while(Serial.available()){
//     char inc = (char)Serial.read();
//     if(inc == '$'){
//       for (i=0; i < TOTAL_LEDS; i++) {
//         //i1 = Serial.read();
//         //i0 = Serial.read();
//         r = Serial.read();
//         g = Serial.read();
//         b = Serial.read();
//
//         //i = (i1 << 8) + i0;
//         color = (r << 16) + (g << 8) + b;
//
//         if (color >= 0) {
//           int loc = led_location(i);
//           if (loc >= 0)
//             leds.setPixel(loc, color);
//         }
//       }
//     leds.show();
//     }
//   }
// }
void loop() {
  uint8_t r, g, b, i0, i1;
  uint16_t i;
  uint32_t color;

  while(Serial.available()){
    char inc = (char)Serial.read();
    if(inc == 'L'){
      i0 = Serial.read();
      i1 = Serial.read();
      r = Serial.read();
      g = Serial.read();
      b = Serial.read();

      i = (i1 << 8) + i0;
      color = (r << 16) + (g << 8) + b;

      if (color >= 0) {
        int loc = led_location(i);
        if (loc >= 0)
          leds.setPixel(i, color);
      }
    }
  }
  leds.show();
}
