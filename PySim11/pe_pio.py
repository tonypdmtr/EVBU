'''
Parallel I/O peripheral for PySim11

This peripheral handles the following:

* Reads/writes to Port A, B, C, D, E
* Changing Port A pins due to output compares
* Detecting edges at input capture pins
* Pulse accumulator

The following are NOT handled:

* Expanded-mode operation. That is, ports B and C
  are treated as parallel I/O, assuming the 68HC11 is
  in single-chip mode.

* Strobes, handshakes, etc. That is, PIOC and PORTCL
  are unimplemented.

* SPI/SCI are not considered so all bits of Port D
  are assumed to be available for general purpose I/O.

* A/D is not considered to all bits of Port E are
  assumed to be unconstrained and available for
  general purpose input.

The Timer module keeps track of the various flags
associated with the pulse accumulator and input
capture.
-------------------------------------------------

The logic of Port A is as follows:

  - reads from input pins 0-2 are simple reads

  - reads from pins 4-6 read the voltage being driven
    on the pin, which is either PAW or something from the
    Output Compare circuitry

  - reads from pins 7 and 3 depend on DDRA7 and DDRA3.
    When an input, the read value is the value at the pin itself.
    When an output, the read value is the value at the pin, which
    may be PAW or something from output compare.

  - DDRA7 always controls the direction of PA7. But DDRA3 is
    overridden if OC5 is used to control PA3, which then forces
    PA3 to be an output.
'''

import operator

from safestruct import *

import PySim11.memory
import PySim11.state
import PySim11.ints
import PySim11.laframe

from PySim11.PySim11 import ucPeripheral

# PORTA pins
OC1 = 0x80    # Note OC1 is same as PA
PA  = 0x80
OC2 = 0x40
OC3 = 0x20
OC4 = 0x10
OC5 = 0x08
IC4 = 0x08
IC1 = 0x04
IC2 = 0x02
IC3 = 0x01

# PACTL pins
DDRA7 = 0x80
PAEN  = 0x40
PAMOD = 0x20
PEDGE = 0x10
DDRA3 = 0x08
I4_O5 = 0x04
#RTR1  = 0x02
#RTR0  = 0x01

# TCTL1 pins (00 - Nothing, 01 - Toggle, 10 - Clear, 11 - Set)
OM2 = 0x80
OL2 = 0x40
OM3 = 0x20
OL3 = 0x10
OM4 = 0x08
OL4 = 0x04
OM5 = 0x02
OL5 = 0x01

# TCTL2 pins (00 - nothing, 01 - rising edges, 10 - falling edges, 11 - any edge)
EDG4B = 0x80
EDG4A = 0x40
EDG1B = 0x20
EDG1A = 0x10
EDG2B = 0x08
EDG2A = 0x04
EDG3B = 0x02
EDG3A = 0x01

# OC1M pins
OC1M7 = 0x80
OC1M6 = 0x40
OC1M5 = 0x20
OC1M4 = 0x10
OC1M3 = 0x08

# TFLG2 pins
PAOVF = 0x20
PAIF  = 0x10

try: from PySim11.laframe import LAFrame   #import wx
except: print('Main import failed')

