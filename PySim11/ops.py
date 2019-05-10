'''
68HC11 instruction set implementation
'''

from PySim11.G import UseSWI
from PySim11.state import CC_S, CC_X, CC_I, CC_H, CC_N, CC_V, CC_Z, CC_C
from PySim11 import BFORCE_ALWAYS,BFORCE_NEVER

IMM8 = 1          # Immediate mode: 8-bit data
IMM16 = 2         # Immediate mode: 16-bit data
EXT = 4           # Extended mode
DIR = 8           # Direct mode
INDX = 16         # Indexed/X mode
INDY = 32         # Indexed/Y mode
INH = 64          # Inherent mode
REL = 128         # Relative mode
BIT2DIR = 256     # BCLR/BSET Direct mode
BIT2INDX = 512    # BCLR/BSET INDX mode
BIT2INDY = 1024   # BCLR/BSET INDY mode
BIT3DIR = 2048    # BRCLR/BRSET Direct mode
BIT3INDX = 4096   # BRCLR/BRSET INDX mode
BIT3INDY = 8192   # BRCLR/BRSET INDY mode

# These are exceptions that are raised when the given instruction
# executes
class StopInstruction(Exception): pass
class WaitInstruction(Exception): pass
class SWIInstruction(Exception): pass
class TestInstruction(Exception): pass
class IllegalOperation(Exception): pass
class InternalError(Exception): pass
class UnhandledInterrupt(Exception):   pass

PrebyteList = [0x18, 0x1A, 0xCD]

