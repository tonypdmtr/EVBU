/*
 * This file demonstrates parallel I/O input on Port A.
 * It responds to the stimulus files porta_20.sti through
 * porta_22.sti by echoing inputs at PA0-PA2 to PA4-PA6.
 *
 * In the waveform I/O panel, add a waveform for
 * Port A pins 0 through 2 and assign the file porta_20.sti
 * to PA0, porta_21.sti to PA1, and porta_22.sti to PA2. Then
 * add waveforms for Port A pins 4 through 6.
 *
 * Finally, type 'LOAD PORTA_2.S19' in the BUFFALO command
 * window, then type 'GO 1040'.
 */

#include <hc11a8.h>
#include <buffalo.h>

int main(void)
{
  int i;
  unsigned short start;

  /* Just copy PA0-2 up to PA4-6 for the next 5000 cycles, then
   * stop.
   */
  start = TCNT;
  while ((TCNT-start) < 5000) {
    PORTA = (PORTA & 0x07) << 4;
  }

  return 0;
}