class PIO(SafeStruct):
  def __init__(self, parentWindow):
    super().__init__({
      'sim': 0,
      'state': 0,
      'memory': 0,
      'ints': 0,
      'events': 0,
      'la': None,
      'laframe': None,
      'parent': parentWindow,
      'stimuli': None,   # List of (Cycles, Value, PortPin) tuples for input stimuli
      'pacnt': 0,
      'oc1m_cache': 0,
      'tctl1_cache': 0,
      'pactl_cache': 0,
      'PAI': 0,     # Input value (i.e., reads) of Port A present at external pins
                    # These values may be set by external stimulus files.
      'PAW': 0,     # Written value (i.e., writes) of Port A as written by software
                    # These values are set by executing code.
      'PAO': 0,     # Output value of Port A as would be driven on the actual pins.
                    # These values are either PAW or controlled by Output Compares.
      'PCI': 0,     # Input value (i.e., reads) of Port C as driven by stimulus
      'PCW': 0,     # Written value (i.e., writes) of Port C as written by software
      'PCO': 0,     # Output value of Port C as would be driven on the actual pins.
      'PDI': 0,     # Input value (i.e., reads) of Port D as driven by stimulus
      'PDW': 0,     # Written value (i.e., writes) of Port D as written by software
      'PDO': 0,     # Output value of Port D as would be driven on the actual pins.
      'PEI': 0      # Input value (i.e., reads) of Port E as driven by stimulus
    })

    self.laframe = PySim11.laframe.LAFrame(self.parent, -1, 'Parallel I/O')
    try:
      self.laframe.Show(1)

      # self.la is the LAPanel instance
      self.la = self.laframe.la

    except Exception as detail:
      print('Unable to import waveform display/stimulus interface.')
      print('Parallel I/O will only be reflected in the values of')
      print('on-chip registers.')
      print(detail)

  def BuildStimulusList(self):
    if self.la: self.stimuli = self.la.BuildStimulusList()
    else: self.stimuli = None

  def update(self, cycles):
    self.ProcessStimuli(self.sim.cycles)

    if self.pactl_cache & PAEN:
      if self.pactl_cache & (PAMOD|DDRA7) == PAMOD:   # Gated time accumulation mode
        # Check for count inhibited
        if (   ((self.pactl_cache & PEDGE == PEDGE) and (self.PAI & PA == 0)) \
            or ((self.pactl_cache & PEDGE == 0)     and (self.PAI & PA == PA))
           ):
          self.pa_counter += cycles
          if self.pa_counter >= 64:
            self.pa_counter -= 64
            self.pacnt = self.pacnt+1
            # Note: No PAIF event in gated mode
            if self.pacnt == 256:
              self.pacnt = 0
              self.events.notifyEvent(self.events.PAOV)

  def updatePAO(self):
    # Update voltages driven on Port A pins based on changes to PAW or
    # controlling registers (OC1M, TCTL1, PACTL).

    # We worry only about bits 3-7 as bits 0-2 are inputs. Bits 4-6 are
    # driven either by PAW or by output compare circuitry. The output
    # compare events do not persist and serve only to modify PAO directly.
    # Once the OC circuitry doesn't control a pin, it reverts back to the
    # last software-written value. Thus, we construct a mask that indicates
    # which bits are driven by PAW. All other bits are left alone.

    # OC1M indicates which bits are controlled by OC1 for sure
    mask = self.oc1m_cache

    # Failing OC1M control, the OM/OL bits in TCTL1 indicate control
    tctl1 = self.tctl1_cache
    if tctl1 & (OM2|OL2): mask |= OC1M6
    if tctl1 & (OM3|OL3): mask |= OC1M5
    if tctl1 & (OM4|OL4): mask |= OC1M4
    if tctl1 & (OM5|OL5): mask |= OC1M3

    # Now turn off mask bits for input pins. DDRA7 is an absolute.
    pactl = self.pactl_cache
    if pactl & DDRA7 == 0: mask &= ~OC1M7
    if pactl & I4_O5: mask &= ~OC1M3

    # At last. Write the value and note any events
    self.notifyPAO(self.PAO & mask | self.PAW & ~mask)

  def notifyPAO(self, newPAO, exactcycle=None):
    oldPAO = self.PAO
    self.PAO = newPAO
    diff = oldPAO ^ self.PAO

    exactcycle = exactcycle or self.sim.cycles

    if self.la and diff:
      for bit in range(3,8):
        m = 1 << bit
        if diff & m:
          self.la.Append('PA%d' % bit, exactcycle, ((self.PAO & m) != 0))

  def readPortA(self, addr, bits, val, rw):
    pactl = self.pactl_cache

    # First, read bits 0-2 and 4-6 since these are dedicated.
    val = self.PAI & 0x07 | self.PAO & 0x70

    # Check DDRA7. If an output, use PAO, otherwise use PAI
    if pactl & DDRA7: val |= self.PAO & 0x80
    else: val |= self.PAI & 0x80

    # Check DDRA3. If an output, use PAO, otherwise use PAI.
    # Also, if OC5 is controlling PA3, this overrides DDRA3.
    # This logic needs to be verified as the reference manual
    # applies to the A8 device which doesn't have the bidirectional
    # PA3 pin.
    if pactl & DDRA3 == DDRA3: val |= self.PAO & 0x08       # output
    elif pactl & I4_O5 == 0:            #OC5 enabled
      if self.tctl1_cache & (OM5|OL5):
        val |= self.PAO & 0x08          #OC5 is forcing PA3 to be an output
      elif self.oc1m_cache & OC1M3:
        val |= self.PAO & 0x08          #OC1 is controlling PA3 hence forcing an output
      else: val |= self.PAI & 0x08
    else: val |= self.PAI & 0x08

    self.memory.writeRawUns8(self.memory.PORTA, val)

  def writePortA(self, addr, bits, val, rw):
    self.PAW = val
    self.updatePAO()

  def writePortB(self, addr, bits, val, rw):
    oldPB = self.memory.readUns8(self.memory.PORTB)
    diff = oldPB ^ val

    if self.la and diff:
      for bit in range(8):
        m = 1 << bit
        if diff & m:
          self.la.Append('PB%d' % bit, self.sim.cycles, ((val & m) != 0))

  def updatePCO(self, ddrc=None):
    ddrc = ddrc or self.memory.readUns8(self.memory.DDRC)   # 1 for bits marked as outputs
    newPCO = self.PCW & ddrc | self.PCI & ~ddrc

    diff = newPCO ^ self.PCO
    self.PCO = newPCO

    if self.la and diff:
      for bit in range(8):
        m = 1 << bit
        if diff & ddrc & m:
          self.la.Append('PC%d' % bit, self.sim.cycles, ((self.PCO & m) != 0))

  def writeDDRC(self, addr, bits, val, rw): self.updatePCO(val)

  def writePortC(self, addr, bits, val, rw):
    self.PCW = val
    self.updatePCO()

  def readPortC(self, addr, bits, val, rw):
    mask = self.memory.readUns8(self.memory.DDRC)   # 1 for bits marked as outputs
    readval = self.PCI & ~mask | self.PCW & mask
    self.memory.writeRawUns8(self.memory.PORTC, readval)

  def updatePDO(self, ddrd=None):
    ddrd = ddrd or self.memory.readUns8(self.memory.DDRD)   # 1 for bits marked as outputs
    newPDO = self.PDW & ddrd | self.PDI & ~ddrd

    diff = newPDO ^ self.PDO
    self.PDO = newPDO

    if self.la and diff:
      for bit in range(6):
        m = 1 << bit
        if diff & ddrd & m:
          self.la.Append('PD%d' % bit, self.sim.cycles, ((self.PDO & m) != 0))

  def writeDDRD(self, addr, bits, val, rw): self.updatePDO(val)

  def writePortD(self, addr, bits, val, rw):
    self.PDW = val & 0x3F
    self.updatePDO()

  def readPortD(self, addr, bits, val, rw):
    mask = self.memory.readUns8(self.memory.DDRD)   # 1 for bits marked as outputs
    readval = self.PDI & ~mask | self.PDW & mask
    self.memory.writeRawUns8(self.memory.PORTD, readval & 0x3F)

  def readPortE(self, addr, bits, val, rw):
    self.memory.writeRawUns8(self.memory.PORTE, self.PEI)

  def writeOC1M(self, addr, bits, val, rw):
    self.oc1m_cache = val
    self.updatePAO()

  def writeTCTL1(self, addr, bits, val, rw):
    self.tctl1_cache = val
    self.updatePAO()

  def writePACTL(self, addr, bits, val, rw):
    self.pactl_cache = val
    self.updatePAO()

  def readPACNT(self, addr, bits, val, rw):
    self.memory.writeRawUns8(self.memory.PACNT, self.pacnt)

  def writePACNT(self, addr, bits, val, rw): self.pacnt = val

  def OCEvent(self, event, exactcycle=None):
    tctl1 = self.tctl1_cache
    pactl = self.pactl_cache

    # Compute the actual simulator cycle time of the event.
    # We use the exactcyle parameter if given, simulator cycles if not
    exactcycle = exactcycle or self.sim.cycles

    # Let's handle easy ones first. If the TCTL
    # register is configured to manipulate bits
    # based on compares, then handle it, otherwise
    # do nothing.
    if event == 'OC2':
      if tctl1 & (OM2|OL2) == OL2:      # TOGGLE
        self.notifyPAO(self.PAO ^ OC2, exactcycle)
      elif tctl1 & (OM2|OL2) == OM2:    # CLEAR
        self.notifyPAO(self.PAO & ~OC2, exactcycle)
      elif tctl1 & (OM2|OL2) == OM2|OL2:# SET
        self.notifyPAO(self.PAO | OC2, exactcycle)
    elif event == 'OC3':
      if tctl1 & (OM3|OL3) == OL3:      # TOGGLE
        self.notifyPAO(self.PAO ^ OC3, exactcycle)
      elif tctl1 & (OM3|OL3) == OM3:    # CLEAR
        self.notifyPAO(self.PAO & ~OC3, exactcycle)
      elif tctl1 & (OM3|OL3) == OM3|OL3:# SET
        self.notifyPAO(self.PAO | OC3, exactcycle)
    elif event == 'OC4':
      if tctl1 & (OM4|OL4) == OL4:      # TOGGLE
        self.notifyPAO(self.PAO ^ OC4, exactcycle)
      elif tctl1 & (OM4|OL4) == OM4:    # CLEAR
        self.notifyPAO(self.PAO & ~OC4, exactcycle)
      elif tctl1 & (OM4|OL4) == OM4|OL4:# SET
        self.notifyPAO(self.PAO | OC4, exactcycle)
    elif event == 'OC5' and pactl & I4_O5 == 0:
      if tctl1 & (OM5|OL5) == OL5:      # TOGGLE
        self.notifyPAO(self.PAO ^ OC5, exactcycle)
      elif tctl1 & (OM5|OL5) == OM5:    # CLEAR
        self.notifyPAO(self.PAO & ~OC5, exactcycle)
      elif tctl1 & (OM5|OL5) == OM5|OL5:# SET
        self.notifyPAO(self.PAO | OC5, exactcycle)

    # Now we handle OC1.
    if event == 'OC1':
      oc1m = self.oc1m_cache
      oc1d = self.memory.readUns8(self.memory.OC1D)
      newPAO = self.PAO
      if oc1m & OC1M7 and pactl & DDRA7 == DDRA7:
        newPAO = newPAO & ~OC1 | oc1d & OC1M7
      if oc1m & OC1M6: newPAO = newPAO & ~OC2 | oc1d & OC1M6
      if oc1m & OC1M5: newPAO = newPAO & ~OC3 | oc1d & OC1M5
      if oc1m & OC1M4: newPAO = newPAO & ~OC4 | oc1d & OC1M4
      if oc1m & OC1M3 and pactl & I4_O5 == 0:
        newPAO = newPAO & ~OC5 | oc1d & OC1M3
      self.notifyPAO(newPAO, exactcycle)

  def OnSimStart(self, event): self.la.IsSimulating(1)

  def OnSimEnd(self, event): self.la.IsSimulating(0)

  def ProcessStimuli(self, toCycle):
    while self.stimuli:
      S = self.stimuli[0]

      if S[0] <= toCycle:
        del self.stimuli[0]
        self.StimPortBit(S[2], S[1], S[0])
      else: break

  def StimPortBit(self, portpin, val, atTime):
    port = portpin[:2]
    bit  = int(portpin[2:])
    mask = ~(1 << bit)
    bitval = val << bit

    if port == 'PA' and bit in [0,1,2,3,7]:
      #print self.sim.cycles, ' Old PAI:', hex(self.PAI)
      newPAI = (self.PAI & mask) | bitval
      self.CheckInputCaptureAndPA(bit, newPAI, atTime)
      self.PAI = newPAI
      #print self.sim.cycles, ' New PAI:', hex(self.PAI)
    elif port == 'PC': self.PCI = self.PCI & mask | bitval
    elif port == 'PD': self.PDI = self.PDI & mask | bitval
    elif port == 'PE': self.PEI = self.PEI & mask | bitval

  def CheckInputCaptureAndPA(self, bit, newPAI, atTime):
    mask = 1 << bit
    diff = (self.PAI ^ newPAI) & mask
    if diff==0: return

    tctl2 = self.memory.readUns8(self.memory.TCTL2)
    rising  = newPAI & mask == mask
    falling = not rising

    if bit==0:
      action = tctl2 & (EDG3B|EDG3A)
      if (   (action == EDG3A and rising) \
          or (action == EDG3B and falling) \
          or (action == EDG3A|EDG3B) \
         ):
        self.events.notifyEvent(self.events.IC3, (atTime,))
    elif bit==1:
      action = tctl2 & (EDG2B|EDG2A)
      if (   (action == EDG2A and rising) \
          or (action == EDG2B and falling) \
          or (action == EDG2A|EDG2B) \
         ):
        self.events.notifyEvent(self.events.IC2, (atTime,))
    elif bit==2:
      action = tctl2 & (EDG1B|EDG1A)
      if (   (action == EDG1A and rising) \
          or (action == EDG1B and falling) \
          or (action == EDG1A|EDG1B) \
         ):
        self.events.notifyEvent(self.events.IC1, (atTime,))
    elif bit==3:
      if self.pactl_cache & I4_O5 == I4_O5:
        action = (tctl2 & (EDG4B|EDG4A))
        if (   (action == EDG4A and rising) \
            or (action == EDG4B and falling) \
            or (action == EDG4A|EDG4B) \
           ):
          self.events.notifyEvent(self.events.IC4, (atTime,))
    elif bit==7:
      # Check that PA is enabled, PA7 is an input, event counter mode
      if self.pactl_cache & (DDRA7|PAEN|PAMOD) == PAEN:
        # Now check to see if we got the right edge
        if (   (self.pactl_cache & PEDGE==0 and falling) \
            or (self.pactl_cache & PEDGE!=0 and rising) \
           ):
          self.pacnt = self.pacnt+1
          self.events.notifyEvent(self.events.PAI)
          if self.pacnt == 256:
            self.pacnt = 0
            self.events.notifyEvent(self.events.PAOV)

  def OnCycReset(self, event):
    if self.la: self.la.OnCycReset(event)

    self.BuildStimulusList()
    self.ProcessStimuli(0)

