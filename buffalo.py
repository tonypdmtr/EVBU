'''
buffalo.py -- Emulate BUFFALO services as virtual functions
'''

SHFTREG = 0x96  # Correct for BUFFALO 3.4
STOPITH = 0xE3
STOPITL = 0x71
STOPIT  = STOPITH << 8 | STOPITL
JSCI    = 0xC4  # Start of secondary interrupt jump table

FuncList = (
  (0xFF82, 'rprint'),
  (0xFF85, 'hexbin'),
  (0xFF8E, 'chgbyt'),
  (0xFFA0, 'upcase'),
  (0xFFA3, 'wchek'),
  (0xFFAC, 'input'),
  (0xFFB2, 'outlhl'),
  (0xFFB5, 'outrhl'),
  (0xFFB8, 'outa'),
  (0xFFBB, 'out1by'),
  (0xFFBE, 'out1bs'),
  (0xFFC1, 'out2bs'),
  (0xFFC4, 'outcrl'),
  (0xFFC7, 'outstr'),
  (0xFFCA, 'outst0'),
  (0xFFCD, 'inchar'),
  (0xFFD0, 'vecint'),
  (STOPIT, 'unhandledInt')
  )

VecList = (
  (0xFFD6, JSCI+0),       # SCI
  (0xFFD8, JSCI+3),       # SPIE
  (0xFFDA, JSCI+6),       # PAII
  (0xFFDC, JSCI+9),       # PAOVI
  (0xFFDE, JSCI+12),      # TOI
  (0xFFE0, JSCI+15),      # OC5I
  (0xFFE2, JSCI+18),      # OC4I
  (0xFFE4, JSCI+21),      # OC3I
  (0xFFE6, JSCI+24),      # OC2I
  (0xFFE8, JSCI+27),      # OC1I
  (0xFFEA, JSCI+30),      # IC3I
  (0xFFEC, JSCI+33),      # IC2I
  (0xFFEE, JSCI+36),      # IC1I
  (0xFFF0, JSCI+39),      # RTII
  (0xFFF2, JSCI+42),      # IRQ
  (0xFFF4, JSCI+45),      # XIRQ
  (0xFFF6, JSCI+48),      # SWI
  (0xFFF8, JSCI+51),      # ILLOP
  (0xFFFA, JSCI+54),      # COP
  (0xFFFC, JSCI+57),      # CLOCKMON
  (0xFFFE, 0xE000)        # Reset
  )

import sys
import string
import os
import queue
import time

from safestruct import *

import evbu
from PySim11 import PySim11
from PySim11.ops import UnhandledInterrupt
from PySim11.state import CC_Z

