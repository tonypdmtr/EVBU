/*
 * This file demonstrates pulse accumulator functionality
 * in event counting mode.
 *
 * It sets the accumulator to 250, waits for 6 pulses,
 * at which time an interrupt is generated. After the
 * interrupt, every time another pulse occurs, a message
 * is printed, until the pulse count reaches 4.
 *
 * In the waveform I/O panel, add a waveform for
 * Port A pins 7 and assign the pacc_1.sti stimulus file.
 * Then type 'LOAD PORTA_1.S19' in the BUFFALO command window,
 * then type 'GO 1040'.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

volatile static gotOV = 0;  // Set to 1 when overflow occurs

extern void paovfISR(void) __attribute__((interrupt));
void paovfISR(void)
{
  unsigned short attime = TCNT;
  unsigned char pacnt = PACNT;

  TFLG2 = PAOVF|PAIF; // clear flags
  outstr("Pulse accumulator overflow occurred at cycle:");
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

  /* Set PACNT to 250 so that after 6 pulses, we have a counter overflow */
  PACNT = 250;

  /* Program PACTL for event counting mode, rising edges */
  PACTL |= (PAEN|PEDGE);

  /* Program PAOVF interrupt */
  TMSK2 = PAOVI;

  /* Clear PAOVF flag */
  TFLG2 = PAOVF;

  /* Install PAOVF interrupt vector into secondary interrupt table */
  addr = *((unsigned short *)0xFFDC);
  *((unsigned short *)(addr+1)) = (unsigned short)paovfISR;

  interruptsON();

  /* Wait for overflow flag */
  while (gotOV == 0) /* NULL */ ;

  while (PACNT < 4) {
    /* Poll for next event */
    while ((TFLG2 & PAIF) == 0) /* NULL */ ;
    TFLG2 = PAIF;
    disp8(PACNT);
    outstr("\n");
  }

  return 0;
}
