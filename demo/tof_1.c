/*
 * This file demonstrates the TOF flag. It looks at both
 * the TOF flag and TOI interrupt. It causes Port A pin 6
 * to toggle every 65536 cycles, in response to timer
 * overflow. The first toggle occurs by polling the TOF
 * flag, the second via an interrupt handler.
 *
 * Add a waveform for PA6, load this program by typing
 * 'LOAD TOF_1.S19' and type 'GO 1040'.
 *
 */
#include <hc11a8.h>
#include <buffalo.h>

static volatile int done = 0;

extern void tofISR(void) __attribute__((interrupt));
void tofISR(void)
{
  TFLG2 = TOF;
  PORTA ^= PA6;
  done = 1;
}

int main(void)
{
  int i;
  unsigned short addr;

  interruptsOFF();

  addr = *((unsigned short *)0xFFDE);
  *((unsigned short *)(addr+1)) = (unsigned short)tofISR;

  PORTA = 0;

  i = 0;
  while ((TFLG2 & TOF) != TOF) /* NULL */ ;

  PORTA ^= PA6;
  TFLG2 = TOF;
  TMSK2 = TOI;

  interruptsON();

  while (! done) /* NULL */ ;

  return 0;
}
