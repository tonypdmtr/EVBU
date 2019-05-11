'''
PySim11 -- A simulator engine for the 68HC11
'''

PySim11VersionMajor = 0
PySim11VersionMinor = 5

import sys
import time

from safestruct import *

from PySim11.G import Peripherals
import PySim11.math11 as math11
import PySim11.memory as memory
import PySim11.state as state
import PySim11.ints as ints
import PySim11.ops as ops
import PySim11.asm as asm
from PySim11.ops import IMM8, IMM16, EXT, DIR, INDX, INDY, INH, REL, BIT2DIR, BIT2INDX, BIT2INDY, BIT3DIR, BIT3INDX, BIT3INDY
from PySim11.sysevents import SystemEvents

################################################################################

class ucBreakpoint(SafeStruct,Exception):
  def __init__(self):
    super().__init__({
      'addr': 0xFFFF,
      'text': "Unknown Breakpoint",
      'count': 1,
      'basecount': 1,
      'action': None,
      'autoremove': 0
    })

  def hit(self, simstate):
    allow = 1
    if self.action: allow = self.action(*(self,simstate))
    if allow and self.count > 0:
      self.count -= 1
      if self.count == 0: return 1
    return 0

  def restoreCount(self): self.count = self.basecount

################################################################################

class ucVirtualFunction(SafeStruct):
  def __init__(self, addr=0, func=None, text=""):
    super().__init__({
      'addr': addr,
      'text': text,
      'func': func
    })

################################################################################

class ucPeripheral(SafeStruct):
  def __init__(self, object, text=""):
    super().__init__({
      'object': object,
      'text': text
    })

################################################################################

