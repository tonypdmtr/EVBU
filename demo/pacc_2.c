/*
 * This file demonstrates pulse accumulator functionality
 * in event counting mode. It tests for proper operation
 * of the PAI interrupt in event counting mode.
 *
 * In the waveform I/O panel, add a waveform for
 * Port A pins 7 and assign the pacc_2.sti stimulus file.
 * Then type 'LOAD PORTA_1.S19' in the BUFFALO command window,
 * then type 'GO 1040'.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

volatile unsigned char gotOV = 0;

extern void paifISR(void) __attribute__((interrupt));
void paifISR(void)
{
  unsigned short attime = TCNT;
  unsigned char pacnt = PACNT;

  TFLG2 = PAOVF|PAIF; // clear flags
  outstr("Pulse accumulator interrupt occurred at cycle:");
  disp16(attime);
  outstr("\n");
  disp8(pacnt);
  outstr("\n");
  TMSK2 = 0;     // disable further interrupts
  gotOV = 1;
}

int main(void)
{
  int i;
  unsigned short addr;

  interruptsOFF();

  /* Set DDRA7 to configure PA7 as an input */
  PACTL &= ~DDRA7;
  PACNT = 0;

  /* Program PACTL for event counting mode, rising edges */
  PACTL |= (PAEN|PEDGE);

  /* Program PAIF interrupt */
  TMSK2 = PAII;

  /* Clear PAIF flag */
  TFLG2 = PAIF;

  /* Install PAIF interrupt vector into secondary interrupt table */
  addr = *((unsigned short *)0xFFDA);
  *((unsigned short *)(addr+1)) = (unsigned short)paifISR;

  interruptsON();

  /* Wait for overflow flag */
  while (gotOV == 0) /* NULL */ ;

  return 0;
}
