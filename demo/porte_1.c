/*
 * This file demonstrates parallel I/O input on Port E.
 * It responds by printing the new value of Port E every
 * time it changes. Stimulus files porte_20.sti through
 * porte_27.sti (porte_20 for PE0, porte_21 for PE1, etc.)
 * are used in this example.
 *
 * In the waveform I/O panel, add a waveform for
 * Port E pins 0 through 7 and assign stimulus files
 * porte_20.sti through porte_27.sti. Then type 'LOAD PORTE_2.S19'
 * in the BUFFALO command window, then type 'GO 1040'.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

int main(void)
{
  unsigned short start;
  unsigned char pe;

  /* Monitor Port E for 10000 cycles, displaying when it
   * changes.
   */
  start = TCNT;
  pe = PORTE;
  while ((TCNT-start) < 10000) {
    if (pe != PORTE) {
      pe = PORTE;
      outstr("Port E is now: ");
      disp8(pe);
      outstr("\n");
    }
  }

  return 0;
}
