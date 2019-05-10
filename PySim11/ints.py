'''
Interrupt generation and recognition

The basic operation is as follows. After every instruction is executed
(with iexec() in PySim11.py) the flush() method of ucInterrupts is called
to clear all pending interrupts. Then, iexec() invokes each peripheral's
"udpate" function to possibly generate new interrupts. These are added
to the intdicts member of ucInterrupts (see the signal() method below
for an example). The member intdicts is a dictionary so multiple sources
of the same interrupt don't generate multiple interrupts. Finally,
iexec() calls nextInt() where interrupt priority resolution takes place.
This method either returns None if no interrupts are pending (or are
masked) or it returns one of the integers from 1 to 16 (i.e., from
XIRQ through SCI) to indicate the interrupt source.
'''

import sys
import string

from safestruct import *

XIRQ = 1
IRQ  = 2
RTII = 3
IC1I = 4
IC2I = 5
IC3I = 6
OC1I = 7
OC2I = 8
OC3I = 9
OC4I = 10
OC5I = 11     # Note that OC5I is also IC4I
IC4I = 11
TOI  = 12
PAOVI = 13
PAII  = 14
SPIE  = 15
SCI   = 16

Promotions = [    # From HPRIO
  TOI, PAOVI, PAII, SPIE, SCI, IRQ, IRQ, RTII,
  IC1I, IC2I, IC3I, OC1I, OC2I, OC3I, OC4I, OC5I
  ]

Vector = {
   XIRQ: 0xFFF4,
   IRQ:  0xFFF2,
   RTII: 0xFFF0,
   IC1I: 0xFFEE,
   IC2I: 0xFFEC,
   IC3I: 0xFFEA,
   OC1I: 0xFFE8,
   OC2I: 0xFFE6,
   OC3I: 0xFFE4,
   OC4I: 0xFFE2,
   OC5I: 0xFFE0,
   TOI:  0xFFDE,
   PAOVI: 0xFFDC,
   PAII:  0xFFDA,
   SPIE:  0xFFD8,
   SCI:   0xFFD6
   }

class ucInterrupts(SafeStruct):
  def __init__(self):
    super().__init__({
       'intdict': {}
    })

  def flush(self): self.intdict = {}

  def nextInt(self, simstate):
    L = self.intdict.keys()
    if L:
      if XIRQ in L: hipri = XIRQ
      else:
        promoted = Promotions[simstate.ucMemory.readUns8(simstate.ucMemory.HPRIO) & 0xF]
        if promoted in L: hipri = promoted
        else: hipri = min(L)

      if hipri == XIRQ:
        if not simstate.ucState.isXSet():
          del self.intdict[hipri]
          return hipri
      elif not simstate.ucState.isISet():
        del self.intdict[hipri]
        return hipri

  def signal(self, sig):
    assert 1 <= sig <= 16
    self.intdict[sig]=1
