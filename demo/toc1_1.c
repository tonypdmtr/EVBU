/*
 * This file demonstrates the TOC1 peripheral. In
 * the waveform I/O panel, add a waveform for Port A
 * pins 3-7 then type 'LOAD TOC1_1.S19' and then
 * type 'GO 1040'.
 *
 * This demonstration exercises all aspects of TOC1
 * behavior: OC1M/OC1D control, flags, interrupts, etc.
 * First, we use polling to generate a pattern on the
 * TOC outputs (pins 3-7) then we do the same using
 * interrupts.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

#define VEC 0xFFE8

static volatile int flag = 0;

extern void tocISR(void) __attribute__((interrupt));
void tocISR(void)
{
  TFLG1 = OC1F;
  OC1D = (OC1D >> 1);
  TOC1 += 2000;
  flag = 1;
}

int main(void)
{
  int i;
  unsigned short addr;

  interruptsOFF();
  addr = *((unsigned short *)VEC);
  *((unsigned short *)(addr+1)) = (unsigned short)tocISR;

  /* Phase 1: Generate OC1F events by polling and setting
   * a new bit in OC1D each time. */
  PORTA = 0;
  PACTL = DDRA3|DDRA7; // PA3 and PA7 outputs
  TOC1 = TCNT;
  OC1M = 0xF8;

  OC1D = 0;  /* March 1's from PA3 to PA7 */
  for (i=0; i < 5; i++) {
    OC1D = (OC1D << 1) | PA3;
    TOC1 += 2000;
    TFLG1 = OC1F;
    while ((TFLG1 & OC1F) != OC1F) /* NULL */ ;
  }

  /* Phase 2: Generate OC1I interrupts and clear a bit
   * in OC1D each time. */
  TOC1 += 2000;
  TFLG1 = OC1F;
  TMSK1 = OC1F;
  OC1D >>= 1;
  interruptsON();
  for (i=0; i < 5; i++) {
    flag = 0;
    while (flag == 0) /* NULL */ ;
  }

  /* Phase 3: Force a compare using CFORC. We will observe
   * this by setting PA7 and PA3 high. */
  OC1D = PA3|PA7;
  CFORC = FOC1;

  return 0;
}
