/*
 * This file demonstrates parallel I/O output on Port A.
 * It sets each bit high in sequence, then each bit low.
 *
 * In the waveform I/O panel, add a waveform for
 * Port A pins 3 through 7 then type 'LOAD PORTA_1.S19'
 * in the BUFFALO command window, then type 'GO 1040'.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

#ifndef DDRA3
#define DDRA3 bit3
#endif

int main(void)
{
  int i;

  /* Set DDRA7 and DDRA3 to configure PA3 and PA7 as outputs */
  PACTL |= DDRA7|DDRA3;

  /* First clear all bits */
  PORTA = 0;

  /* Now walk some ones from bit 3 through 7 */
  for (i=PA3; i <= PA7; i <<= 1) {
    PORTA |= i;
  }

  /* Now walk zeros in the same place */
  for (i=PA3; i <= PA7; i <<= 1) {
    PORTA &= ~i;
  }

  return 0;
}
