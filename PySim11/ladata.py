import types
import re

## import all of the wxPython GUI package
import wx
import wx.lib.colourdb
wx.lib.colourdb.updateColourDB()

#---------------------------------------------------------------------------

##############################################################
#
#     LAData -- a logic analyzer data display window
#
#     This class displays a single waveform in a logic analyzer
#     format. That is, only two levels (1 and 0) are allowed.
#     The class displays transitions as vertical edges.
#
#     The attributes of the logic analyzer window are:
#
#       startTime : GetStartTime, SetStartTime
#                   The first time point to draw
#
#       division  : GetDivision, SetDivision
#                   The number of time points in a "division".
#                   Divisions may be drawn in the window with tick
#                   marks.
#
#       tickSpacing : GetTickSpacing, SetTickSpacing
#                     The number of pixels between tick marks
#
#       lineColor : GetLineColor, SetLineColor
#                   The color of the line being drawn (wx.Colour object)
#
#       lineWidth : GetLineWidth, SetLineWidth
#                   The width of the lines being drawn
#
#       backgroundColor : GetBackgroundColor, SetBackgroundColor
#                   The color of the window background (wx.Colour object)
#
#       tickColor : GetTickColor, SetTickColor
#                   The color of tick marks (wx.Colour object)
#
#       events : see accessors below
#                 List of events to draw. Each event is a (T,V)
#                 tuple where T is the time (long) and V is the
#                 value (0 or 1). Events are sorted by ascending
#                 time.
#
#     The accessors that manipulate the events:
#
#       Clear()       : Remove all events
#       Append(T, V)  : Add an event at the given time. T must be
#                       larger than the most recent event.
#       AppendRel(DT, V) : Add an event DT time units from the most
#                          recent event.
#       IsEmpty()     : True if there are no events
#       MinTime()     : Minimum time of any event
#       MaxTime()     : Maximum time of any event
#       LoadFromFile() : Loads events from a file name

def _iswxColour(w):
  # I'm not sure of a good way to make sure something is
  # a wx.Colour object. isinstance(w, wx.Colour) doesn't
  # seem to work.
  return hasattr(w, 'Blue')

