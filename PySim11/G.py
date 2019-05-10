'''
Global variables for PySim11
'''

# This is just a placeholder for global variables

# If set to 1, SWI instructions are executed like any other.
# Otherwise, execution stops with an exception.
UseSWI = 0

# Indicate whether or not to use the various peripherals.
Peripherals = {
  'Timer': [1, 'PySim11.pe_timer'],
  'ParallelIO': [1, 'PySim11.pe_pio']
}
