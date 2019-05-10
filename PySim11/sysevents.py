'''
This class implements a publish/subscribe mechanism for system events.
These include "real" events, like OC1F getting set and meta-events,
like simulation starting/stopping.
'''

from safestruct import SafeStruct

class SystemEvents(SafeStruct):

  def __init__(self):
    super().__init__({
      'OC1': 'OC1',              # Events OC1 through OC5 sometimes take an extra parameter to notifyEvent
      'OC2': 'OC2',              # indicating the exact simulator cycle of the event.
      'OC3': 'OC3',
      'OC4': 'OC4',
      'OC5': 'OC5',
      'IC1': 'IC1',              # Events IC1 through IC4 take an extra time parameter to notifyEvent
      'IC2': 'IC2',              # and, consequently, at each handler.
      'IC3': 'IC3',
      'IC4': 'IC4',
      'TOV': 'TOV',
      'RTI': 'RTI',
      'PAI': 'PAI',
      'PAOV':'PAOV',
      'SimStart': 'SimStart',    # Simulation begins/ends
      'SimEnd':   'SimEnd',
      'CycReset': 'CycReset',    # Cycle counters reset to 0
      'CharWait': 'CharWait',    # inchar() has been called, waiting for a keypress
      'NoCharWait':'NoCharWait', # character received, no longer waiting
      'handlers': {}
      })

  def addHandler(self, event, handler):
    assert hasattr(self, event)
    try: self.handlers[event].append(handler)
    except: self.handlers[event] = [handler]

  def notifyEvent(self, event, args=()):
    assert hasattr(self, event)
    if event in self.handlers:
      for h in self.handlers[event]: h(*(event,)+args)