class BuffaloServices(SafeStruct):
  def __init__(self, evb):
    super().__init__({
      'evb': evb
    })
    self.write = evb.write

    for tup in FuncList:
      evb.simstate.VFlist.append(PySim11.ucVirtualFunction(tup[0], eval('self.%s' % tup[1])))

    for tup in VecList: evb.simstate.ucMemory.writeUns16(tup[0], tup[1])

    self.vecint(evb.simstate, force = 1)

  # Initialize the RAM secondary vector table with "JMP >STOPIT"
  # instructions, except where the user has changed "STOPIT" to their
  # own address.
  def vecint(self, simstate, force = 0):
    for addr in range(JSCI, JSCI+3*20, 3):
      if force or (simstate.ucMemory.readUns8(addr) != 0x7E):
        simstate.ucMemory.writeUns8(addr, 0x7E)       # JMP instruction
        simstate.ucMemory.writeUns16(addr+1, STOPIT)

  # This gets called when "JMP >STOPIT" is actually executed, i.e., the
  # user hasn't replaced "STOPIT" with their own address.

  def unhandledInt(self, simstate):
    raise UnhandledInterrupt('!!! Unhandled interrupt')

  # I don't think this works the way it's supposed to. Why is it still here?
  if 0:
            def __intdispatch(self, simstate, JSCIoffset, text):
              # See if the secondary jump table offset is 'JMP STOPIT'. If not,
              # it's a user-installed vector and we take it.
              JSCIaddr = JSCI + JSCIoffset
              if simstate.ucMemory.readRawTuple8(JSCIaddr, JSCIaddr+2) == (0x7E, STOPITH, STOPITL):
                # It's an unhandled interrupt
                raise UnhandledInterrupt(f'!!! Unhandled {text} interrupt !!!')

              # It's a handled interrupt. Let the user do whatever he wants.
              # We jump to this address by pushing it on the stack since the
              # virtual function handler in PySim11.step() assumes all virtual
              # functions end in RTS.
              simstate.ucState.push16(simstate.ucMemory, JSCIaddr)

            def intSCI(self, simstate): self.__intdispatch(simstate, 0, "SCI")
            def intSPIE(self, simstate): self.__intdispatch(simstate, 3, "SPI")
            def intPAII(self, simstate): self.__intdispatch(simstate, 6, "PAI")
            def intPAOVI(self, simstate): self.__intdispatch(simstate, 9, "PAOV")
            def intTOI(self, simstate): self.__intdispatch(simstate, 12, "TOI")
            def intOC5I(self, simstate): self.__intdispatch(simstate, 15, "OC5")
            def intOC4I(self, simstate): self.__intdispatch(simstate, 18, "OC4")
            def intOC3I(self, simstate): self.__intdispatch(simstate, 21, "OC3")
            def intOC2I(self, simstate): self.__intdispatch(simstate, 24, "OC2")
            def intOC1I(self, simstate): self.__intdispatch(simstate, 27, "OC1")
            def intIC4I(self, simstate): self.__intdispatch(simstate, 30, "OC5") # IC4 is the same as OC5
            def intIC3I(self, simstate): self.__intdispatch(simstate, 30, "IC3")
            def intIC2I(self, simstate): self.__intdispatch(simstate, 33, "IC2")
            def intIC1I(self, simstate): self.__intdispatch(simstate, 36, "IC1")
            def intRTII(self, simstate): self.__intdispatch(simstate, 39, "RTI")
            def intIRQ(self, simstate): self.__intdispatch(simstate, 42, "IRQ")
            def intXIRQ(self, simstate): self.__intdispatch(simstate, 45, "XIRQ")
            def intSWI(self, simstate): self.__intdispatch(simstate, 48, "SWI")
            def intILLOP(self, simstate): self.__intdispatch(simstate, 51, "ILLOP")
            def intCOP(self, simstate): self.__intdispatch(simstate, 54, "COP")
            def intCLOCKMON(self, simstate): self.__intdispatch(simstate, 57, "CLOCKMON")

  def input(self, simstate):
    try:
      ch = self.evb.queue.get(0)
      assert len(ch)
      simstate.ucState.setA(ord(ch[0]))
    except queue.Empty:
      simstate.ucState.setA(0)

  def inchar(self, simstate):
    simstate.ucEvents.notifyEvent(simstate.ucEvents.CharWait)
    while 1:
      try:
        ch = self.evb.queue.get(0)
        assert len(ch)
        ch = ch[0]
      except queue.Empty: ch = 0

      if ch != 0:
        simstate.ucState.setA(ord(ch))
        break

      if simstate.breakEvent and not simstate.breakEvent.isSet():
        # User requested break. Give up.
        break

      # A little sleep, just so we don't hog 100% CPU time
      time.sleep(0.1)
    #end while
    simstate.ucEvents.notifyEvent(simstate.ucEvents.NoCharWait)

  def upcase(self, simstate):
    newstr = ("%c" % simstate.ucState.A).upper()
    simstate.ucState.setA(ord(newstr[0]))

  def rprint(self, simstate): simstate.ucState.display(self.write)

  def out1bs(self, simstate):
    self.out1by(simstate)
    self.write(' ')

  def out2bs(self, simstate):
    self.out1by(simstate)
    self.out1bs(simstate)

  def out1by(self, simstate):
    X = simstate.ucState.X
    val = simstate.ucMemory.readUns8(X)
    self.write('%02X' % val)
    simstate.ucState.setX(X+1)

  def outlhl(self, simstate):
    val = simstate.ucState.A >> 4 & 0x0F
    self.write('%1X' % val)

  def outrhl(self, simstate):
    val = simstate.ucState.A & 0x0F
    self.write('%1X' % val)

  def outcrl(self, simstate): self.write('\n')

  def outa(self, simstate):
    self.write('%c' % simstate.ucState.A)
    sys.stdout.flush()

  def outstr(self, simstate):
    self.write('\n')
    self.outst0(simstate)

  def outst0(self, simstate):
    addr = simstate.ucState.X
    count = 0
    s = ''
    while count < 300:
      c = simstate.ucMemory.readUns8(addr)
      if c == 4: break
      s += chr(c)
      count += 1
      addr += 1
    self.write(s+'\n')
    if count >= 300: self.write("<<<truncated to 300 characters>>>\n")

  def hexbin(self, simstate):
    try:
      val = int(chr(simstate.ucState.A), 16)
    except:
      # 'A' wasn't a hex digit. BUFFALO increments the TMP1
      # location but I don't see the point. The programmer
      # should do the error checking.
      return
    val = (val | (simstate.ucMemory.readUns16(SHFTREG) << 4)) & 0xFFFF
    simstate.ucMemory.writeUns16(SHFTREG, val)

  def chgbyt(self, simstate):
    simstate.ucMemory.writeUns8(simstate.ucState.X, simstate.ucMemory.readUns8(SHFTREG+1))

  def wchek(self, simstate):
    flags = 0
    if chr(simstate.ucState.A) in ' ,\t': flags = CC_Z
    simstate.ucState.setZ(flags)
