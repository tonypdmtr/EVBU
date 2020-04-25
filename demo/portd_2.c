/*
 * This file demonstrates parallel I/O input on Port D.
 * It responds by printing the new value of Port D every
 * time it changes. Stimulus files portd_20.sti through
 * portd_25.sti (portd_20 for PD0, portd_21 for PD1, etc.)
 * are used in this example.
 *
 * In the waveform I/O panel, add a waveform for
 * Port D pins 0 through 5 and assign stimulus files
 * portd_20.sti through portd_25.sti. Then type 'LOAD PORTD_2.S19'
 * in the BUFFALO command window, then type 'GO 1040'.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

int main(void)
{
  unsigned short start;
  unsigned char pd;

  /* Ensure DDRD set to all inputs */
  DDRD = 0x00;

  /* Monitor Port D for 10000 cycles, displaying when it
   * changes.
   */
  start = TCNT;
  pd = PORTD;
  while ((TCNT-start) < 10000) {
    if (pd != PORTD) {
      pd = PORTD;
      outstr("Port D is now: ");
      disp8(pd);
      outstr("\n");
    }
  }

  return 0;
}
