/*
 * This file demonstrates output waveform displays.
 * In the waveform I/O panel, add a waveform for
 * Port A pin 6 (PA6) then type 'LOAD EX1.S19'
 * in the BUFFALO command window, then type 'GO 1040'.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

int main(void)
{
  int i;

  for (i=0; i < 3; i++) {
    TOC2 = TCNT + 2000;
    TFLG1 = OC2F;
    while ((TFLG1 & OC2F) != OC2F) /* NULL */ ;
    PORTA ^= PA6;
  }

  return 0;
}
