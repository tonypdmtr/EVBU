/*
 * This file demonstrates parallel I/O output on Port B.
 * It sets each bit high in sequence, then each bit low.
 *
 * In the waveform I/O panel, add a waveform for
 * Port B pins 0 through 7 then type 'LOAD PORTB_1.S19'
 * in the BUFFALO command window, then type 'GO 1040'.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

int main(void)
{
  int i;

  /* First clear all bits */
  PORTB = 0;

  /* Now walk some ones from bit 0 through 7 */
  for (i=PB0; i <= PB7; i <<= 1) {
    PORTB |= i;
  }

  /* Now walk zeros in the same place */
  for (i=PB0; i <= PB7; i <<= 1) {
    PORTB &= ~i;
  }

  return 0;
}
