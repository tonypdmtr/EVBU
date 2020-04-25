/*
 * This file demonstrates input waveform stimulus and display.
 * In the waveform I/O panel, add a waveform for
 * Port A pin 0 (PA0). In the Stimulus File text box of the
 * dialog box, browse for the EXAMPLE.STI file and enter it in
 * the box. Then type 'LOAD EX2.S19'
 * in the BUFFALO command window, then type 'GO 1040'.
 *
 */
#include <hc11a8.h>
#include <buffalo.h>

int main(void)
{
  int i;
  unsigned char oldPortA = PORTA;

  for (i=0; i < 3; i++) {
    while (PORTA == oldPortA) /* NULL */ ;
    oldPortA = PORTA;
    outstr("Port A changed at cycle ");
    disp16(TCNT);
    outstr("\n");
  }

  return 0;
}
