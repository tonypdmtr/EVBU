'''
Abstraction for 16-bit addressed 8-bit data memory of 68HC11
'''

import sys
import string
import operator

from safestruct import *

import PySim11.math11

printableInts = {}
map(operator.setitem, [printableInts]*len(string.printable), \
                       map(ord, string.printable), [1]*len(string.printable))

# These define the offsets of special registers from the register
# base address. The third entry is the register value at reset. This
# isn't quite correct as some registers and bits are unaffected by reset.
RegBaseOffsets = (
  ('PORTA', 0x00, 0x00),
  ('PIOC',  0x02, 0x03),
  ('PORTC', 0x03, 0x00),
  ('PORTB', 0x04, 0x00),
  ('PORTCL',0x05, 0x00),
  ('DDRC',  0x07, 0x00),
  ('PORTD', 0x08, 0x00),
  ('DDRD',  0x09, 0x00),
  ('PORTE', 0x0A, 0x00),
  ('CFORC', 0x0B, 0x00),
  ('OC1M',  0x0C, 0x00),
  ('OC1D',  0x0D, 0x00),
  ('TCNT',  0x0E, 0x00),
  ('TIC1',  0x10, 0x00),
  ('TIC2',  0x12, 0x00),
  ('TIC3',  0x14, 0x00),
  ('TOC1',  0x16, 0x00),
  ('TOC2',  0x18, 0x00),
  ('TOC3',  0x1A, 0x00),
  ('TOC4',  0x1C, 0x00),
  ('TOC5',  0x1E, 0x00),      # Note duplication of TOC5/TIC4
  ('TIC4',  0x1E, 0x00),
  ('TCTL1', 0x20, 0x00),
  ('TCTL2', 0x21, 0x00),
  ('TMSK1', 0x22, 0x00),
  ('TFLG1', 0x23, 0x00),
  ('TMSK2', 0x24, 0x00),
  ('TFLG2', 0x25, 0x00),
  ('PACTL', 0x26, 0x00),
  ('PACNT', 0x27, 0x00),
  ('SPCR',  0x28, 0x04),
  ('SPSR',  0x29, 0x00),
  ('SPDR',  0x2A, 0x00),
  ('BAUD',  0x2B, 0x00),
  ('SCCR1', 0x2C, 0x00),
  ('SCCR2', 0x2D, 0x00),
  ('SCSR',  0x2E, 0xC0),
  ('ADCTL', 0x30, 0x80),
  ('ADR1',  0x31, 0x00),
  ('ADR2',  0x32, 0x00),
  ('ADR3',  0x33, 0x00),
  ('ADR4',  0x34, 0x00),
  ('BPROT', 0x35, 0x1F),
  ('EPROG', 0x36, 0x00),
  ('OPTION',0x39, 0x10),
  ('COPRST',0x3A, 0x00),
  ('PPROG', 0x3B, 0x00),
  ('HPRIO', 0x3C, 0x06),
  ('INIT',  0x3D, 0x01),
  ('TEST1', 0x3E, 0x00),
  ('CONFIG',0x3F, 0x02)
  )

# This class filters out accesses to a range of memory
# addresses and calls any handlers that may care.
class ucMemoryFilter(SafeStruct):
  def __init__(self, low=0, high=65535, rwh=None, roh=None, woh=None):
    super().__init__({
        'ALow': low,
        'AHigh': high,
        'RWHandler': rwh,          # Read/write handler
        'ROHandler': roh,          # Read/only handler
        'WOHandler': woh           # Write/only handler
      })

