/*
 * This file demonstrates parallel I/O output on Port D.
 * It sets each bit high in sequence, then each bit low.
 *
 * In the waveform I/O panel, add a waveform for
 * Port D pins 0 through 5 then type 'LOAD PORTD_1.S19'
 * in the BUFFALO command window, then type 'GO 1040'.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

int main(void)
{
  int i;

  /* Ensure DDRD set to all outputs */
  DDRD = 0x3F;

  /* First clear all bits */
  PORTD = 0;

  /* Now walk some ones from bit 0 through 5 */
  for (i=PD0; i <= PD5; i <<= 1) {
    PORTD |= i;
  }

  /* Now walk zeros in the same place */
  for (i=PD0; i <= PD5; i <<= 1) {
    PORTD &= ~i;
  }

  return 0;
}
