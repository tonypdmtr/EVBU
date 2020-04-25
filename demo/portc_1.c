/*
 * This file demonstrates parallel I/O output on Port C.
 * It sets each bit high in sequence, then each bit low.
 *
 * In the waveform I/O panel, add a waveform for
 * Port C pins 0 through 7 then type 'LOAD PORTC_1.S19'
 * in the BUFFALO command window, then type 'GO 1040'.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

int main(void)
{
  int i;

  /* Ensure DDRC set to all outputs */
  DDRC = 0xFF;

  /* First clear all bits */
  PORTC = 0;

  /* Now walk some ones from bit 0 through 7 */
  for (i=PC0; i <= PC7; i <<= 1) {
    PORTC |= i;
  }

  /* Now walk zeros in the same place */
  for (i=PC0; i <= PC7; i <<= 1) {
    PORTC &= ~i;
  }

  return 0;
}
