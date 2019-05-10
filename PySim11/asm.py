'''
Disassembly of 68HC11 instructions
'''

import PySim11.math11
import PySim11.memory
import PySim11.state
import PySim11.ops
from PySim11.ops import IMM8, IMM16, EXT, DIR, INDX, INDY, INH, REL, BIT2DIR, BIT2INDX, BIT2INDY, BIT3DIR, BIT3INDX, BIT3INDY

def dasm_line(addr, bytes, instr, mode, parms, cycles):
  s= '%04X  ' % addr
  for b in bytes: s += ('%02X ' % b)
  if len(bytes) < 4: s += '   '*(4-len(bytes))
  return s + ('  [%2d]  ' % cycles) + dasm(instr, mode, parms)

def dasm(instr, mode, parms):
  s = '%-6s' % instr
  if mode == IMM8:       s += '#$%02X' % parms[1]
  elif mode == IMM16:    s += '#$%04X' % parms[1]
  elif mode == EXT:      s += '$%04X' % parms[0]
  elif mode == DIR:      s += '$%02X' % parms[0]
  elif mode == INDX:     s += '%d,X' % parms[2]
  elif mode == INDY:     s += '%d,Y' % parms[2]
  elif mode == REL:      s += '$%04X' % parms[0]
  elif mode == BIT2DIR:  s += '$%02X #$%02X' % (parms[0], parms[1])
  elif mode == BIT2INDX: s += '%d,X #$%02X' % (parms[2], parms[1])
  elif mode == BIT2INDY: s += '%d,Y #$%02X' % (parms[2], parms[1])
  elif mode == BIT3DIR:  s += '$%02X #$%02X $%04X' % (parms[0], parms[1], parm[2])
  elif mode == BIT3INDX: s += '%d,X #$%02X $%04X' % (parms[3], parms[1], parms[2])
  elif mode == BIT3INDY: s += '%d,Y #$%02X $%04X' % (parms[3], parms[1], parms[2])
  return s
