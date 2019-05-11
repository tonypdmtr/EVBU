'''
Utility functions for parsing integers/symbols
'''

import string

# Service routines to parse strings into integers and verify them
def parseInteger(field, simstate=None):
  try:
    if simstate and simstate.mapfile:
      try:
        val = simstate.mapfile.symtab[field.upper()]
        return val
      except: pass
    if all(x in string.hexdigits for x in field): val = int(field, 16)
    elif field[0] == '$': val = int(field[1:], 16)
    elif field[0] == '%': val = int(field[1:], 2)
    elif field[0] == '&': val = int(field[1:])
    elif field[0] == '-': val = int(field)
    elif field[0] == '@': val = int(field[1:], 8)
    else: raise ValueError
    return val
  except: raise ValueError(f'Invalid integer: "{field}"')

def parseu32(field):
  val = parseInteger(field)
  if val < 0:
    raise ValueError(f'Quantity "{field}" is not an unsigned integer')
  return val

def parseu16(field, simstate=None):
  val = parseInteger(field, simstate)
  if val < 0: val += 65536
  if val < 0 or val > 0xFFFF:
    raise ValueError(f'Quantity "{field}" is not a valid 16-bit integer')
  return val

def parseu8(field, simstate=None):
  val = parseInteger(field, simstate)
  if val < 0: val += 256
  if val < 0 or val > 0xFF:
    raise ValueError(f'Quantity "{field}" is not a valid 8-bit integer')
  return val

def parseFields(line, minF, maxF):
  if len(line) > 0:
    rawfields = line.split()
    fields = []
    for f in rawfields:
      if len(f): fields.append(f)
  else: fields = []

  if len(fields) < minF:
    s = f'Expecting at least {minF} parameter{"s" if minF > 1 else ""}'
    raise ValueError(s)
  elif len(fields) > maxF:
    s = f'Expecting at most {maxF} parameter{"s" if maxF > 1 else ""}'
    raise ValueError(s)
  return fields

def getu32(line, simstate=None):
  "Expecting a single 32-bit unsigned integer"
  fields = parseFields(line, 1, 1)
  return parseu32(fields[0])

def getu16(line, simstate=None):
  "Expecting a single 16-bit unsigned integer"
  fields = parseFields(line, 1, 1)
  return parseu16(fields[0], simstate)

def getu16u16(line, simstate=None):
  "Expecting two 16-bit unsigned integers"
  fields = parseFields(line, 2, 2)
  return parseu16(fields[0], simstate), parseu16(fields[1], simstate)

def getu16u16optu16(line, simstate=None):
  "Expecting two or three 16-bit unsigned integers"
  fields = parseFields(line, 2, 3)
  if len(fields) > 2:
    return parseu16(fields[0], simstate), parseu16(fields[1], simstate), parseu16(fields[2], simstate)
  return parseu16(fields[0], simstate), parseu16(fields[1], simstate), None

def getu16u16u8(line, simstate=None):
  "Expecting two 16-bit unsigned integers and an 8-bit unsigned integer"
  fields = parseFields(line, 3, 3)
  return parseu16(fields[0], simstate), parseu16(fields[1], simstate), parseu8(fields[2], simstate)

def getu16optu16(line, simstate=None):
  "Expecting one-to-two 16-bit unsigned integers"
  fields = parseFields(line, 1, 2)
  if len(fields) == 1: return (parseu16(fields[0], simstate), None)
  return parseu16(fields[0], simstate), parseu16(fields[1], simstate)

def getoptu16(line, simstate=None):
  "Expecting zero-to-one 16-bit unsigned integers"
  fields = parseFields(line, 0, 1)
  if len(fields) == 1: return parseu16(fields[0], simstate)

def getoptu16optu16(line, simstate=None):
  "Expecting zero-to-two 16-bit unsigned integers"
  fields = parseFields(line, 0, 2)
  if len(fields) == 1:
    return (parseu16(fields[0], simstate), None)
  elif len(fields) == 2:
    return parseu16(fields[0], simstate), parseu16(fields[1], simstate)
  return None, None

def getu8(line, simstate=None):
  "Expecting a single 8-bit unsigned integer"
  fields = parseFields(line, 1, 1)
  return parseu8(fields[0], simstate)