class LAData(wx.Window):
  def __init__(self, parent, id, orig, size):
    super().__init__(parent, id, orig, size, wx.SUNKEN_BORDER)

    self.Bind(wx.EVT_PAINT,self.OnPaint) #EVT_PAINT(self, self.OnPaint)
    self.Bind(wx.EVT_SIZE,self.OnSize) #EVT_SIZE(self, self.OnSize)
    self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightClick) #EVT_RIGHT_DOWN(self, self.OnRightClick)
    self.Bind(wx.EVT_LEFT_DCLICK,self.OnLeftDoubleClick) #EVT_LEFT_DCLICK(self, self.OnLeftDoubleClick)

    self.startTime = 0
    self.division = 100000   # 100ns/div
    self.lineColor = wx.WHITE
    self.lineWidth = 2
    self.backgroundColor = wx.BLACK
    self.tickSpacing = 50     # pixels/division
    self.tickColor = wx.YELLOW #ColourDatabase.FindColour('YELLOW')

    self.cursor1 = self.cursor2 = None

    self.events = []    # A list of (T,V) tuples where T are 'long' types (ascending) and V is 0 or 1

    self.parent = parent
    self.UpdateDX()

  def GetEvents(self): return self.events

  def FindNextEdgeFromX(self, x):
    cycles = int(round(x / self.dX)) + self.startTime
    for EV in self.events:
      if EV[0] >= cycles: return EV[0]

  def UpdateDX(self): self.dX = float(self.tickSpacing) / self.division

  def GetDX(self): return self.dX

  def OnLeftDoubleClick(self, event):
    self.parent.OnLeftDoubleClick(event, self)

  def OnRightClick(self, event): self.parent.OnRightClick(event, self)

  def MinTime(self):
    assert len(self.events)
    return self.events[0][0]

  def MaxTime(self):
    assert len(self.events)
    return self.events[-1][0]

  def IsEmpty(self): return not len(self.events)

  def GetStartTime(self): return self.startTime

  def SetStartTime(self, T):
    assert repr(type(T)) == "<class 'int'>"
    self.startTime = T
    self.Refresh()

  def GetDivision(self): return self.division

  def SetDivision(self, T):
    assert repr(type(T)) == "<class 'int'>"
    assert T > 0
    self.division = T
    self.UpdateDX()
    self.Refresh()

  def GetTickSpacing(self): return self.tickSpacing

  def SetTickSpacing(self, T):
    assert repr(type(T)) == "<class 'int'>"
    assert T > 0
    self.tickSpacing = T
    self.UpdateDX()
    self.Refresh()

  def GetLineColor(self): return self.lineColor

  def SetLineColor(self, C):
    assert _iswxColour(C)
    self.lineColor = C
    self.Refresh()

  def GetBackgroundColor(self):
    return self.backgroundColor

  def SetBackgroundColor(self, C):
    assert _iswxColour(C)
    self.backgroundColor = C
    self.Refresh()

  def GetTickColor(self): return self.tickColor

  def SetTickColor(self, C):
    assert _iswxColour(C)
    self.tickColor = C
    self.Refresh()

  def GetLineWidth(self): return self.lineWidth

  def SetLineWidth(self, W):
    assert type(W) is types.IntType
    assert W > 0
    self.lineWidth = W
    self.Refresh()

  def TrackCursor1(self, xpos):
    oldpos = self.cursor1
    self.cursor1 = xpos
    (w, h) = self.GetClientSize()

    if oldpos is not None and self.cursor1 is not None:
      T1 = int((self.cursor1 - self.startTime)*self.dX)
      T2 = int((oldpos - self.startTime)*self.dX)
      if T1 > T2: T1,T2 = T2,T1
      self.Refresh(1, wx.Rect(T1, 0, T2-T1+1, h))
    elif self.cursor1 is not None:
      T1 = int((self.cursor1 - self.startTime)*self.dX)
      self.Refresh(1, wx.Rect(T1-2, 0, 5, h))
    elif oldpos is not None:
      T1 = int((oldpos - self.startTime)*self.dX)
      self.Refresh(1, wx.Rect(T1-2, 0, 5, h))
    else: self.Refresh()

  def TrackCursor2(self, xpos):
    oldpos = self.cursor2
    self.cursor2 = xpos
    (w, h) = self.GetClientSize()

    if oldpos is not None and self.cursor2 is not None:
      T1 = int((self.cursor2 - self.startTime)*self.dX)
      T2 = int((oldpos - self.startTime)*self.dX)
      if T1 > T2: T1, T2 = T2, T1
      self.Refresh(1, wx.Rect(T1, 0, T2-T1+1, h))
    elif self.cursor2 is not None:
      T1 = int((self.cursor2 - self.startTime)*self.dX)
      self.Refresh(1, wx.Rect(T1-2, 0, 5, h))
    elif oldpos is not None:
      T1 = int((oldpos - self.startTime)*self.dX)
      self.Refresh(1, wx.Rect(T1-2, 0, 5, h))
    else: self.Refresh()

  def OnPaint(self, event):
    dc = wx.PaintDC(self)
    (w, h) = self.GetClientSize()
    YVal = [h-4, 4]  # Mapping from (0,1) to pixel positions

    dc.SetPen(wx.Pen(self.lineColor, self.lineWidth, wx.SOLID))
    dc.SetBackground(wx.Brush(self.backgroundColor, wx.SOLID))

    region = self.GetUpdateRegion()
    dc.SetClippingRegionAsRegion(region)

    dc.Clear()

    oldT = 0
    oldV = -1
    for ev in self.events:
      newT = int((ev[0]-self.startTime)*self.dX)
      newV = ev[1]

      if newT < 0:
        oldV = newV
        continue

      if newT > w:
        if oldV != -1: dc.DrawLine(oldT, YVal[oldV], w, YVal[oldV])
        break

      if oldV == -1: oldV = 1 - newV

      # Advance the line
      dc.DrawLine(oldT, YVal[oldV], newT, YVal[oldV])

      # Draw a transition, if necessary
      if (oldV != newV): dc.DrawLine(newT, YVal[oldV], newT, YVal[newV])

      oldT = newT
      oldV = newV
    # end for

    # Continue drawing up to end of window if the last event stopped
    # before this point.
    if (oldT < w) and (oldV != -1):
      dc.DrawLine(oldT, YVal[oldV], w, YVal[oldV])

    # Draw tick marks
    firstTime = (self.startTime / self.division) * self.division
    if firstTime < self.startTime: firstTime = firstTime + self.division

    dc.SetPen(wx.Pen(self.tickColor, 1, wx.SOLID))
    if self.events:
      while 1:
        T = int((firstTime - self.startTime)*self.dX)
        if T > w: break
        dc.DrawLine(T, 0, T, 4)
        dc.DrawLine(T, h-4, T, h)
        firstTime += self.division

    # Draw cursors
    if self.cursor1 is not None:
      T = int((self.cursor1 - self.startTime)*self.dX)
      dc.SetPen(wx.RED_PEN)
      dc.DrawLine(T, 0, T, h)
    if self.cursor2 is not None:
      T = int((self.cursor2 - self.startTime)*self.dX)
      dc.SetPen(wx.Pen(wx.CYAN, 1, wx.SOLID))
      dc.DrawLine(T, 0, T, h)

  def Clear(self):
    self.events = []
    self.Refresh()

  def Append(self, T, V, autoRefresh=1):
    assert V == 0 or V == 1
    assert repr(type(T)) == "<class 'int'>"

    if self.events: assert T > self.events[-1][0]
    self.events.append((T, V))
    if autoRefresh: self.Refresh()

  def AppendRel(self, DT, V, autoRefresh=1):
    assert V == 0 or V == 1
    assert type(DT) in [types.LongType, types.IntType]
    assert DT > 0

    if self.events: self.events.append((self.events[-1][0]+DT, V))
    else: self.events.append((DT, V))
    if autoRefresh: self.Refresh()

  def OnSize(self, event): pass

  def LoadFromFile(self, filename):
    events = []
    try: fid = open(filename, 'r')
    except IOError as detail:
      wx.MessageBox('%s: "%s"' % (detail.strerror, detail.filename), "You lose", wx.OK|wx.CENTRE)
      return 0

    try: lines = fid.readlines()
    except IOError as detail:
      wx.MessageBox('%s: "%s"' % (detail.strerror, filename), "You lose", wx.OK|wx.CENTRE)
      return 0

    fid.close()

    pat = r'^\s*(\d+)\s+(0|1)'      # CycleNumber Value
    pat_c = re.compile(pat)
    comment = r'^\s*(?:#.*)?$'
    comment_c = re.compile(comment)

    linenum = 0
    for line in lines:
      linenum += 1
      match = pat_c.match(line)
      if match is None:
        if comment_c.match(line) is None:
          wx.MessageBox('Error at "%s" line %d\nLine is not in the format\n"CYCLE ZeroOrOne"' % (filename, linenum), "Bad file format", wx.OK|wx.CENTRE)
          return 0
        else: continue

      cycle = long(match.group(1))
      val   = int(match.group(2))

      if events:
        if cycle <= events[-1][0]:
          wx.MessageBox('Error at "%s" line %d\nCycle time not in ascending order' % (filename, linenum), "Bad file format", wx.OK|wx.CENTRE)
          return 0

        if val != events[-1][1]: events.append((cycle, val))
      else: events.append((cycle, val))

    # end for

    self.events = events
    self.Refresh()

    return 1