Ops = {
 0x00: ('TEST',  INH,     1),
 0x01: ('NOP',   INH,     2),
 0x02: ('IDIV',  INH,     41),
 0x03: ('FDIV',  INH,     41),
 0x04: ('LSRD',  INH,     3),
 0x05: ('LSLD',  INH,     3),    # aka ASLD
 0x06: ('TAP',   INH,     2),
 0x07: ('TPA',   INH,     2),
 0x08: ('INX',   INH,     3),
 0x09: ('DEX',   INH,     3),
 0x0A: ('CLV',   INH,     2),
 0x0B: ('SEV',   INH,     2),
 0x0C: ('CLC',   INH,     2),
 0x0D: ('SEC',   INH,     2),
 0x0E: ('CLI',   INH,     2),
 0x0F: ('SEI',   INH,     2),
 0x10: ('SBA',   INH,     2),
 0x11: ('CBA',   INH,     2),
 0x12: ('BRSET', BIT3DIR, 6),
 0x13: ('BRCLR', BIT3DIR, 6),
 0x14: ('BSET',  BIT2DIR, 6),
 0x15: ('BCLR',  BIT2DIR, 6),
 0x16: ('TAB',   INH,     2),
 0x17: ('TBA',   INH,     2),

 0x19: ('DAA',   INH,     2),

 0x1B: ('ABA',   INH,     2),
 0x1C: ('BSET',  BIT2INDX, 7),
 0x1D: ('BCLR',  BIT2INDX, 7),
 0x1E: ('BRSET', BIT3INDX, 7),
 0x1F: ('BRCLR', BIT3INDX, 7),
 0x20: ('BRA',   REL,      3),
 0x21: ('BRN',   REL,      3),
 0x22: ('BHI',   REL,      3),
 0x23: ('BLS',   REL,      3),
 0x24: ('BHS',   REL,      3),   # aka BCC
 0x25: ('BLO',   REL,      3),   # aka BCS
 0x26: ('BNE',   REL,      3),
 0x27: ('BEQ',   REL,      3),
 0x28: ('BVC',   REL,      3),
 0x29: ('BVS',   REL,      3),
 0x2A: ('BPL',   REL,      3),
 0x2B: ('BMI',   REL,      3),
 0x2C: ('BGE',   REL,      3),
 0x2D: ('BLT',   REL,      3),
 0x2E: ('BGT',   REL,      3),
 0x2F: ('BLE',   REL,      3),
 0x30: ('TSX',   INH,      3),
 0x31: ('INS',   INH,      3),
 0x32: ('PULA',  INH,      4),
 0x33: ('PULB',  INH,      4),
 0x34: ('DES',   INH,      3),
 0x35: ('TXS',   INH,      3),
 0x36: ('PSHA',  INH,      3),
 0x37: ('PSHB',  INH,      3),
 0x38: ('PULX',  INH,      5),
 0x39: ('RTS',   INH,      5),
 0x3A: ('ABX',   INH,      3),
 0x3B: ('RTI',   INH,      12),
 0x3C: ('PSHX',  INH,      4),
 0x3D: ('MUL',   INH,      10),
 0x3E: ('WAI',   INH,      1),
 0x3F: ('SWI',   INH,      14),
 0x40: ('NEGA',  INH,      2),
 0x43: ('COMA',  INH,      2),
 0x44: ('LSRA',  INH,      2),
 0x46: ('RORA',  INH,      2),
 0x47: ('ASRA',  INH,      2),
 0x48: ('ASLA',  INH,      2),   # aka LSLA
 0x49: ('ROLA',  INH,      2),
 0x4A: ('DECA',  INH,      2),
 0x4C: ('INCA',  INH,      2),
 0x4D: ('TSTA',  INH,      2),
 0x4F: ('CLRA',  INH,      2),
 0x50: ('NEGB',  INH,      2),
 0x53: ('COMB',  INH,      2),
 0x54: ('LSRB',  INH,      2),
 0x56: ('RORB',  INH,      2),
 0x57: ('ASRB',  INH,      2),
 0x58: ('ASLB',  INH,      2),   # aka LSLB
 0x59: ('ROLB',  INH,      2),
 0x5A: ('DECB',  INH,      2),
 0x5C: ('INCB',  INH,      2),
 0x5D: ('TSTB',  INH,      2),
 0x5F: ('CLRB',  INH,      2),
 0x60: ('NEG',   INDX,     6),
 0x63: ('COM',   INDX,     6),
 0x64: ('LSR',   INDX,     6),
 0x66: ('ROR',   INDX,     6),
 0x67: ('ASR',   INDX,     6),
 0x68: ('ASL',   INDX,     6),   # aka LSL
 0x69: ('ROL',   INDX,     6),
 0x6A: ('DEC',   INDX,     6),
 0x6C: ('INC',   INDX,     6),
 0x6D: ('TST',   INDX,     6),
 0x6E: ('JMP',   INDX,     3),
 0x6F: ('CLR',   INDX,     6),
 0x70: ('NEG',   EXT,      6),
 0x73: ('COM',   EXT,      6),
 0x74: ('LSR',   EXT,      6),
 0x76: ('ROR',   EXT,      6),
 0x77: ('ASR',   EXT,      6),
 0x78: ('ASL',   EXT,      6),   # aka LSL
 0x79: ('ROL',   EXT,      6),
 0x7A: ('DEC',   EXT,      6),
 0x7C: ('INC',   EXT,      6),
 0x7D: ('TST',   EXT,      6),
 0x7E: ('JMP',   EXT,      3),
 0x7F: ('CLR',   EXT,      6),
 0x80: ('SUBA',  IMM8,     2),
 0x81: ('CMPA',  IMM8,     2),
 0x82: ('SBCA',  IMM8,     2),
 0x83: ('SUBD',  IMM16,    4),
 0x84: ('ANDA',  IMM8,     2),
 0x85: ('BITA',  IMM8,     2),
 0x86: ('LDAA',  IMM8,     2),
 0x88: ('EORA',  IMM8,     2),
 0x89: ('ADCA',  IMM8,     2),
 0x8A: ('ORAA',  IMM8,     2),
 0x8B: ('ADDA',  IMM8,     2),
 0x8C: ('CPX',   IMM16,    4),
 0x8D: ('BSR',   REL,      6),
 0x8E: ('LDS',   IMM16,    3),
 0x8F: ('XGDX',  INH,      3),
 0x90: ('SUBA',  DIR,      3),
 0x91: ('CMPA',  DIR,      3),
 0x92: ('SBCA',  DIR,      3),
 0x93: ('SUBD',  DIR,      5),
 0x94: ('ANDA',  DIR,      3),
 0x95: ('BITA',  DIR,      3),
 0x96: ('LDAA',  DIR,      3),
 0x97: ('STAA',  DIR,      3),
 0x98: ('EORA',  DIR,      3),
 0x99: ('ADCA',  DIR,      3),
 0x9A: ('ORAA',  DIR,      3),
 0x9B: ('ADDA',  DIR,      3),
 0x9C: ('CPX',   DIR,      5),
 0x9D: ('JSR',   DIR,      5),
 0x9E: ('LDS',   DIR,      4),
 0x9F: ('STS',   DIR,      4),
 0xA0: ('SUBA',  INDX,     4),
 0xA1: ('CMPA',  INDX,     4),
 0xA2: ('SBCA',  INDX,     4),
 0xA3: ('SUBD',  INDX,     6),
 0xA4: ('ANDA',  INDX,     4),
 0xA5: ('BITA',  INDX,     4),
 0xA6: ('LDAA',  INDX,     4),
 0xA7: ('STAA',  INDX,     4),
 0xA8: ('EORA',  INDX,     4),
 0xA9: ('ADCA',  INDX,     4),
 0xAA: ('ORAA',  INDX,     4),
 0xAB: ('ADDA',  INDX,     4),
 0xAC: ('CPX',   INDX,     6),
 0xAD: ('JSR',   INDX,     6),
 0xAE: ('LDS',   INDX,     5),
 0xAF: ('STS',   INDX,     5),
 0xB0: ('SUBA',  EXT,      4),
 0xB1: ('CMPA',  EXT,      4),
 0xB2: ('SBCA',  EXT,      4),
 0xB3: ('SUBD',  EXT,      6),
 0xB4: ('ANDA',  EXT,      4),
 0xB5: ('BITA',  EXT,      4),
 0xB6: ('LDAA',  EXT,      4),
 0xB7: ('STAA',  EXT,      4),
 0xB8: ('EORA',  EXT,      4),
 0xB9: ('ADCA',  EXT,      4),
 0xBA: ('ORAA',  EXT,      4),
 0xBB: ('ADDA',  EXT,      4),
 0xBC: ('CPX',   EXT,      6),
 0xBD: ('JSR',   EXT,      6),
 0xBE: ('LDS',   EXT,      5),
 0xBF: ('STS',   EXT,      5),
 0xC0: ('SUBB',  IMM8,     2),
 0xC1: ('CMPB',  IMM8,     2),
 0xC2: ('SBCB',  IMM8,     2),
 0xC3: ('ADDD',  IMM16,    4),
 0xC4: ('ANDB',  IMM8,     2),
 0xC5: ('BITB',  IMM8,     2),
 0xC6: ('LDAB',  IMM8,     2),
 0xC8: ('EORB',  IMM8,     2),
 0xC9: ('ADCB',  IMM8,     2),
 0xCA: ('ORAB',  IMM8,     2),
 0xCB: ('ADDB',  IMM8,     2),
 0xCC: ('LDD',   IMM16,    3),

 0xCE: ('LDX',   IMM16,    3),
 0xCF: ('STOP',  INH,      2),
 0xD0: ('SUBB',  DIR,      3),
 0xD1: ('CMPB',  DIR,      3),
 0xD2: ('SBCB',  DIR,      3),
 0xD3: ('ADDD',  DIR,      5),
 0xD4: ('ANDB',  DIR,      3),
 0xD5: ('BITB',  DIR,      3),
 0xD6: ('LDAB',  DIR,      3),
 0xD7: ('STAB',  DIR,      3),
 0xD8: ('EORB',  DIR,      3),
 0xD9: ('ADCB',  DIR,      3),
 0xDA: ('ORAB',  DIR,      3),
 0xDB: ('ADDB',  DIR,      3),
 0xDC: ('LDD',   DIR,      4),
 0xDD: ('STD',   DIR,      4),
 0xDE: ('LDX',   DIR,      4),
 0xDF: ('STX',   DIR,      4),
 0xE0: ('SUBB',  INDX,     4),
 0xE1: ('CMPB',  INDX,     4),
 0xE2: ('SBCB',  INDX,     4),
 0xE3: ('ADDD',  INDX,     6),
 0xE4: ('ANDB',  INDX,     4),
 0xE5: ('BITB',  INDX,     4),
 0xE6: ('LDAB',  INDX,     4),
 0xE7: ('STAB',  INDX,     4),
 0xE8: ('EORB',  INDX,     4),
 0xE9: ('ADCB',  INDX,     4),
 0xEA: ('ORAB',  INDX,     4),
 0xEB: ('ADDB',  INDX,     4),
 0xEC: ('LDD',   INDX,     5),
 0xED: ('STD',   INDX,     5),
 0xEE: ('LDX',   INDX,     5),
 0xEF: ('STX',   INDX,     5),
 0xF0: ('SUBB',  EXT,      4),
 0xF1: ('CMPB',  EXT,      4),
 0xF2: ('SBCB',  EXT,      4),
 0xF3: ('ADDD',  EXT,      6),
 0xF4: ('ANDB',  EXT,      4),
 0xF5: ('BITB',  EXT,      4),
 0xF6: ('LDAB',  EXT,      4),
 0xF7: ('STAB',  EXT,      4),
 0xF8: ('EORB',  EXT,      4),
 0xF9: ('ADCB',  EXT,      4),
 0xFA: ('ORAB',  EXT,      4),
 0xFB: ('ADDB',  EXT,      4),
 0xFC: ('LDD',   EXT,      5),
 0xFD: ('STD',   EXT,      5),
 0xFE: ('LDX',   EXT,      5),
 0xFF: ('STX',   EXT,      5),

 (0x18, 0x08): ('INY',  INH,  4),
 (0x18, 0x09): ('DEY',  INH,  4),
 (0x18, 0x1C): ('BSET', BIT2INDY, 8),
 (0x18, 0x1D): ('BCLR', BIT2INDY, 8),
 (0x18, 0x1E): ('BRSET', BIT3INDY, 8),
 (0x18, 0x1F): ('BRCLR', BIT3INDY, 8),
 (0x18, 0x30): ('TSY',  INH,  4),
 (0x18, 0x35): ('TYS',  INH,  4),
 (0x18, 0x38): ('PULY', INH,  6),
 (0x18, 0x3A): ('ABY',  INH,  4),
 (0x18, 0x3C): ('PSHY', INH,  5),
 (0x18, 0x60): ('NEG',  INDY, 7),
 (0x18, 0x63): ('COM',  INDY, 7),
 (0x18, 0x64): ('LSR',  INDY, 7),
 (0x18, 0x66): ('ROR',  INDY, 7),
 (0x18, 0x67): ('ASR',  INDY, 7),
 (0x18, 0x68): ('ASL',  INDY, 7),  # aka LSL
 (0x18, 0x69): ('ROL',  INDY, 7),
 (0x18, 0x6A): ('DEC',  INDY, 7),
 (0x18, 0x6C): ('INC',  INDY, 7),
 (0x18, 0x6D): ('TST',  INDY, 7),
 (0x18, 0x6E): ('JMP',  INDY, 4),
 (0x18, 0x6F): ('CLR',  INDY, 7),
 (0x18, 0x8C): ('CPY',  IMM16,5),
 (0x18, 0x8F): ('XGDY', INH,  4),
 (0x18, 0x9C): ('CPY',  DIR,  6),
 (0x18, 0xA0): ('SUBA', INDY, 5),
 (0x18, 0xA1): ('CMPA', INDY, 5),
 (0x18, 0xA2): ('SBCA', INDY, 5),
 (0x18, 0xA3): ('SUBD', INDY, 7),
 (0x18, 0xA4): ('ANDA', INDY, 5),
 (0x18, 0xA5): ('BITA', INDY, 5),
 (0x18, 0xA6): ('LDAA', INDY, 5),
 (0x18, 0xA7): ('STAA', INDY, 5),
 (0x18, 0xA8): ('EORA', INDY, 5),
 (0x18, 0xA9): ('ADCA', INDY, 5),
 (0x18, 0xAA): ('ORAA', INDY, 5),
 (0x18, 0xAB): ('ADDA', INDY, 5),
 (0x18, 0xAC): ('CPY',  INDY, 7),
 (0x18, 0xAD): ('JSR',  INDY, 7),
 (0x18, 0xAE): ('LDS',  INDY, 6),
 (0x18, 0xAF): ('STS',  INDY, 6),
 (0x18, 0xBC): ('CPY',  EXT,  7),
 (0x18, 0xCE): ('LDY',  IMM16,4),
 (0x18, 0xDE): ('LDY',  DIR,  5),
 (0x18, 0xDF): ('STY',  DIR,  5),
 (0x18, 0xE0): ('SUBB', INDY, 5),
 (0x18, 0xE1): ('CMPB', INDY, 5),
 (0x18, 0xE2): ('SBCB', INDY, 5),
 (0x18, 0xE3): ('ADDD', INDY, 7),
 (0x18, 0xE4): ('ANDB', INDY, 5),
 (0x18, 0xE5): ('BITB', INDY, 5),
 (0x18, 0xE6): ('LDAB', INDY, 5),
 (0x18, 0xE7): ('STAB', INDY, 5),
 (0x18, 0xE8): ('EORB', INDY, 5),
 (0x18, 0xE9): ('ADCB', INDY, 5),
 (0x18, 0xEA): ('ORAB', INDY, 5),
 (0x18, 0xEB): ('ADDB', INDY, 5),
 (0x18, 0xEC): ('LDD',  INDY, 6),
 (0x18, 0xED): ('STD',  INDY, 6),
 (0x18, 0xEE): ('LDY',  INDY, 6),
 (0x18, 0xEF): ('STY',  INDY, 6),
 (0x18, 0xFE): ('LDY',  EXT,  6),
 (0x18, 0xFF): ('STY',  EXT,  6),

 (0x1A, 0x83): ('CPD',  IMM16,5),
 (0x1A, 0x93): ('CPD',  DIR,  6),
 (0x1A, 0xA3): ('CPD',  INDX, 7),
 (0x1A, 0xAC): ('CPY',  INDX, 7),
 (0x1A, 0xB3): ('CPD',  EXT,  7),
 (0x1A, 0xEE): ('LDY',  INDX, 6),
 (0x1A, 0xEF): ('STY',  INDX, 6),

 (0xCD, 0xA3): ('CPD',  INDY, 7),
 (0xCD, 0xAC): ('CPX',  INDY, 7),
 (0xCD, 0xEE): ('LDX',  INDY, 6),
 (0xCD, 0xEF): ('STX',  INDY, 6)
 }

