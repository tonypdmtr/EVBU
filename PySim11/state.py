'''
This module abstracts the state of the 68HC11
'''

import sys
import string

from safestruct import *

ccbits = 'sxhinzvc'
CC_S = 0x80
CC_X = 0x40
CC_H = 0x20
CC_I = 0x10
CC_N = 0x08
CC_Z = 0x04
CC_V = 0x02
CC_C = 0x01

class ucState(SafeStruct):
  def __init__(self):
    super().__init__({
       'PC': 0,
       'SP': 0,
       'X': 0,
       'Y': 0,
       'A': 0,
       'B': 0,
       'CC': 0x55,
       'PChandlers': [],
       'SPhandlers': [],
       'Xhandlers': [],
       'Yhandlers': [],
       'Ahandlers': [],
       'Bhandlers': [],
       'Dhandlers': [],
       'CChandlers': []
    })

  def display(self, write=None):
    if not write: write = sys.stdout.write
    write('PC-%04X A-%02X B-%02X D-%04X X-%04X Y-%04X SP-%04X CCR-%02X ' % \
         (self.PC, self.A, self.B, self.D(), self.X, self.Y, self.SP, self.CC))

    for bit in range(8):
      c = ccbits[bit]
      if self.CC & 0x80 >> bit: c = c.upper()
      else: c = '.'           #print just a dot for clear bits
      write(f'{c}')

  def setA(self, A):
    for h in self.Ahandlers: h(*self, A)
    self.A = A

  def setB(self, B):
    for h in self.Bhandlers: h(*self, B)
    self.B = B

  def setX(self, X):
    for h in self.Xhandlers: h(*self, X)
    self.X = X

  def setY(self, Y):
    for h in self.Yhandlers: h(*self, Y)
    self.Y = Y

  def setPC(self, PC):
    for h in self.PChandlers: h(*self, PC)
    self.PC = PC

  def setSP(self, SP):
    for h in self.SPhandlers: h(*self, SP)
    self.SP = SP

  def setCC(self, CC):
    for h in self.CChandlers: h(*self, CC)
    self.CC = CC

  def D(self): return self.A*256 + self.B

  def setD(self, D):
    for h in self.Dhandlers: h(*self, D)
    self.A, self.B = divmod(D, 256)

  def setHNZVC(self, flags): self.setCC((self.CC & 0xD0) | flags)
  def setNZVC(self, flags): self.setCC((self.CC & 0xF0) | flags)
  def setNZV(self, flags): self.setCC((self.CC & 0xF1) | flags)
  def setZVC(self, flags): self.setCC((self.CC & 0xF8) | flags)
  def setC(self, flags): self.setCC((self.CC & 0xFE) | flags)
  def setI(self, flags): self.setCC((self.CC & 0xEF) | flags)
  def setV(self, flags): self.setCC((self.CC & 0xFD) | flags)
  def setZ(self, flags): self.setCC((self.CC & 0xFB) | flags)
  def setXbit(self, flags): self.setCC((self.CC & 0xBF) | flags)

  def isCarrySet(self): return 1 if self.CC & CC_C else 0
  def isZeroSet(self): return 1 if self.CC & CC_Z else 0
  def isNegativeSet(self): return 1 if self.CC & CC_N else 0
  def isOverflowSet(self): return 1 if self.CC & CC_V else 0
  def isStopSet(self): return 1 if self.CC & CC_S else 0
  def isHalfSet(self): return 1 if self.CC & CC_H else 0
  def isXSet(self): return 1 if self.CC & CC_X else 0
  def isISet(self): return 1 if self.CC & CC_I else 0

  def push8(self, memory, data):
    memory.writeUns8(self.SP, data)
    self.setSP((self.SP-1) & 0xFFFF)

  def push16(self, memory, data):
    ea = (self.SP-1) & 0xFFFF
    memory.writeUns16(ea, data)
    self.setSP((self.SP - 2) & 0xFFFF)

  def pull8(self, memory):
    self.setSP((self.SP+1) & 0xFFFF)
    return memory.readUns8(self.SP)

  def pull16(self, memory):
    ea = (self.SP+1) & 0xFFFF
    self.setSP((self.SP+2) & 0xFFFF)
    return memory.readUns16(ea)
