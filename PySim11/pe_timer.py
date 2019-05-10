'''
Timer peripheral for PySim11

This peripheral has the following tasks:

* Maintain the free-running counter at $100E
* Generate TOF for timer overflows
* Generate RTIF for the real-time interval timer
* Generate OC1F-OC5F if output compares match
* Handle the TFLG1/TFLG2 registers properly
* Generate OC1F-OC5F upon writes to CFORC
* Generate interrupts based upon flags
'''

import operator

from safestruct import *

import PySim11.memory
import PySim11.state
import PySim11.ints

from PySim11.PySim11 import ucPeripheral

# TMSK2 register
PRbits = 0x03

# TFLG2 register
TOF   = 0x80
RTIF  = 0x40
PAOVF = 0x20
PAIF  = 0x10

# TFLG1 register
OC1F = 0x80
OC2F = 0x40
OC3F = 0x20
OC4F = 0x10
OC5F = 0x08   # Same as IC4F
IC4F = 0x08
IC1F = 0x04
IC2F = 0x02
IC3F = 0x01

# PACTL register
RTRbits = 0x03
I4_O5   = 0x04

Prescales = [1, 4, 8, 16];   # Determined by lower 2 bits of TMSK2
RTILimits = [8192, 16384, 32768, 65536]  # Determined by lower 2 bits of PACTL