def add8(u1, u2):
  'Add two 8-bit numbers together and set flags'
  flags = 0
  result = u1+u2
  if result & 0xFF != result: flags |= CC_C
  if result & 0x80: flags |= CC_N
  if not result & 0xFF: flags |= CC_Z
  if (u1 & u2 | u1 & ~result | u2 & ~result) & 0x08:
    flags |= CC_H
  if (u1 & u2 & ~result | ~u1 & ~u2 & result) & 0x80:
    flags |= CC_V
  return (result & 0xFF, flags)

def sub8(u1, u2):
  "Subtract two 8-bit numbers together and set flags"
  flags = 0
  result = u1-u2
  if result & 0xFF != result: flags |= CC_C
  if result & 0x80: flags |= CC_N
  if not result & 0xFF: flags |= CC_Z
  if (u1 & ~u2 & ~result | ~u1 & u2 & result) & 0x80:
    flags |= CC_V
  return (result & 0xFF, flags)

def add16(u1, u2):
  "Add two 16-bit numbers together and set flags"
  flags = 0
  result = u1+u2
  if result & 0xFFFF != result: flags |= CC_C
  if result & 0x8000: flags |= CC_N
  if not result & 0xFFFF: flags |= CC_Z
  if (u1 & u2 & ~result | ~u1 & ~u2 & result) & 0x8000:
    flags |= CC_V
  return (result & 0xFFFF, flags)

