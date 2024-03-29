'''
mapsym -- Support for MAP files and source-level debugging

This module is intended to support *.MAP files generated by
Tony Papadimitriou's ASM11 v12.20+ (www.aspisys.com/asm11.htm)
using the -MTA option (i.e., parsable ASCII output).
'''

import sys
import string
import re
import os

from safestruct import *

class MapFile(SafeStruct):
  def __init__(self, fid = None, direct = '.'):
    super().__init__({
      'fnames': [],   # List of file names indexed by file number
      'files': [],    # Indexed by file number, each entry contains a
                      # sub-list indexed by line numbers (first is 0)
      'addrmap': {},  # Indexed by 16-bit address, each entry contains
                      # a 3-tuple with a reference to the right line in files,
                      # the filename, and the line number
      'linemap': {},  # Indexed by (filenumber, linenumber) tuples, each
                      # entry contains a 2-tuple with 16-bit address and
                      # symbol.
      'symtab': {}    # Indexed by symbol name, each entry contains a
                      # 16-bit unsigned value
    })

    if fid: self.readfid(fid, direct)

  def readfid(self, fid, direct = '.'):
    assert fid
    lines = fid.readlines()

    lineno = 0
    # Sanity check
    if lines[0][:10] != '[COMMENTS]':
      raise IOError('This does not look like a supported MAP file')

    # Skip over comments
    while lines[lineno][:7] != '[FILES]':
      lineno += 1
      if lineno >= len(lines):
        raise IOError('Did not find [FILES] section in MAP file')

    # Skip over blank line
    lineno += 2

    while lines[lineno][:7] != '[LINKS]':
      fname = lines[lineno].strip()
      if len(fname):
        fullname = os.path.join(direct, fname)
        if not os.path.exists(fullname):
          raise IOError(f'File {fname} in [FILES] section not found in {direct}')
        self.fnames.append(fname)
        with open(fullname, 'rt', errors='ignore') as f:
          self.files.append(f.readlines())
        f.close()
      lineno += 1
      if lineno >= len(lines):
        raise IOError('Did not find [LINKS] section in MAP file')

    lineno += 1
    while lineno < len(lines):
      if len(lines[lineno]) < 2:
        lineno += 1
        continue  # blank line
      try:
        addr_s, fnum_s, linenum_s, sym, bytesize = lines[lineno].split()
        sym = sym.upper()
      except:
        sym = None
        try: addr_s, fnum_s, linenum_s = lines[lineno].split()
        except: raise IOError(f'MAP file format error at line {lineno}')
      lineno += 1

      addr = int(addr_s, 16)
      fnum = int(fnum_s)
      linenum = int(linenum_s)
      if fnum > 0:
        if fnum > len(self.files):
          raise IOError(f'Illegal file number at line {lineno} of MAP file')
        if linenum > len(self.files[fnum-1]):
          raise IOError(f'Illegal line number at line {lineno} of MAP file')
        self.addrmap[addr] = (self.files[fnum-1][linenum-1], self.fnames[fnum-1], linenum)
        self.linemap[(fnum, linenum)] = (addr, sym)
      if sym: self.symtab[sym] = addr

################################################################################

def add_extension(filename):
  try: filename, ext = filename.rsplit('.',1)
  except: pass
  ext = 'map'
  return filename + '.' + ext

def LoadMapFile(filename, simstate):
  filename = add_extension(filename)
  if filename:
    try:
      mf = MapFile(open(filename, 'rt'))
    except Exception as detail:
      mf = None
      if detail: print(detail)
    if mf:
      simstate.mapfile = mf
      return f'Loaded MAP file "{filename}"'
    else: return f'Unable to interpret MAP file "{filename}"'
  else: return "No MAP file found"

##############################################################################

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print('mapsym Filename.MAP')
    sys.exit(0)

  with open(sys.argv[1], 'rt') as fid: mf = MapFile(fid); fid.close()

  addr = mf.addrmap.keys()
  addr = sorted(addr)

  for A in addr: print("%04X: " % A, mf.addrmap[A][0],end=' ')
  for sym in mf.symtab.keys(): print("%10s %04X" % (sym, mf.symtab[sym]))
