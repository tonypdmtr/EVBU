'''
Global variables and option handling for EVBU
'''

from safestruct import *
SetDebug(0)

EVBUVersionMajor = 0
EVBUVersionMinor = 6

import sys
import os
import re
import getopt
import string
import math
from types import *
from G import *
from PySim11.G import *
from PySim11 import PySim11

def usage(arglist):
  head, tail = os.path.split(arglist[0])
  root, ext  = os.path.splitext(tail)

  print('''\
Usage:
  evbu [Options] [Filename.S19]

Options:
  -s, --start=addr -- Specify starting address (overrides S19 file)
  --use-swi        -- Allow SWI instructions to execute
  --no-buffalo     -- Do not use BUFFALO services
  --no-timer       -- Do not install the timer peripheral
  --no-pio         -- Do not install the parallel I/O peripheral
  -h, --help       -- Display this help summary
  -v, --version    -- Display version information

The EVBU home page is at <http://claymore.engineer.gvsu.edu/~steriana/Python>
Contact the author at <steriana@claymore.engineer.gvsu.edu>\
''')

  sys.exit(1)

def parseArgs(arglist = None):
  if not arglist: arglist = sys.argv

  try:
    optlist, args = getopt.getopt(arglist[1:], 'hHvs:', ['help', 'version', 'use-swi', 'start=', 'no-buffalo',
                                                          'no-timer', 'no-pio'])
  except getopt.error as detail:
    print('Option error:', detail)
    usage(arglist)

  for item in optlist:
    if (w := item[0]) in ['-h','-H','--help']:
      usage(arglist)
    elif w in ['-v','--version']:
      print('EVBU Version %d.%d' % (EVBUVersionMajor, EVBUVersionMinor))
      print('PySim11 Version %d.%d' % (PySim11.PySim11VersionMajor, PySim11.PySim11VersionMinor))
      sys.exit(0)
    elif w == '--use-swi': UseSWI = 1
    elif w == '--no-buffalo': UseBuffaloServices = 0
    elif w == '--no-timer': Peripherals['Timer'][0] = 0
    elif w == '--no-pio': Peripherals['ParallelIO'][0] = 0
    elif w in ['-s','--start']: StartPC = int(item[1],0)
    else:
      print('UNKNOWN OPTION:', w)
      sys.exit(1)

  if len(args) > 0: S19FileName = args[0]

  if len(args) > 1:
    print('Too many arguments')
    sys.exit(1)