class ucMemory(SafeStruct):
  def __init__(self):
    super().__init__({
        'LowLimit': 0,
        'HighLimit': 65535,
        'Array': [0]*65536,
        'Filters': [],
        'FilterAddressHash': {},
        'RegBase': 0x1000
      })
    self.mapRegisters()
    self.reset()
    self.addFilter(ucMemoryFilter(self.INIT, self.INIT, None, self.readINIT, self.writeINIT))

  def reset(self):
    for regname, offset, resetval in RegBaseOffsets:
      self.Array[0x1000 + offset] = resetval

  # This function reassigns the special register addresses. It
  # also searches through all the special memory filters installed
  # and remaps the addresses of all filters that fall into the old
  # register base. It is assumed that these filters support
  # peripherals and they do not cross over the register space
  # boundary.
  def mapRegisters(self, base=0x1000):
    oldLow = self.RegBase
    oldHigh = oldLow + 0x3F
    self.FilterAddressHash = {}
    for f in self.Filters:
      if oldLow <= f.ALow <= oldHigh:
        f.ALow += base - oldLow
        f.AHigh += base - oldLow
        for addr in range(f.ALow, f.AHigh+1):
          try: self.FilterAddressHash[addr].append(f)
          except: self.FilterAddressHash[addr] = [f]

    self.RegBase = base

    regdict = {}
    for regname, offset, resetval in RegBaseOffsets:
      regdict[regname] = base + offset
    self.add_attributes(regdict)

    if oldLow != base:
      self.Array[base:base+0x40] = self.Array[oldLow:oldLow+0x40]
      self.Array[oldLow:oldLow+0x40] = [0]*0x40

  def readINIT(self, addr, bits, val, rw):
    val = self.readRawUns8(self.INIT) & 0xF0
    val = val | (self.RegBase & 0xF000) >> 12
    self.writeRawUns8(self.INIT, val)

  def writeINIT(self, addr, bits, val, rw):
    # Doesn't take into account restriction that this can only occur
    # within 64 cycles of reset.
    newBase = (val & 0x0F) << 12
    self.mapRegisters(newBase)

  def addFilter(self, f):
    self.Filters.append(f)
    for addr in range (f.ALow, f.AHigh+1):
      try: self.FilterAddressHash[addr].append(f)
      except: self.FilterAddressHash[addr] = [f]

  def _applyReadHandlers(self, addr, bits):
    handlers = self.FilterAddressHash[addr]

    for f in handlers:
      if f.RWHandler:
        f.RWHandler(*(addr, bits, 0, 0)) # The last 0 indicates READ

      if f.ROHandler:
        f.ROHandler(*(addr, bits, 0, 0)) # The last 0 indicates READ

  def _applyWriteHandlers(self, addr, bits, val):
    handlers = self.FilterAddressHash[addr]

    for f in handlers:
      if f.RWHandler: f.RWHandler(*(addr, bits, val, 1)) # The last 1 indicates WRITE
      if f.WOHandler: f.WOHandler(*(addr, bits, val, 1)) # The last 1 indicates WRITE

  def readRawTuple8(self, addrLo, addrHi):
    assert self.LowLimit <= addrLo <= addrHi <= self.HighLimit
    return tuple(self.Array[addrLo:(addrHi+1)])

  def readUns8(self, addr):
    assert self.LowLimit <= addr <= self.HighLimit

    if addr in self.FilterAddressHash: self._applyReadHandlers(addr, 8)
    return self.Array[addr]

  def readSgn8(self, addr):
    assert self.LowLimit <= addr <= self.HighLimit

    if addr in self.FilterAddressHash: self._applyReadHandlers(addr, 8)
    return math11.TwosC8ToInt(self.Array[addr])

  def readUns16(self, addr):
    assert self.LowLimit <= addr <= self.HighLimit

    if addr in self.FilterAddressHash: self._applyReadHandlers(addr, 16)
    if addr < self.HighLimit: val = (self.Array[addr]<<8) + self.Array[addr+1]
    else: val = (self.Array[addr]<<8) + self.Array[0]
    return val

  def readSgn16(self, addr):
    assert self.LowLimit <= addr <= self.HighLimit

    if addr in self.FilterAddressHash: self._applyReadHandlers(addr, 16)
    if addr < self.HighLimit: val = (self.Array[addr]<<8) + self.Array[addr+1]
    else: val = (self.Array[addr]<<8) + self.Array[0]
    return math11.TwosC16ToInt(val)

  def readRawUns8(self, addr):
    assert self.LowLimit <= addr <= self.HighLimit

    return self.Array[addr]

  def readRawSgn8(self, addr):
    assert self.LowLimit <= addr <= self.HighLimit

    return math11.TwosC8ToInt(self.Array[addr])

  def readRawUns16(self, addr):
    assert self.LowLimit <= addr <= self.HighLimit

    if addr < self.HighLimit: val = (self.Array[addr]<<8) + self.Array[addr+1]
    else: val = (self.Array[addr]<<8) + self.Array[0]
    return val

  def readRawSgn16(self, addr):
    assert self.LowLimit <= addr <= self.HighLimit

    if addr < self.HighLimit: val = (self.Array[addr]<<8) + self.Array[addr+1]
    else: val = (self.Array[addr]<<8) + self.Array[0]
    return math11.TwosC16ToInt(val)

  def writeUns8(self, addr, val):
    assert self.LowLimit <= addr <= self.HighLimit
    assert 0 <= val <= 255

    if addr in self.FilterAddressHash: self._applyWriteHandlers(addr, 8, val)
    self.Array[addr] = val

  def writeSgn8(self, addr, val):
    assert self.LowLimit <= addr <= self.HighLimit
    assert -128 <= val <= 127

    if addr in self.FilterAddressHash: self._applyWriteHandlers(addr, 8, val)
    self.Array[addr] = math11.IntToTwosC8(val)

  def writeUns16(self, addr, val):
    assert self.LowLimit <= addr <= self.HighLimit
    assert 0 <= val <= 65535

    if addr in self.FilterAddressHash: self._applyWriteHandlers(addr, 16, val)
    self.Array[addr] = val >> 8
    if addr < self.HighLimit: self.Array[addr+1] = val & 0xFF
    else: self.Array[0] = val & 0xFF

  def writeSgn16(self, addr, val):
    assert self.LowLimit <= addr <= self.HighLimit
    assert -32768 <= val <= 32767

    if addr in self.FilterAddressHash: self._applyWriteHandlers(addr, 16, val)
    val = math11.IntToTwosC16(val)
    self.Array[addr] = val >> 8
    if addr < self.HighLimit: self.Array[addr+1] = val & 0xFF
    else: self.Array[0] = val & 0xFF

  def writeRawUns8(self, addr, val):
    assert self.LowLimit <= addr <= self.HighLimit
    assert 0 <= val <= 255

    self.Array[addr] = val

  def writeRawSgn8(self, addr, val):
    assert self.LowLimit <= addr <= self.HighLimit
    assert -128 <= val <= 127

    self.Array[addr] = math11.IntToTwosC8(val)

  def writeRawUns16(self, addr, val):
    assert self.LowLimit <= addr <= self.HighLimit
    assert 0 <= val <= 65535

    self.Array[addr] = val >> 8
    if addr < self.HighLimit: self.Array[addr+1] = val & 0xFF
    else: self.Array[0] = val & 0xFF

  def writeRawSgn16(self, addr, val):
    assert self.LowLimit <= addr <= self.HighLimit
    assert -32768 <= val <= 32767

    val = math11.IntToTwosC16(val)
    self.Array[addr] = val >> 8
    if addr < self.HighLimit: self.Array[addr+1] = val & 0xFF
    else: self.Array[0] = val & 0xFF

  def displayAscii(self, skip, addrLow, addrHigh, write):
    if skip: write(' '*skip)

    for addr in range(addrLow, addrHigh):
      val = self.readUns8(addr)
      if val not in printableInts: val = ord('.')
      write('%c' % val)

  def display8(self, addrLow, addrHigh, write = None):
    if not write: write = sys.stdout.write
    assert self.LowLimit <= addrLow <= addrHigh <= self.HighLimit

    initix = ix = addrLow % 16

    write('%04X: ' % addrLow)
    if ix: write(' ' * ix*3)

    beginAddr = addrLow
    while addrLow <= addrHigh:
      write('%02X ' % self.readUns8(addrLow))
      addrLow += 1
      ix += 1
      if ix == 16:
        write('| ')
        self.displayAscii(initix, beginAddr, addrLow, write)
        initix = 0

        write('\n')
        ix = 0
        beginAddr = addrLow

        if addrLow <= addrHigh: write('%04X: ' % addrLow)

    if ix:
      write(' ' * (16-ix)*3)
      write('| ')
      self.displayAscii(initix, beginAddr, addrLow, write)
      write('\n')