def sub16(u1, u2):
  "Subtract two 16-bit numbers together and set flags"
  flags = 0
  result = u1-u2
  if result & 0xFFFF != result: flags |= CC_C
  if result & 0x8000: flags |= CC_N
  if not result & 0xFFFF: flags |= CC_Z
  if (u1 & ~u2 & ~result | ~u1 & u2 & result) & 0x8000:
    flags |= CC_V
  return (result & 0xFFFF, flags)

def and8(u1, u2):
  "Logically AND two 8-bit numbers together and set flags"
  flags = 0
  result = u1 & u2
  if result & 0x80: flags |= CC_N
  if not result & 0xFF: flags |= CC_Z
  # V flag is cleared
  return (result & 0xFF, flags)

def or8(u1, u2):
  "Logically OR two 8-bit numbers together and set flags"
  flags = 0
  result = (u1 | u2) & 0xFF
  if result & 0x80: flags |= CC_N
  if result == 0x00: flags |= CC_Z
  return (result, flags)

def asl8(val):
  "Shift left 8 bit value and set flags"
  result = val << 1
  n = c = flags = 0
  if result & 0x80:
    flags |= CC_N
    n=1
  if not result & 0xFF: flags |= CC_Z
  if val & 0x80:
    flags |= CC_C
    c=1
  if n ^ c: flags |= CC_V
  return (result & 0xFF, flags)

def asr8(val):
  "Shift right 8 bit value and set flags"
  result = (val & 0xFF) >> 1 | val & 0x80
  n = c = flags = 0
  if result & 0x80:
    flags |= CC_N
    n=1
  if not result & 0xFF: flags |= CC_Z
  if val & 0x01:
    flags |= CC_C
    c=1
  if n ^ c: flags |= CC_V
  return (result & 0xFF, flags)

def lsr8(val):
  "Logical shift right 8 bit value and set flags"
  result = (val & 0xFF) >> 1
  flags = 0
  if not result & 0xFF: flags |= CC_Z
  if val & 0x01: flags |= CC_C | CC_V
  return (result & 0xFF, flags)

def asl16(val):
  "Shift left 16 bit value and set flags"
  result = val << 1
  n = c = flags = 0
  if result & 0x8000:
    flags |= CC_N
    n=1
  if not result & 0xFFFF: flags |= CC_Z
  if val & 0x8000:
    flags |= CC_C
    c=1
  if n ^ c: flags |= CC_V
  return (result & 0xFFFF, flags)

def lsr16(val):
  "Logical shift right 16 bit value and set flags"
  result = (val & 0xFFFF) >> 1
  flags = 0
  if not result & 0xFFFF: flags |= CC_Z
  if val & 0x0001: flags |= CC_C | CC_V
  return (result & 0xFFFF, flags)

def rol8(val, carry):
  "Rotate left 8 bit value and set flags"
  result = (val << 1 | carry) & 0xFF
  n = c = flags = 0
  if result & 0x80:
    flags |= CC_N
    n=1
  if result == 0: flags |= CC_Z
  if val & 0x80:
    flags |= CC_C
    c=1
  if n ^ c: flags |= CC_V
  return (result, flags)

def ror8(val, carry):
  "Rotate right 8 bit value and set flags"
  result = (val >> 1 | carry * 0x80) & 0xFF
  n = c = flags = 0
  if result & 0x80:
    flags |= CC_N
    n=1
  if result == 0: flags |= CC_Z
  if val & 0x01:
    flags |= CC_C
    c=1
  if n ^ c: flags |= CC_V
  return (result, flags)

def neg8(val):
  "Two's complement negative of 8-bit integer"
  result = -val & 0xFF
  flags = 0
  if result & 0x80: flags |= CC_N
  if result == 0: flags |= CC_Z
  if result == 0x80: flags |= CC_V
  if result != 0x00: flags |= CC_C
  return (result, flags)

def testNZ8(val):
  flags = 0
  if val & 0x80: flags |= CC_N
  if not val & 0xFF: flags |= CC_Z
  return flags

def testNZ16(val):
  flags = 0
  if val & 0x8000: flags |= CC_N
  if not val & 0xFFFF: flags |= CC_Z
  return flags

def eor8(u1, u2):
  "Exclusive-OR 8-bit quantities and set flags"
  result = u1 ^ u2
  flags = 0
  if result & 0x80: flags |= CC_N
  if not result & 0xFF: flags |= CC_Z
  return (result, flags)

def ABA(simstate):
  A, flags = add8(simstate.ucState.A, simstate.ucState.B)
  simstate.ucState.setA(A)
  simstate.ucState.setHNZVC(flags)

def ABX(simstate):
  X = (simstate.ucState.X + simstate.ucState.B) & 0xFFFF
  simstate.ucState.setX(X)

def ABY(simstate):
  Y = (simstate.ucState.Y + simstate.ucState.B) & 0xFFFF
  simstate.ucState.setY(Y)

def ADCA(simstate, addr, value):
  if addr is None:
    A, flags = add8(simstate.ucState.A, value + simstate.ucState.isCarrySet())
  else:
    A, flags = add8(simstate.ucState.A, simstate.ucMemory.readUns8(addr) + simstate.ucState.isCarrySet())
  simstate.ucState.setA(A)
  simstate.ucState.setHNZVC(flags)

def ADCB(simstate, addr, value):
  if addr is None:
    B, flags = add8(simstate.ucState.B, value + simstate.ucState.isCarrySet())
  else:
    B, flags = add8(simstate.ucState.B, simstate.ucMemory.readUns8(addr) + simstate.ucState.isCarrySet())
  simstate.ucState.setB(B)
  simstate.ucState.setHNZVC(flags)

