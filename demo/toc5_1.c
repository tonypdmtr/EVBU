/*
 * This file demonstrates the TOC5 peripheral. In
 * the waveform I/O panel, add a waveform for Port A
 * pin 6 (PA6) then type 'LOAD TOC5_1.S19' and then
 * type 'GO 1040'.
 *
 * This demonstration exercises all aspects of TOC5
 * behavior: TCTL1 control, flags, interrupts, etc.
 * First, we use polling to generate a rising and falling
 * edge manually. Then we do the same using TCTL1 control
 * with set/clear, and then again with TCTL1 toggle
 * behavior. Finally, we generate two more compare events
 * and record the time in interrupt handlers.
 *
 */

#include <hc11a8.h>
#include <buffalo.h>

#define TOC TOC5
#define OCF OC5F
#define PA  PA3
#define OM  OM5
#define OL  OL5
#define VEC 0xFFE0

extern void tocISR(void) __attribute__((interrupt));
void tocISR(void)
{
  TFLG1 = OCF;
  PORTA ^= PA;
  TOC += 2000;
}

int main(void)
{
  int i;
  unsigned short addr;

  /* Must ensure OC5 is enabled, DDRA3 is an output */
  PACTL = DDRA3;

  interruptsOFF();
  addr = *((unsigned short *)VEC);
  *((unsigned short *)(addr+1)) = (unsigned short)tocISR;

  /* Phase 1: Verify output compares occur */
  PORTA = 0;
  TOC = TCNT;

  TOC += 2000;
  TFLG1 = OCF;
  while ((TFLG1 & OCF) != OCF) /* NULL */ ;
  PORTA |= PA;

  TOC += 2000;
  TFLG1 = OCF;
  while ((TFLG1 & OCF) != OCF) /* NULL */ ;
  PORTA &= ~PA;

  /* Phase 2: Verify TCTL1 set/clear control */
  TOC += 2000;
  TFLG1 = OCF;
  TCTL1 = OM|OL;  // Set on compare
  while ((TFLG1 & OCF) != OCF) /* NULL */ ;

  TOC += 2000;
  TFLG1 = OCF;
  TCTL1 = OM;     // Clear on compare
  while ((TFLG1 & OCF) != OCF) /* NULL */ ;

  /* Phase 3: Verify TCTL1 toggle control */
  TOC += 2000;
  TFLG1 = OCF;
  TCTL1 = OL;     // Toggle on compare
  while ((TFLG1 & OCF) != OCF) /* NULL */ ;

  TOC += 2000;
  TFLG1 = OCF;
  while ((TFLG1 & OCF) != OCF) /* NULL */ ;

  /* Phase 4: Verify toggle via interrupts */
  TOC += 2000;
  TFLG1 = OCF;
  TMSK1 = OCF;
  TCTL1 = 0;
  interruptsON();

  // Wait for rising edge
  while ((PORTA & PA) != PA) /* NULL */ ;

  // Wait for falling edge
  while ((PORTA & PA) == PA) /* NULL */ ;

  interruptsOFF();

  // Now generate toggle events using CFORC
  TCTL1 = OL; // Toggle on compare
  CFORC = OCF; // Force compare twice
  CFORC = OCF;

  return 0;
}
