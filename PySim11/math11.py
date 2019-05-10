'''
16-bit/8-bit math support functions
'''

def TwosC8ToInt(val):
  # Return integer representation of two's complement 8-bit number
  if val > 127: val = val - 256
  assert -128 <= val <= 127
  return val

def TwosC16ToInt(val):
  # Return integer representation of two's complement 16-bit number
  if val > 32767: val = val - 65536
  assert -32768 <= val <= 32767
  return val

def IntToTwosC8(val):
  # Return 8-bit representation of two's complement integer
  assert -128 <= val <= 127
  if val < 0: val = val + 256
  return val

def IntToTwosC16(val):
  # Return 16-bit representation of two's complement integer
  assert -32768 <= val <= 32767
  if val < 0: val = val + 65536
  return val
