'''
Read and verify S19 files
'''

import os
import string
import re

import PySim11.memory

__all__ = ["ReadS19","VerifyS19"]

s19pat = r'S(\d)([\da-fA-F]{2,2})([\da-fA-F]{4,4})([\da-fA-F]*)([\da-fA-F]{2,2})'
s19re = re.compile(s19pat)

def add_extension(filename):
  try: filename, ext = filename.rsplit('.',1)
  except: pass
  ext = 's19'
  return filename + '.' + ext

def ReadS19(Filename, Memory): return S19reader(Filename, Memory, 0)

def VerifyS19(Filename, Memory): return S19reader(Filename, Memory, 1)

def S19reader(Filename, Memory, verify = 0):
  '''This function returns a tuple (address, diagnostics) which contains the
  address to run at (if any) and the diagnostics, if not None, contains
  a strings with some diagnostics to print (such as the number of ignored
  S-records).'''

  Filename = add_extension(Filename)
  with open(Filename, 'rt') as fid: lines = fid.readlines()
  fid.close()

  retaddr = None
  ignoreCount = 0

  lineix = 0
  for line in lines:
    lineix += 1
    m = s19re.match(line)
    if not m: raise ValueError(f'S19 format error at line {lineix}')

    typ, count, addr, data, chksum = m.groups()

    if typ in '19':
      if (len(data) & 0x01):
        raise ValueError(f'Odd-length data at line {lineix}')

      count = int(count,16)
      addr = int(addr, 16)
      chksum = int(chksum, 16) + count + (addr//256) + (addr%256) + 1

      if count != (3+len(data)//2):
        raise ValueError(f'Record count mismatch at line {lineix}')

      if typ == '9':
        if count > 3:
          raise ValueError(f'Unexpected data in S9 record at line {lineix}')
        s = None
        if ignoreCount:
          s = f'Ignored {ignoreCount} S-record{"" if ignoreCount == 1 else "s"} of unsupported format\n'
        return addr, s

      retaddr = retaddr or addr

      if count <= 3:
        raise ValueError(f'Unexpected empty S1 record at line {lineix}')

      for count in range(len(data)//2):
        val = int(data[2*count:2*count+2],16)
        if verify:
          if Memory.readUns8(addr+count) != val:
            s = 'Verify error at $%04X\n' % (addr+count)
            s += '  Memory: $%02X  %s: $%02X' % (Memory.readUns8(addr+count), Filename, val)
            raise ValueError(s)
        else: Memory.writeUns8(addr+count, val)
        chksum += val

      if (chksum & 0xFF): raise ValueError(f'Checksum error at line {lineix}')

    else: ignoreCount += 1

  retaddr = retaddr or 0

  s = 'WARNING: No S9 record found'
  if ignoreCount:
    s += f'\nIgnored {ignoreCount} S-records of unsupported format'

  return retaddr, s