def install(sim, parentWindow):
  T = PIO(parentWindow)
  T.sim = sim
  T.state = sim.ucState
  T.memory = sim.ucMemory
  T.ints = sim.ucInterrupts
  T.events = sim.ucEvents

  pe = ucPeripheral(T, 'Parallel I/O')

  # Register memory handler to handle reads/writes of Port A, B, C, D, E
  f = PySim11.memory.ucMemoryFilter(T.memory.PORTA, T.memory.PORTA, None, T.readPortA, T.writePortA)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.PORTB, T.memory.PORTB, None, None, T.writePortB)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.PORTC, T.memory.PORTC, None, T.readPortC, T.writePortC)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.PORTD, T.memory.PORTD, None, T.readPortD, T.writePortD)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.PORTE, T.memory.PORTE, None, T.readPortE, None)
  sim.ucMemory.addFilter(f)

  # Trap DDRC and DDRD to update Ports C and D if necessary
  f = PySim11.memory.ucMemoryFilter(T.memory.DDRC, T.memory.DDRC, None, None, T.writeDDRC)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.DDRD, T.memory.DDRD, None, None, T.writeDDRD)
  sim.ucMemory.addFilter(f)

  # Register memory handler to handle writes of OC1M, TCTL1, and PACTL
  # as these can affect the data driven onto Port A.
  # Read PACNT through us, too.
  f = PySim11.memory.ucMemoryFilter(T.memory.OC1M, T.memory.OC1M, None, None, T.writeOC1M)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.PACTL, T.memory.PACTL, None, None, T.writePACTL)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.TCTL1, T.memory.TCTL1, None, None, T.writeTCTL1)
  sim.ucMemory.addFilter(f)
  f = PySim11.memory.ucMemoryFilter(T.memory.PACNT, T.memory.PACNT, None, T.readPACNT, T.writePACNT)
  sim.ucMemory.addFilter(f)

  # Register event handlers for output compares
  T.events.addHandler(T.events.OC1, T.OCEvent)
  T.events.addHandler(T.events.OC2, T.OCEvent)
  T.events.addHandler(T.events.OC3, T.OCEvent)
  T.events.addHandler(T.events.OC4, T.OCEvent)
  T.events.addHandler(T.events.OC5, T.OCEvent)

  # Register system event handlers for simulation start/stop
  T.events.addHandler(T.events.SimStart, T.OnSimStart)
  T.events.addHandler(T.events.SimEnd, T.OnSimEnd)

  # Handler for when to reset the display panel
  T.events.addHandler(T.events.CycReset, T.OnCycReset)
  return pe
