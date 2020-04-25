/*
 * This file demonstrates the TIC1 peripheral. In
 * the waveform I/O panel, add a waveform for Port A
 * pin 2 (PA2) and assign the TIC1_1.STI stimulus file
 * to it. Then type 'LOAD TIC1_1.S19' and type 'GO 1040'.
 *
 * This demonstration exercises all aspects of TIC1
 * behavior: flags, interrupts, TIC register. We use
 * a stimulus that oscillates every 1024 cycles and display
 * when TIC1F events occur. First, we use polling, then
 * interrupts.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

#define TIC TIC1
#define ICF IC1F
#define PA  PA2
#define EDGA EDG1A
#define EDGB EDG1B
#define VEC 0xFFEE

static volatile int intcount = 0;

extern void ticISR(void) __attribute__((interrupt));
void ticISR(void)
{
  TFLG1 = ICF;
  disp16(TIC); outstr("\n");
  intcount++;
}

int main(void)
{
  int i;
  unsigned short addr;

  interruptsOFF();
  addr = *((unsigned short *)VEC);
  *((unsigned short *)(addr+1)) = (unsigned short)ticISR;

  TCTL2 = EDGA|EDGB;

  /* Phase 1: Verify flag behavior */
  TFLG1 = ICF;
  while ((TFLG1 & ICF) != ICF) /* NULL */ ;
  disp16(TIC); outstr("\n");

  TFLG1 = ICF;
  while ((TFLG1 & ICF) != ICF) /* NULL */ ;
  disp16(TIC); outstr("\n");

  /* Phase 2: Verify interrupt behavior */
  TMSK1 = ICF;
  TFLG1 = ICF;
  interruptsON();

  while (intcount < 2) /* NULL */ ;

  return 0;
}