def ADDA(simstate, addr, value):
  if addr is None:
    A, flags = add8(simstate.ucState.A, value)
  else:
    A, flags = add8(simstate.ucState.A, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setA(A)
  simstate.ucState.setHNZVC(flags)

def ADDB(simstate, addr, value):
  if addr is None:
    B, flags = add8(simstate.ucState.B, value)
  else:
    B, flags = add8(simstate.ucState.B, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setB(B)
  simstate.ucState.setHNZVC(flags)

def ADDD(simstate, addr, value):
  if addr is None:
    D, flags = add16(simstate.ucState.D(), value)
  else:
    D, flags = add16(simstate.ucState.D(), simstate.ucMemory.readUns16(addr))
  simstate.ucState.setD(D)
  simstate.ucState.setNZVC(flags)

def ANDA(simstate, addr, value):
  if addr is None:
    A, flags = and8(simstate.ucState.A, value)
  else:
    A, flags = and8(simstate.ucState.A, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setA(A)
  simstate.ucState.setNZV(flags)

def ANDB(simstate, addr, value):
  if addr is None:
    B, flags = and8(simstate.ucState.B, value)
  else:
    B, flags = and8(simstate.ucState.B, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setB(B)
  simstate.ucState.setNZV(flags)

def ASL(simstate, addr, value):
  M, flags = asl8(simstate.ucMemory.readUns8(addr))
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZVC(flags)

def ASLA(simstate):
  A, flags = asl8(simstate.ucState.A)
  simstate.ucState.setA(A)
  simstate.ucState.setNZVC(flags)

def ASLB(simstate):
  B, flags = asl8(simstate.ucState.B)
  simstate.ucState.setB(B)
  simstate.ucState.setNZVC(flags)

def ASR(simstate, addr, value):
  M, flags = asr8(simstate.ucMemory.readUns8(addr))
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZVC(flags)

def ASRA(simstate):
  A, flags = asr8(simstate.ucState.A)
  simstate.ucState.setA(A)
  simstate.ucState.setNZVC(flags)

def ASRB(simstate):
  B, flags = asr8(simstate.ucState.B)
  simstate.ucState.setB(B)
  simstate.ucState.setNZVC(flags)

def BCLR(simstate, addr, mask):
  M = (simstate.ucMemory.readUns8(addr) & ~mask) & 0xFF
  flags = testNZ8(M)
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZV(flags)

def branchIf(simstate, truth, addr):
  import PySim11
  if truth and simstate.BForce != BFORCE_NEVER or simstate.BForce == BFORCE_ALWAYS:
    simstate.ucState.setPC(addr)

def BEQ(simstate, addr):
  branchIf(simstate, simstate.ucState.isZeroSet(), addr)

def BGE(simstate, addr):
  branchIf(simstate, not (simstate.ucState.isNegativeSet() ^ simstate.ucState.isOverflowSet()), addr)

def BGT(simstate, addr):
  branchIf(simstate, not ((simstate.ucState.isNegativeSet() ^ simstate.ucState.isOverflowSet()) | simstate.ucState.isZeroSet()), addr)

def BHI(simstate, addr):
  branchIf(simstate, not (simstate.ucState.isCarrySet() | simstate.ucState.isZeroSet()), addr)

def BHS(simstate, addr):
  branchIf(simstate, not simstate.ucState.isCarrySet(), addr)

def BITA(simstate, addr, value):
  if addr is None:
    M, flags = and8(simstate.ucState.A, value)
  else:
    M, flags = and8(simstate.ucState.A, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setNZV(flags)

def BITB(simstate, addr, value):
  if addr is None:
    M, flags = and8(simstate.ucState.B, value)
  else:
    M, flags = and8(simstate.ucState.B, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setNZV(flags)

def BLE(simstate, addr):
  branchIf(simstate, (simstate.ucState.isNegativeSet() ^ simstate.ucState.isOverflowSet()) | simstate.ucState.isZeroSet(), addr)

def BLO(simstate, addr):
  branchIf(simstate, simstate.ucState.isCarrySet(), addr)

def BLS(simstate, addr):
  branchIf(simstate, simstate.ucState.isCarrySet() | simstate.ucState.isZeroSet(), addr)

def BLT(simstate, addr):
  branchIf(simstate, simstate.ucState.isNegativeSet() ^ simstate.ucState.isOverflowSet(), addr)

def BMI(simstate, addr):
  branchIf(simstate, simstate.ucState.isNegativeSet(), addr)

def BNE(simstate, addr):
  branchIf(simstate, not simstate.ucState.isZeroSet(), addr)

def BPL(simstate, addr):
  branchIf(simstate, not simstate.ucState.isNegativeSet(), addr)

def BRA(simstate, addr): branchIf(simstate, 1, addr)

def BRCLR(simstate, addr, mask, newpc):
  branchIf(simstate, not (simstate.ucMemory.readUns8(addr) & mask), newpc)

def BRN(simstate, addr): branchIf(simstate, 0, addr)

def BRSET(simstate, addr, mask, newpc):
  branchIf(simstate, not ((~simstate.ucMemory.readUns8(addr)) & mask), newpc)

def BSET(simstate, addr, mask):
  M = (simstate.ucMemory.readUns8(addr) | mask) & 0xFF
  flags = testNZ8(M)
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZV(flags)

def BSR(simstate, addr):
  simstate.ucState.push16(simstate.ucMemory, simstate.ucState.PC)
  simstate.ucState.setPC(addr)

def BVC(simstate, addr):
  branchIf(simstate, not simstate.ucState.isOverflowSet(), addr)

def BVS(simstate, addr):
  branchIf(simstate, simstate.ucState.isOverflowSet(), addr)

def CBA(simstate):
  diff, flags = sub8(simstate.ucState.A, simstate.ucState.B)
  simstate.ucState.setNZVC(flags)

def CLC(simstate): simstate.ucState.setC(0)

def CLI(simstate): simstate.ucState.setI(0)

def CLR(simstate, addr, value):
  simstate.ucMemory.writeUns8(addr, 0)
  simstate.ucState.setNZVC(CC_Z)

def CLRA(simstate):
  simstate.ucState.setA(0)
  simstate.ucState.setNZVC(CC_Z)

def CLRB(simstate):
  simstate.ucState.setB(0)
  simstate.ucState.setNZVC(CC_Z)

def CLV(simstate): simstate.ucState.setV(0)

def CMPA(simstate, addr, value):
  if addr is None:
    M, flags = sub8(simstate.ucState.A, value)
  else:
    M, flags = sub8(simstate.ucState.A, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setNZVC(flags)

def CMPB(simstate, addr, value):
  if addr is None:
    M, flags = sub8(simstate.ucState.B, value)
  else:
    M, flags = sub8(simstate.ucState.B, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setNZVC(flags)

def COM(simstate, addr, value):
  M = (~simstate.ucMemory.readUns8(addr)) & 0xFF
  flags = testNZ8(M)
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZVC(flags | CC_C)

def COMA(simstate):
  simstate.ucState.setA((~simstate.ucState.A) & 0xFF)
  simstate.ucState.setNZVC(testNZ8(simstate.ucState.A) | CC_C)

def COMB(simstate):
  simstate.ucState.setB((~simstate.ucState.B) & 0xFF)
  simstate.ucState.setNZVC(testNZ8(simstate.ucState.B) | CC_C)

def CPD(simstate, addr, value):
  if addr is None:
    M, flags = sub16(simstate.ucState.D(), value)
  else:
    M, flags = sub16(simstate.ucState.D(), simstate.ucMemory.readUns16(addr))
  simstate.ucState.setNZVC(flags)

def CPX(simstate, addr, value):
  if addr is None:
    M, flags = sub16(simstate.ucState.X, value)
  else:
    M, flags = sub16(simstate.ucState.X, simstate.ucMemory.readUns16(addr))
  simstate.ucState.setNZVC(flags)

def CPY(simstate, addr, value):
  if addr is None:
    M, flags = sub16(simstate.ucState.Y, value)
  else:
    M, flags = sub16(simstate.ucState.Y, simstate.ucMemory.readUns16(addr))
  simstate.ucState.setNZVC(flags)

def DEC(simstate, addr, value):
  M, flags = sub8(simstate.ucMemory.readUns8(addr), 1)
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZV(flags)

def DECA(simstate):
  A, flags = sub8(simstate.ucState.A, 1)
  simstate.ucState.setA(A)
  simstate.ucState.setNZV(flags)

def DECB(simstate):
  B, flags = sub8(simstate.ucState.B, 1)
  simstate.ucState.setB(B)
  simstate.ucState.setNZV(flags)

def DES(simstate):
  S = (simstate.ucState.SP - 1) & 0xFFFF
  simstate.ucState.setSP(S)

def DEX(simstate):
  X = (simstate.ucState.X - 1) & 0xFFFF
  flags = 0
  if not X: flags |= CC_Z
  simstate.ucState.setX(X)
  simstate.ucState.setZ(flags)

def DEY(simstate):
  Y = (simstate.ucState.Y - 1) & 0xFFFF
  flags = 0
  if not Y: flags |= CC_Z
  simstate.ucState.setY(Y)
  simstate.ucState.setZ(flags)

def EORA(simstate, addr, value):
  if addr is None:
    A, flags = eor8(simstate.ucState.A, value)
  else:
    A, flags = eor8(simstate.ucState.A, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setA(A)
  simstate.ucState.setNZV(flags)

def EORB(simstate, addr, value):
  if addr is None:
    B, flags = eor8(simstate.ucState.B, value)
  else:
    B, flags = eor8(simstate.ucState.B, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setB(B)
  simstate.ucState.setNZV(flags)

def INC(simstate, addr, value):
  M, flags = add8(simstate.ucMemory.readUns8(addr), 1)
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZV(flags)

def INCA(simstate):
  A, flags = add8(simstate.ucState.A, 1)
  simstate.ucState.setA(A)
  simstate.ucState.setNZV(flags)

def INCB(simstate):
  B, flags = add8(simstate.ucState.B, 1)
  simstate.ucState.setB(B)
  simstate.ucState.setNZV(flags)

def INS(simstate):
  S = (simstate.ucState.SP + 1) & 0xFFFF
  simstate.ucState.setSP(S)

def INX(simstate):
  X = (simstate.ucState.X + 1) & 0xFFFF
  flags = 0
  if not X: flags |= CC_Z
  simstate.ucState.setX(X)
  simstate.ucState.setZ(flags)

def INY(simstate):
  Y = (simstate.ucState.Y + 1) & 0xFFFF
  flags = 0
  if not Y: flags |= CC_Z
  simstate.ucState.setY(Y)
  simstate.ucState.setZ(flags)

def JMP(simstate, addr, value):
  simstate.ucState.setPC(addr)

def JSR(simstate, addr, value):
  simstate.ucState.push16(simstate.ucMemory, simstate.ucState.PC)
  simstate.ucState.setPC(addr)

def LDAA(simstate, addr, value):
  if addr is None: A = value
  else: A = simstate.ucMemory.readUns8(addr)
  flags = testNZ8(A)
  simstate.ucState.setA(A)
  simstate.ucState.setNZV(flags)

def LDAB(simstate, addr, value):
  if addr is None: B = value
  else: B = simstate.ucMemory.readUns8(addr)
  flags = testNZ8(B)
  simstate.ucState.setB(B)
  simstate.ucState.setNZV(flags)

def LDD(simstate, addr, value):
  if addr is None: D = value
  else: D = simstate.ucMemory.readUns16(addr)
  flags = testNZ16(D)
  simstate.ucState.setD(D)
  simstate.ucState.setNZV(flags)

def LDS(simstate, addr, value):
  if addr is None: D = value
  else: D = simstate.ucMemory.readUns16(addr)
  flags = testNZ16(D)
  simstate.ucState.setSP(D)
  simstate.ucState.setNZV(flags)

def LDX(simstate, addr, value):
  if addr is None: D = value
  else: D = simstate.ucMemory.readUns16(addr)
  flags = testNZ16(D)
  simstate.ucState.setX(D)
  simstate.ucState.setNZV(flags)

def LDY(simstate, addr, value):
  if addr is None: D = value
  else: D = simstate.ucMemory.readUns16(addr)
  flags = testNZ16(D)
  simstate.ucState.setY(D)
  simstate.ucState.setNZV(flags)

def LSLD(simstate):
  D,flags = asl16(simstate.ucState.D())
  simstate.ucState.setD(D)
  simstate.ucState.setNZVC(flags)

def LSR(simstate, addr, value):
  M, flags = lsr8(simstate.ucMemory.readUns8(addr))
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZVC(flags)

def LSRA(simstate):
  A, flags = lsr8(simstate.ucState.A)
  simstate.ucState.setA(A)
  simstate.ucState.setNZVC(flags)

def LSRB(simstate):
  B, flags = lsr8(simstate.ucState.B)
  simstate.ucState.setB(B)
  simstate.ucState.setNZVC(flags)

def LSRD(simstate):
  D, flags = lsr16(simstate.ucState.D())
  simstate.ucState.setD(D)
  simstate.ucState.setNZVC(flags)

def NEG(simstate, addr, value):
  M, flags = neg8(simstate.ucMemory.readUns8(addr))
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZVC(flags)

def NEGA(simstate):
  A, flags = neg8(simstate.ucState.A)
  simstate.ucState.setA(A)
  simstate.ucState.setNZVC(flags)

def NEGB(simstate):
  B, flags = neg8(simstate.ucState.B)
  simstate.ucState.setB(B)
  simstate.ucState.setNZVC(flags)

def NOP(simstate): pass

def ORAA(simstate, addr, value):
  if addr is None:
    A, flags = or8(simstate.ucState.A, value)
  else:
    A, flags = or8(simstate.ucState.A, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setA(A)
  simstate.ucState.setNZV(flags)

def ORAB(simstate, addr, value):
  if addr is None:
    B, flags = or8(simstate.ucState.B, value)
  else:
    B, flags = or8(simstate.ucState.B, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setB(B)
  simstate.ucState.setNZV(flags)

def PSHA(simstate):
  simstate.ucState.push8(simstate.ucMemory, simstate.ucState.A)

def PSHB(simstate):
  simstate.ucState.push8(simstate.ucMemory, simstate.ucState.B)

def PSHX(simstate):
  simstate.ucState.push16(simstate.ucMemory, simstate.ucState.X)

def PSHY(simstate):
  simstate.ucState.push16(simstate.ucMemory, simstate.ucState.Y)

def PULA(simstate):
  simstate.ucState.setA(simstate.ucState.pull8(simstate.ucMemory))

def PULB(simstate):
  simstate.ucState.setB(simstate.ucState.pull8(simstate.ucMemory))

def PULX(simstate):
  simstate.ucState.setX(simstate.ucState.pull16(simstate.ucMemory))

def PULY(simstate):
  simstate.ucState.setY(simstate.ucState.pull16(simstate.ucMemory))

def ROL(simstate, addr, value):
  M, flags = rol8(simstate.ucMemory.readUns8(addr), simstate.ucState.isCarrySet())
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZVC(flags)

def ROLA(simstate):
  A, flags = rol8(simstate.ucState.A, simstate.ucState.isCarrySet())
  simstate.ucState.setA(A)
  simstate.ucState.setNZVC(flags)

def ROLB(simstate):
  B, flags = rol8(simstate.ucState.B, simstate.ucState.isCarrySet())
  simstate.ucState.setB(B)
  simstate.ucState.setNZVC(flags)

def ROR(simstate, addr, value):
  M, flags = ror8(simstate.ucMemory.readUns8(addr), simstate.ucState.isCarrySet())
  simstate.ucMemory.writeUns8(addr, M)
  simstate.ucState.setNZVC(flags)

def RORA(simstate):
  A, flags = ror8(simstate.ucState.A, simstate.ucState.isCarrySet())
  simstate.ucState.setA(A)
  simstate.ucState.setNZVC(flags)

def RORB(simstate):
  B, flags = ror8(simstate.ucState.B, simstate.ucState.isCarrySet())
  simstate.ucState.setB(B)
  simstate.ucState.setNZVC(flags)

def RTI(simstate):
  newCC = simstate.ucState.pull8(simstate.ucMemory)
  simstate.ucState.setB(simstate.ucState.pull8(simstate.ucMemory))
  simstate.ucState.setA(simstate.ucState.pull8(simstate.ucMemory))
  simstate.ucState.setX(simstate.ucState.pull16(simstate.ucMemory))
  simstate.ucState.setY(simstate.ucState.pull16(simstate.ucMemory))
  simstate.ucState.setPC(simstate.ucState.pull16(simstate.ucMemory))

  # The deal is that the X bit in the CC is not allowed to go from 0 to 1
  # but is allowed to go from 1 to 0.
  oldCC = simstate.ucState.CC
  simstate.ucState.setCC(oldCC & newCC & CC_X | newCC & ~CC_X)

def RTS(simstate):
  simstate.ucState.setPC(simstate.ucState.pull16(simstate.ucMemory))

def SBA(simstate):
  diff, flags = sub8(simstate.ucState.A, simstate.ucState.B)
  simstate.ucState.setA(diff)
  simstate.ucState.setNZVC(flags)

def SBCA(simstate, addr, value):
  if addr is None:
    A, flags = sub8(simstate.ucState.A, value + simstate.ucState.isCarrySet())
  else:
    A, flags = sub8(simstate.ucState.A, simstate.ucMemory.readUns8(addr) + simstate.ucState.isCarrySet())
  simstate.ucState.setA(A)
  simstate.ucState.setNZVC(flags)

def SBCB(simstate, addr, value):
  if addr is None:
    B, flags = sub8(simstate.ucState.B, value + simstate.ucState.isCarrySet())
  else:
    B, flags = sub8(simstate.ucState.B, simstate.ucMemory.readUns8(addr) + simstate.ucState.isCarrySet())
  simstate.ucState.setB(B)
  simstate.ucState.setNZVC(flags)

def SEC(simstate): simstate.ucState.setC(CC_C)
def SEI(simstate): simstate.ucState.setI(CC_I)
def SEV(simstate): simstate.ucState.setV(CC_V)

def STAA(simstate, addr, value):
  simstate.ucMemory.writeUns8(addr, simstate.ucState.A)
  flags = testNZ8(simstate.ucState.A)
  simstate.ucState.setNZV(flags)

def STAB(simstate, addr, value):
  simstate.ucMemory.writeUns8(addr, simstate.ucState.B)
  flags = testNZ8(simstate.ucState.B)
  simstate.ucState.setNZV(flags)

def STD(simstate, addr, value):
  simstate.ucMemory.writeUns16(addr, simstate.ucState.D())
  flags = testNZ16(simstate.ucState.D())
  simstate.ucState.setNZV(flags)

def STOP(simstate):
  if simstate.ucState.isStopSet(): return
  raise StopInstruction

def STS(simstate, addr, value):
  simstate.ucMemory.writeUns16(addr, simstate.ucState.SP)
  flags = testNZ16(simstate.ucState.SP)
  simstate.ucState.setNZV(flags)

def STX(simstate, addr, value):
  simstate.ucMemory.writeUns16(addr, simstate.ucState.X)
  flags = testNZ16(simstate.ucState.X)
  simstate.ucState.setNZV(flags)

def STY(simstate, addr, value):
  simstate.ucMemory.writeUns16(addr, simstate.ucState.Y)
  flags = testNZ16(simstate.ucState.Y)
  simstate.ucState.setNZV(flags)

def SUBA(simstate, addr, value):
  if addr is None:
    A, flags = sub8(simstate.ucState.A, value)
  else:
    A, flags = sub8(simstate.ucState.A, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setA(A)
  simstate.ucState.setNZVC(flags)

def SUBB(simstate, addr, value):
  if addr is None:
    B, flags = sub8(simstate.ucState.B, value)
  else:
    B, flags = sub8(simstate.ucState.B, simstate.ucMemory.readUns8(addr))
  simstate.ucState.setB(B)
  simstate.ucState.setNZVC(flags)

def SUBD(simstate, addr, value):
  if addr is None:
    D, flags = sub16(simstate.ucState.D(), value)
  else:
    D, flags = sub16(simstate.ucState.D(), simstate.ucMemory.readUns16(addr))
  simstate.ucState.setD(D)
  simstate.ucState.setNZVC(flags)

def SWI(simstate):
  if UseSWI:
    simstate.ucState.push16(simstate.ucMemory, simstate.ucState.PC)
    simstate.ucState.push16(simstate.ucMemory, simstate.ucState.Y)
    simstate.ucState.push16(simstate.ucMemory, simstate.ucState.X)
    simstate.ucState.push8(simstate.ucMemory, simstate.ucState.A)
    simstate.ucState.push8(simstate.ucMemory, simstate.ucState.B)
    simstate.ucState.push8(simstate.ucMemory, simstate.ucState.CC)
    simstate.ucState.setI(CC_I)
    simstate.ucState.setPC(simstate.ucMemory.readUns16(0xFFF6))
  else: raise SWIInstruction

def TAB(simstate):
  simstate.ucState.setB(simstate.ucState.A)
  simstate.ucState.setNZV(testNZ8(simstate.ucState.A))

def TAP(simstate):
  # Remember...the X bit may be cleared but it may
  # not be set.
  A = simstate.ucState.A
  oldCC = simstate.ucState.CC
  simstate.ucState.setCC(A & ~CC_X | A & oldCC & CC_X)

def TBA(simstate):
  simstate.ucState.setA(simstate.ucState.B)
  simstate.ucState.setNZV(testNZ8(simstate.ucState.A))

def TEST(simstate): raise TestInstruction
def TPA(simstate): simstate.ucState.setA(simstate.ucState.CC)

def TST(simstate, addr, value):
  flags = testNZ8(simstate.ucMemory.readUns8(addr))
  simstate.ucState.setNZVC(flags)

def TSTA(simstate):
  flags = testNZ8(simstate.ucState.A)
  simstate.ucState.setNZVC(flags)

def TSTB(simstate):
  flags = testNZ8(simstate.ucState.B)
  simstate.ucState.setNZVC(flags)

def TSX(simstate): simstate.ucState.setX((simstate.ucState.SP+1) & 0xFFFF)
def TSY(simstate): simstate.ucState.setY((simstate.ucState.SP+1) & 0xFFFF)
def TXS(simstate): simstate.ucState.setSP((simstate.ucState.X-1) & 0xFFFF)
def TYS(simstate): simstate.ucState.setSP((simstate.ucState.Y-1) & 0xFFFF)

def WAI(simstate):
  simstate.ucState.push16(simstate.ucMemory, simstate.ucState.PC)
  simstate.ucState.push16(simstate.ucMemory, simstate.ucState.Y)
  simstate.ucState.push16(simstate.ucMemory, simstate.ucState.X)
  simstate.ucState.push8(simstate.ucMemory, simstate.ucState.A)
  simstate.ucState.push8(simstate.ucMemory, simstate.ucState.B)
  simstate.ucState.push8(simstate.ucMemory, simstate.ucState.CC)
  raise WaitInstruction

def XGDX(simstate):
  D = simstate.ucState.D()
  simstate.ucState.setD(simstate.ucState.X)
  simstate.ucState.setX(D)

def XGDY(simstate):
  D = simstate.ucState.D()
  simstate.ucState.setD(simstate.ucState.Y)
  simstate.ucState.setY(D)

def DAA(simstate):
  c = simstate.ucState.isCarrySet()
  h = simstate.ucState.isHalfSet()
  uhb = simstate.ucState.A >> 4 & 0x0F
  lhb = simstate.ucState.A & 0x0F

  offset = cout = 0
  if c == 0 and h == 0:
    if uhb <= 9 and lhb <= 9:
      pass
    elif uhb <= 8 and lhb >= 10:
      offset = 0x06
    elif uhb >= 10 and lhb <= 9:
      offset = 0x60
      cout = 1
    elif uhb >= 9 and lhb >= 10:
      offset = 0x66
      cout = 1
  elif c == 0 and h == 1:
    if uhb <= 9 and lhb <= 3:
      offset = 0x06
    elif uhb >= 10 and lhb <= 3:
      offset = 0x66
      cout = 1
  elif c == 1 and h == 0:
    if uhb <= 2 and lhb <= 9:
      offset = 0x60
      cout = 1
    elif uhb <= 2 and lhb >= 10:
      offset = 0x66
      cout = 1
  elif uhb <= 3 and lhb <= 3:
    offset = 0x66
    cout = 1

  simstate.ucState.setA((simstate.ucState.A + offset) & 0xFF)
  simstate.ucState.setNZVC(testNZ8(simstate.ucState.A) | cout * CC_C)

def MUL(simstate):
  D = simstate.ucState.A * simstate.ucState.B
  if D & 0x0080: flags = CC_C
  else: flags = 0
  simstate.ucState.setD(D)
  simstate.ucState.setC(flags)

def IDIV(simstate):
  flags = 0
  if simstate.ucState.X == 0:
    flags |= CC_C
    Q = 0xFFFF
    R = 0
  else:
    Q = int(simstate.ucState.D() / simstate.ucState.X)
    R = simstate.ucState.D() % simstate.ucState.X
    if Q == 0: flags |= CC_Z

  simstate.ucState.setX(Q)
  simstate.ucState.setD(R)
  simstate.ucState.setZVC(flags)

def FDIV(simstate):
  flags = 0
  if simstate.ucState.X == 0 or simstate.ucState.X <= simstate.ucState.D():
    Q = 0xFFFF
    R = 0
    flags |= CC_V
    if simstate.ucState.X == 0: flags |= CC_C
  else:
    Q = int(simstate.ucState.D()*0x10000 / simstate.ucState.X)
    R = int(simstate.ucState.D()*0x10000 % simstate.ucState.X)
    if Q == 0: flags |= CC_Z

  simstate.ucState.setX(Q)
  simstate.ucState.setD(R)
  simstate.ucState.setZVC(flags)