class Timer(SafeStruct):
  def __init__(self, parentWindow):
    super().__init__({
      'sim': 0,
      'state': 0,
      'memory': 0,
      'ints': 0,
      'events': 0,
      'parent': parentWindow,
      'cnt': 0,
      'rticnt': 0,
      'cycles': 0,
      'lastsimcycles': 0,
      'tof_bit': 0,
      'rtif_bit': 0,
      'paif_bit': 0,
      'paovf_bit': 0,
      'oc1f_bit': 0,
      'oc2f_bit': 0,
      'oc3f_bit': 0,
      'oc4f_bit': 0,
      'oc5f_bit': 0,
      'ic1f_bit': 0,
      'ic2f_bit': 0,
      'ic3f_bit': 0,
      'ic4f_bit': 0,
      'tic1': 0,
      'tic2': 0,
      'tic3': 0,
      'tic4': 0,
      'tmsk1_cache': 0,
      'tmsk2_cache': 0,
      'pactl_cache': 0,
      'toc1_cache': 0,
      'toc2_cache': 0,
      'toc3_cache': 0,
      'toc4_cache': 0,
      'toc5_cache': 0,
      'prescale': Prescales[0],
      'rtilimit': RTILimits[0]
    })

  def update(self, cycles, __mod__=operator.__mod__):
    self.cycles += cycles
    self.lastsimcycles = self.sim.cycles

    before = self.cnt
    after = self.cnt = int(self.cycles/self.prescale) & 0xFFFF
    self.cycles &= 0xFFFFF
    if after < before: after += 65536

    # Motorola E-series technical reference manual says RTI is
    # independent of prescaler, so we just add 'cycles' to rticnt.
    self.rticnt += cycles
    if self.rticnt >= self.rtilimit:
      self.rtif_bit = RTIF
      self.rticnt -= self.rtilimit
      self.events.notifyEvent(self.events.RTI)
    while self.rticnt >= self.rtilimit:
      self.rticnt -= self.rtilimit

    # Check for timer overflow and timer compares. We have to adjust the
    # exact time of compares since an instruction generates multiple cycles
    # and the simulator time increments in these quanta, whereas the actual
    # compare event occurs on the very cycle it's supposed to, not on
    # simulator cycle boundaries. So....we generate a list (cycvalues) of all
    # the cycles represented by this instruction, find where in this list the
    # TOC register value lies, then add it to the previous simulator time. Since
    # the simulator time has already been updated by the time we get to update(),
    # we have to subtract off 'cycles'. For example, self.lastsimcycles=1000,
    # cycles=4, and TOC2=999. That means this instruction went through cycles
    # cycvalues=[997, 998, 999, 1000]. We have a TOC2 compare and the expression
    #   self.lastsimcycles - cycles + cycvalues.index(self.toc2_cache) + 1
    # computes
    #   1000 - 4 + 2 + 1 = 999
    # as required.
    if after > before:
      if after >= 65536:
        self.tof_bit = TOF
        self.events.notifyEvent(self.events.TOV)

      cycvalues = range(before+1,after+1)
      # Probably faster as bitwise-and instead of mod
      cycvalues = list(map(__mod__, cycvalues, [65536]*len(cycvalues)))

      if self.toc1_cache in cycvalues:
        self.oc1f_bit = OC1F
        actualcyc = self.lastsimcycles - cycles + cycvalues.index(self.toc1_cache) + 1
        self.events.notifyEvent(self.events.OC1, (actualcyc,))
      if self.toc2_cache in cycvalues:
        self.oc2f_bit = OC2F
        actualcyc = self.lastsimcycles - cycles + cycvalues.index(self.toc2_cache) + 1
        self.events.notifyEvent(self.events.OC2, (actualcyc,))
      if self.toc3_cache in cycvalues:
        self.oc3f_bit = OC3F
        actualcyc = self.lastsimcycles - cycles + cycvalues.index(self.toc3_cache) + 1
        self.events.notifyEvent(self.events.OC3, (actualcyc,))
      if self.toc4_cache in cycvalues:
        self.oc4f_bit = OC4F
        actualcyc = self.lastsimcycles - cycles + cycvalues.index(self.toc4_cache) + 1
        self.events.notifyEvent(self.events.OC4, (actualcyc,))
      if self.toc5_cache in cycvalues:
        self.oc5f_bit = OC5F
        actualcyc = self.lastsimcycles - cycles + cycvalues.index(self.toc5_cache) + 1
        self.events.notifyEvent(self.events.OC5, (actualcyc,))

    tmsk2 = self.tmsk2_cache
    if tmsk2:
      if self.tof_bit & tmsk2: self.ints.signal(ints.TOI)
      if self.rtif_bit & tmsk2: self.ints.signal(ints.RTII)
      if self.paif_bit & tmsk2: self.ints.signal(ints.PAII)
      if self.paovf_bit & tmsk2: self.ints.signal(ints.PAOVI)

    tmsk1 = self.tmsk1_cache
    if tmsk1:
      if self.oc1f_bit & tmsk1: self.ints.signal(ints.OC1I)
      if self.oc2f_bit & tmsk1: self.ints.signal(ints.OC2I)
      if self.oc3f_bit & tmsk1: self.ints.signal(ints.OC3I)
      if self.oc4f_bit & tmsk1: self.ints.signal(ints.OC4I)
      if self.oc5f_bit & tmsk1:
        if (self.pactl_cache & I4_O5) == 0: self.ints.signal(ints.OC5I)

      if self.ic4f_bit & tmsk1:
        if (self.pactl_cache & I4_O5) == I4_O5: self.ints.signal(ints.IC4I)
      if self.ic3f_bit & tmsk1: self.ints.signal(ints.IC3I)
      if self.ic2f_bit & tmsk1: self.ints.signal(ints.IC2I)
      if self.ic1f_bit & tmsk1: self.ints.signal(ints.IC1I)

  def readTimer(self, addr, bits, val, rw):
    self.memory.writeRawUns16(self.memory.TCNT, self.cnt)

  def handleIC1F(self, event, atTime):
    '''The question is how many cycles beyond self.cnt did this event
    happen? The 'atTime' parameter is a simulator cycle number
    (i.e., sim.cycles). In PySim11, the simulator cycles are updated
    *before* calling update() for peripherals. Example situation:
       sim.cycles = 1000, atTime = 998
    Now, if self.lastsimcycles == self.sim.cycles this means that our
    own update() function has already been called and self.cnt
    must be reduced somewhat to get the actual count. Otherwise,
    self.lastsimcycles < self.sim.cycles and this means that our
    own update() function has not been called yet and self.cnt
    must be incremented somewhat to get the actual count.'''

    if self.lastsimcycles == self.sim.cycles:
      # Already updated
      diff = self.lastsimcycles - atTime
      assert diff >= 0
      self.tic1 = self.cnt - int(diff/self.prescale)
    else:
      diff = atTime - self.lastsimcycles
      assert diff >= 0
      self.tic1 = self.cnt + int(diff/self.prescale)
    self.ic1f_bit = IC1F

  def handleIC2F(self, event, atTime):
    if self.lastsimcycles == self.sim.cycles:
      # Already updated
      diff = self.lastsimcycles - atTime
      assert diff >= 0
      self.tic2 = self.cnt - int(diff/self.prescale)
    else:
      diff = atTime - self.lastsimcycles
      assert diff >= 0
      self.tic2 = self.cnt + int(diff/self.prescale)
    self.ic2f_bit = IC2F

  def handleIC3F(self, event, atTime):
    if self.lastsimcycles == self.sim.cycles:
      # Already updated
      diff = self.lastsimcycles - atTime
      assert diff >= 0
      self.tic3 = self.cnt - int(diff/self.prescale)
    else:
      diff = atTime - self.lastsimcycles
      assert diff >= 0
      self.tic3 = self.cnt + int(diff/self.prescale)
    self.ic3f_bit = IC3F

  def handleIC4F(self, event, atTime):
    if self.lastsimcycles == self.sim.cycles:
      # Already updated
      diff = self.lastsimcycles - atTime
      assert diff >= 0
      self.tic4 = self.cnt - int(diff/self.prescale)
    else:
      diff = atTime - self.lastsimcycles
      assert diff >= 0
      self.tic4 = self.cnt + int(diff/self.prescale)
    self.ic4f_bit = IC4F

  def handlePAI(self, event): self.paif_bit = PAIF

  def handlePAOV(self, event): self.paovf_bit = PAOVF

  def readTflg1(self, addr, bits, val, rw):
    if self.pactl_cache & I4_O5: val = self.ic4f_bit        # IC4 enabled
    else: val = self.oc5f_bit                               # OC5 enabled
    val |= self.oc1f_bit | self.oc2f_bit | self.oc3f_bit | self.oc4f_bit \
        | self.ic1f_bit | self.ic2f_bit | self.ic3f_bit

    self.memory.writeRawUns8(self.memory.TFLG1, val)

  def writeTflg1(self, addr, bits, val, rw):
    if val & OC1F: self.oc1f_bit = 0
    if val & OC2F: self.oc2f_bit = 0
    if val & OC3F: self.oc3f_bit = 0
    if val & OC4F: self.oc4f_bit = 0
    if val & OC5F:
      if self.pactl_cache & I4_O5 == 0: self.oc5f_bit = 0
      else: self.ic4f_bit = 0
    if val & IC1F: self.ic1f_bit = 0
    if val & IC2F: self.ic2f_bit = 0
    if val & IC3F: self.ic3f_bit = 0

  def readTflg2(self, addr, bits, val, rw):
    val = self.tof_bit | self.rtif_bit | self.paif_bit | self.paovf_bit
    self.memory.writeRawUns8(self.memory.TFLG2, val)

  def writeTflg2(self, addr, bits, val, rw):
    if val & TOF: self.tof_bit = 0
    if val & RTIF: self.rtif_bit = 0
    if val & PAIF: self.paif_bit = 0
    if val & PAOVF: self.paovf_bit = 0

  def writeCFORC(self, addr, bits, val, rw):
    # Manual says flag bits are NOT set, and no interrupt generated
    if val & OC1F: self.events.notifyEvent(self.events.OC1)
    if val & OC2F: self.events.notifyEvent(self.events.OC2)
    if val & OC3F: self.events.notifyEvent(self.events.OC3)
    if val & OC4F: self.events.notifyEvent(self.events.OC4)
    if val & OC5F and self.pactl_cache & I4_O5 == 0:
      self.events.notifyEvent(self.events.OC5)

  def readTIC123(self, addr, bits, val, rw):
    if addr == self.memory.TIC1:
      self.memory.writeRawUns16(self.memory.TIC1, self.tic1)
    elif addr == self.memory.TIC2:
      self.memory.writeRawUns16(self.memory.TIC2, self.tic2)
    elif addr == self.memory.TIC3:
      self.memory.writeRawUns16(self.memory.TIC3, self.tic3)

  def readTIC4(self, addr, bits, val, rw):
    if self.pactl_cache & I4_O5 == I4_O5:
      self.memory.writeRawUns16(self.memory.TIC4, self.tic4)

  def writeTMSK2(self, addr, bits, val, rw):
    self.tmsk2_cache = val
    self.prescale = Prescales[val & PRbits]

  def writeTMSK1(self, addr, bits, val, rw): self.tmsk1_cache = val

  def writePACTL(self, addr, bits, val, rw):
    self.pactl_cache = val
    self.rtilimit = RTILimits[val & RTRbits]

  def writeTOC12345(self, addr, bits, val, rw):
    if addr == self.memory.TOC1: self.toc1_cache = val
    elif addr == self.memory.TOC2: self.toc2_cache = val
    elif addr == self.memory.TOC3: self.toc3_cache = val
    elif addr == self.memory.TOC4: self.toc4_cache = val
    elif addr == self.memory.TOC5: self.toc5_cache = val

