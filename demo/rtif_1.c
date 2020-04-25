/*
 * This file demonstrates the RTIF flag. It looks at both
 * the RTIF flag and RTII interrupt. It causes Port A pin 6
 * to toggle every 8192 cycles, in response to real-time
 * overflow. The first toggle occurs by polling the RTIF
 * flag, the second via an interrupt handler.
 *
 * Add a waveform for PA6, load this program by typing
 * 'LOAD RTIF_1.S19' and type 'GO 1040'.
 *
 */
#include <hc11a8.h>
#include <buffalo.h>

static volatile int done = 0;

extern void rtifISR(void) __attribute__((interrupt));
void rtifISR(void)
{
  TFLG2 = RTIF;
  PORTA ^= PA6;
  done = 1;
}

int main(void)
{
  int i;
  unsigned short addr;

  interruptsOFF();

  addr = *((unsigned short *)0xFFF0);
  *((unsigned short *)(addr+1)) = (unsigned short)rtifISR;

  PORTA = 0;

  i = 0;
  while ((TFLG2 & RTIF) != RTIF) /* NULL */ ;

  PORTA ^= PA6;
  TFLG2 = RTIF;
  TMSK2 = RTII;

  interruptsON();

  while (! done) /* NULL */ ;

  return 0;
}