class SimState(SafeStruct):
  def __init__(self, parentWindow=None, write=sys.stdout.write, breakEvent=None):
    super().__init__({
      'ucState': None,
      'ucMemory': None,
      'ucInterrupts': None,
      'ucEvents': None,
      'BPlist': [],   # Breakpoint list, each entry is an object of ucBreakpoint class
      'VFlist': [],   # Virtual function list, each entry is ucVirtualFunction class
      'PElist': [],   # Peripheral hook list, each entry is a ucPeripheral object
      'mapfile': None, # symbol table and source code map, if present
      'BForce': 0,    # Allows forcing branch instructions in trace mode
      'cycles': 0,
      'parent': parentWindow,
      'write': write,
      'breakEvent': breakEvent   # A threading.Event object used to notify step() it should stop
    })
    self.ucState = state.ucState()
    self.ucMemory = memory.ucMemory()
    self.ucInterrupts = ints.ucInterrupts()
    self.ucEvents = SystemEvents()

    for name, val in Peripherals.items():
      if val[0]:
        print('Installing %s peripheral...' % name)
        exec("import %s" % val[1])
        exec("self.PElist.append(%s.install(self, parentWindow))" % val[1])

  def fetch8(self):
    PC = self.ucState.PC
    val = self.ucMemory.readUns8(PC)
    self.ucState.setPC(PC+1 & 0xFFFF)
    return val

  def fetch16(self):
    PC = self.ucState.PC
    val = self.ucMemory.readUns16(PC)
    self.ucState.setPC(PC+2 & 0xFFFF)
    return val

  def decode(self, mode):
    addr = value = offset = None
    if mode == INH: return ()

    elif mode in [IMM8, IMM16, EXT, DIR, INDX, INDY]:
      if mode == IMM8: value = self.fetch8()
      elif mode == IMM16: value = self.fetch16()
      elif mode == EXT: addr = self.fetch16()
      elif mode == DIR: addr = self.fetch8()
      elif mode == INDX:
        offset = self.fetch8()
        addr = offset + self.ucState.X & 0xFFFF
      elif mode == INDY:
        offset = self.fetch8()
        addr = offset + self.ucState.Y & 0xFFFF
      return (addr, value, offset)

    elif mode == REL:
      addr = math11.TwosC8ToInt(self.fetch8())
      addr = addr + self.ucState.PC & 0xFFFF
      return (addr,)

    elif mode in [BIT2DIR, BIT2INDX, BIT2INDY]:
      if mode == BIT2DIR: addr = self.fetch8()
      elif mode == BIT2INDX:
        offset = self.fetch8()
        addr = offset + self.ucState.X & 0xFFFF
      elif mode == BIT2INDY:
        offset = self.fetch8()
        addr = offset + self.ucState.Y & 0xFFFF
      value = self.fetch8()
      return (addr, value, offset)

    elif mode in [BIT3DIR, BIT3INDX, BIT3INDY]:
      if mode == BIT3DIR: addr = self.fetch8()
      elif mode == BIT3INDX:
        offset = self.fetch8()
        addr = offset + self.ucState.X & 0xFFFF
      elif mode == BIT3INDY:
        offset = self.fetch8()
        addr = offset + self.ucState.Y & 0xFFFF
      value = self.fetch8()
      newpc = math11.TwosC8ToInt(self.fetch8())
      newpc = newpc + self.ucState.PC & 0xFFFF
      return (addr, value, newpc, offset)
    else: raise ops.InternalError('Unknown instruction mode')

  def ifetch(self):
    hipri = self.ucInterrupts.nextInt(self)
    if hipri:
      #print 'Interrupt', hipri, 'pending'
      self.ucState.push16(self.ucMemory, self.ucState.PC)
      self.ucState.push16(self.ucMemory, self.ucState.Y)
      self.ucState.push16(self.ucMemory, self.ucState.X)
      self.ucState.push8(self.ucMemory, self.ucState.A)
      self.ucState.push8(self.ucMemory, self.ucState.B)
      self.ucState.push8(self.ucMemory, self.ucState.CC)
      self.ucState.setI(state.CC_I)
      if hipri == ints.XIRQ: self.ucState.setXbit(state.CC_X)

      self.ucState.setPC(self.ucMemory.readUns16(ints.Vector[hipri]))
    return self.ifetch_raw()

  def ifetch_raw(self):
    opcode = self.fetch8()
    if opcode in ops.PrebyteList: opcode = (opcode, self.fetch8())

    try: instr, mode, cycles = ops.Ops[opcode]
    except: raise ops.IllegalOperation

    return (instr, mode, cycles)

  def iexec(self, instr, mode, cycles, parms):
    if mode == INH: exec("ops.%s(self)" % instr)

    elif mode in [IMM8, IMM16, EXT, DIR, INDX, INDY]:
      exec("ops.%s(self, parms[0], parms[1])" % instr)

    elif mode == REL:
      exec("ops.%s(self, parms[0])" % instr)

    elif mode in [BIT2DIR, BIT2INDX, BIT2INDY]:
      exec("ops.%s(self, parms[0], parms[1])" % instr)

    elif mode in [BIT3DIR, BIT3INDX, BIT3INDY]:
      exec("ops.%s(self, parms[0], parms[1], parms[2])" % instr)

    else: raise ops.InternalError('Unknown instruction mode')

    self.ucInterrupts.flush()
    for periph in self.PElist: exec('periph.object.update(cycles)')

  def printCurrentInstruction(self, instr, mode, parms, PC):
    if self.mapfile:
      try:
        srcline, fname, linenum = self.mapfile.addrmap[PC]
        self.write("%s:%d %04X  %s" % (fname, linenum, PC, srcline))
      except: self.write("<<< No source line found >>>\n")
    self.write(('%-21s' % asm.dasm(instr, mode, parms)))

  def printNextInstruction(self):
    oldPC = self.ucState.PC
    try:
      instr, mode, cycles = self.ifetch_raw()
      parms = self.decode(mode)
    except ops.IllegalOperation:
      instr = 'ILLOP'
      mode = INH
      parms = ()
    self.printCurrentInstruction(instr, mode, parms, oldPC)
    self.write('\n')
    self.ucState.setPC(oldPC)

  def step(self, count = 0, trace = 0, cyclimit = 0, branchForce = 0):
    done = 0
    breakaddrs = {}
    virtsubs = {}

    # We don't want to hit a breakpoint on the first instruction
    # so we use the firstInstruction flag to prevent this.
    firstInstruction = 1

    # Notify subscribers that a simulation is to begin.
    self.ucEvents.notifyEvent(self.ucEvents.SimStart)

    start_clock = time.clock()
    start_cyc = self.cycles

    for br in self.BPlist:
      br.restoreCount()
      breakaddrs[br.addr] = br

    for vs in self.VFlist: virtsubs[vs.addr] = vs.func

    cycthresh = None
    if cyclimit > 0: cycthresh = self.cycles + cyclimit

    while not done:
      PC = self.ucState.PC
      try:
        func = virtsubs[PC]
        try: func(*(self,))
        except Exception as detail:
          if detail: self.write(str(detail)+'\n')
          self.write('\n')
          done = 1
          raise
        newPC = self.ucState.pull16(self.ucMemory)
        self.ucState.setPC(newPC)
      except: func = None
      if func:
        firstInstruction = 0
        continue
      if done: continue       # In case a virtual function raised an exception

      if firstInstruction: self.BForce = branchForce

      try:
        try: br = breakaddrs[PC]
        except: br = None
        if br and not firstInstruction and br.hit(self):
          if br.autoremove: self.BPlist.remove(br)
          raise br
        firstInstruction = 0

        instr, mode, cycles = self.ifetch()

        parms = self.decode(mode)
        if trace: self.printCurrentInstruction(instr, mode, parms, PC)

        # Updating self.cycles *prior* to execution is counted
        # upon by peripheral modules.
        self.cycles += cycles
        try: self.iexec(instr, mode, cycles, parms)
        except:
          if trace: self.write('\n')
          raise
        if trace:
          self.ucState.display(self.write)
          self.write('\n')
          self.printNextInstruction()

      except ucBreakpoint as br:
        if br.text: self.write(br.text+'\n\n')
        done = 1
      except ops.SWIInstruction:
        self.write('SWI instruction encountered\n\n')
        done = 1
      except ops.StopInstruction:
        self.write('STOP instruction encountered\n\n')
        done = 1
      except ops.WaitInstruction:
        self.write('WAI instruction encountered\n\n')
        done = 1
      except ops.TestInstruction:
        self.write('TEST instruction encountered\n\n')
        done = 1
      except ops.IllegalOperation:
        self.write('Illegal instruction encountered\n\n')
        done = 1
      except KeyboardInterrupt:
        self.write('Execution interrupted\n\n')
        done = 1
      except Exception as detail:
        if detail: self.write(str(detail)+'\n\n')
        done = 1
      # end try

      # Branch force only works in trace mode for the first instruction
      self.BForce = 0

      if count:
        count -= 1
        if count == 0: done = 1
      if not done and cyclimit:
        if self.cycles >= cyclimit:
          done = 1
          self.write('Cycle limit exceeded\n')

      if self.breakEvent:
        if not self.breakEvent.isSet():
          done = 1
          self.breakEvent.set()
    # end while

    # Notify subscribers that a simulation ended
    self.ucEvents.notifyEvent(self.ucEvents.SimEnd)

    stop_clock = time.clock()
    stop_cyc = self.cycles

    # Uncomment the following to see how fast the simulator is
    #print (stop_clock-start_clock), 'seconds to compute', (stop_cyc-start_cyc), 'cycles: RTR=',
    #print (stop_clock-start_clock)/((stop_cyc-start_cyc)*0.5e-6)