def install(sim, parentWindow):
  T = Timer(parentWindow)
  T.sim = sim
  T.state = sim.ucState
  T.memory = sim.ucMemory
  T.ints = sim.ucInterrupts
  T.events = sim.ucEvents

  pe = ucPeripheral(T, "Timer")

  # Register memory handler to return counter when reading $100E
  f = PySim11.memory.ucMemoryFilter(T.memory.TCNT, T.memory.TCNT+1, None, T.readTimer, None)
  sim.ucMemory.addFilter(f)

  # Register memory handler to handle TFLG1 register
  f = PySim11.memory.ucMemoryFilter(T.memory.TFLG1, T.memory.TFLG1, None, T.readTflg1, T.writeTflg1)
  sim.ucMemory.addFilter(f)

  # Register memory handler to handle TFLG2 register
  f = PySim11.memory.ucMemoryFilter(T.memory.TFLG2, T.memory.TFLG2, None, T.readTflg2, T.writeTflg2)
  sim.ucMemory.addFilter(f)

  # Register memory handler to handle writes to CFORC
  f = PySim11.memory.ucMemoryFilter(T.memory.CFORC, T.memory.CFORC, None, None, T.writeCFORC)
  sim.ucMemory.addFilter(f)

  # Register memory handler to handle reads of TIC1-TIC4
  f = PySim11.memory.ucMemoryFilter(T.memory.TIC1, T.memory.TIC3+1, None, T.readTIC123, None)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.TIC4, T.memory.TIC4, None, T.readTIC4, None)
  sim.ucMemory.addFilter(f)

  # Register memory handlers for writes of TMSK1, TMSK2, PACTL, TOC1-TOC5 (for caching)
  f = PySim11.memory.ucMemoryFilter(T.memory.TMSK1, T.memory.TMSK1, None, None, T.writeTMSK1)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.TMSK2, T.memory.TMSK2, None, None, T.writeTMSK2)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.PACTL, T.memory.PACTL, None, None, T.writePACTL)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.TOC1, T.memory.TOC5+1, None, None, T.writeTOC12345)
  sim.ucMemory.addFilter(f)

  # If input capture events are generated by the PIO module, save the times
  T.events.addHandler(T.events.IC1, T.handleIC1F)
  T.events.addHandler(T.events.IC2, T.handleIC2F)
  T.events.addHandler(T.events.IC3, T.handleIC3F)
  T.events.addHandler(T.events.IC4, T.handleIC4F)

  # Pulse accumulator events are generated by the PIO module but we handle
  # the flags.
  T.events.addHandler(T.events.PAI, T.handlePAI)
  T.events.addHandler(T.events.PAOV, T.handlePAOV)

  return pe
