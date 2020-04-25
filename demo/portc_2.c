/*
 * This file demonstrates parallel I/O input on Port C.
 * It responds by printing the new value of Port C every
 * time it changes. Stimulus files portc_20.sti through
 * portc_27.sti (portc_20 for PC0, portc_21 for PC1, etc.)
 * are used in this example.
 *
 * In the waveform I/O panel, add a waveform for
 * Port C pins 0 through 7 and assign stimulus files
 * portc_20.sti through portc_27.sti. Then type 'LOAD PORTC_2.S19'
 * in the BUFFALO command window, then type 'GO 1040'.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

int main(void)
{
  unsigned short start;
  unsigned char pc;

  /* Ensure DDRC set to all inputs */
  DDRC = 0x00;

  /* Monitor Port C for 10000 cycles, displaying when it
   * changes.
   */
  start = TCNT;
  pc = PORTC;
  while ((TCNT-start) < 10000) {
    if (pc != PORTC) {
      pc = PORTC;
      outstr("Port C is now: ");
      disp8(pc);
      outstr("\n");
    }
  }

  return 0;
}
