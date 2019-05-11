'''
This file implements the cursors in the logic analyzer panes
'''

## import all of the wxPython GUI package
import wx

import types
import sys

class LACursors(wx.Window):
  def __init__(self, parent, id, orig, size):
    super().__init__(parent, id, orig, size)
    self.parent = parent

    self.Bind(wx.EVT_PAINT,self.OnPaint)          #EVT_PAINT(self, self.OnPaint)
    self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftClick)  #EVT_LEFT_DOWN(self, self.OnLeftClick)
    self.Bind(wx.EVT_LEFT_UP,self.OnLeftUp)       #EVT_LEFT_UP(self, self.OnLeftUp)
    self.Bind(wx.EVT_MOTION,self.OnMouseMotion)   #EVT_MOTION(self, self.OnMouseMotion)

    self.startTime = 0
    self.division = 100000   # 100ns/div
    self.lineColor1 = wx.RED
    self.lineColor2 = wx.CYAN
    self.lineWidth = 1
    self.tickSpacing = 50     # pixels/division

    self.parent = parent

    self.pos1 = self.pos2 = None
    self.active = 1    # 1 for cursor 1, 2 for cursor 2
    self.grab = 0      # 1 for cursor 1, 2 for cursor 2

  def IsEnabled1(self): return self.pos1 is not None
  def IsEnabled2(self): return self.pos2 is not None

  def SetStartTime(self, T):
    assert repr(type(T)) == "<class 'int'>"
    self.startTime = T
    self.Refresh()

  def SetDivision(self, T):
    assert repr(type(T)) == "<class 'int'>"
    assert T > 0
    self.division = T
    self.Refresh()

  def SetTickSpacing(self, T):
    assert repr(type(T)) == "<class 'int'>"
    assert T > 0
    self.tickSpacing = T
    self.Refresh()

  def SetLineColors(self, args):
    self.lineColor1 = args[0]
    self.lineColor2 = args[1]
    self.Refresh()

  def SetLineWidth(self, W):
    assert type(W) is types.IntType
    assert W > 0
    self.lineWidth = W
    self.Refresh()

  def OnPaint(self, event):
    dc = wx.PaintDC(self)
    (w, h) = self.GetClientSize()
    (decorationDX,decorationDY) = self.parent.GetWaveformBorderSizes()

    # Compute number of pixels per unit time in the window.
    # We have 'division' as time/tick and 'tickSpacing' as
    # pixels/tick so we compute...
    dX = float(self.tickSpacing) / self.division

    dc.SetBackground(wx.Brush(self.parent.GetBackgroundColour(), wx.SOLID))
    dc.Clear()

    if self.pos1 is not None:
      x = int((self.pos1 - self.startTime)*dX + decorationDX)
      if 0 <= x <= w:
        dc.SetPen(wx.Pen(self.lineColor1, self.lineWidth, wx.SOLID))
        if self.active == 1: dc.SetBrush(wx.Brush(self.lineColor1, wx.SOLID))
        else: dc.SetBrush(wx.Brush(self.lineColor1, wx.TRANSPARENT))
        dc.DrawPolygon([wx.Point(0,h), wx.Point(-4,h-4), wx.Point(-4,0), wx.Point(4,0), wx.Point(4,h-4)], xoffset=x)

    if self.pos2 is not None:
      x = int((self.pos2 - self.startTime)*dX + decorationDX)
      if 0 <= x <= w:
        dc.SetPen(wx.Pen(self.lineColor2, self.lineWidth, wx.SOLID))
        if self.active == 2: dc.SetBrush(wx.Brush(self.lineColor2, wx.SOLID))
        else: dc.SetBrush(wx.Brush(self.lineColor2, wx.TRANSPARENT))
        dc.DrawPolygon([wx.Point(0,h), wx.Point(-4,h-4), wx.Point(-4,0), wx.Point(4,0), wx.Point(4,h-4)], xoffset=x)

  def GetC1Pos(self): return self.pos1 or 0
  def GetC2Pos(self): return self.pos2 or 0

  def SetC1Off(self):
    self.pos1 = None
    self.parent.TrackCursor1(None)
    self.Refresh()

  def SetC2Off(self):
    self.pos2 = None
    self.parent.TrackCursor2(None)
    self.Refresh()

  def SetC1Pos(self, x):
    # We get position in (x,y) co-ords, must convert to cycles

    # Compute number of pixels per unit time in the window.
    # We have 'division' as time/tick and 'tickSpacing' as
    # pixels/tick so we compute...
    dX = float(self.tickSpacing) / self.division
    self.pos1 = int(round(x/dX) + self.startTime)
    self.active = 1
    self.parent.TrackCursor1(self.pos1)
    self.Refresh()

  def SetC2Pos(self, x):
    # We get position in (x,y) co-ords, must convert to cycles

    # Compute number of pixels per unit time in the window.
    # We have 'division' as time/tick and 'tickSpacing' as
    # pixels/tick so we compute...
    dX = float(self.tickSpacing) / self.division
    self.pos2 = int(round(x/dX) + self.startTime)
    self.active = 2
    self.parent.TrackCursor2(self.pos2)
    self.Refresh()

  def SetC1PosCycles(self, x):
    self.pos1 = x
    self.parent.TrackCursor1(self.pos1)
    self.active = 1
    self.Refresh()

  def SetC2PosCycles(self, x):
    self.pos2 = x
    self.parent.TrackCursor2(self.pos2)
    self.active = 2
    self.Refresh()

  def OnLeftClick(self, event):
    x = event.GetX()
    dX = float(self.tickSpacing) / self.division
    pos = int(round(x / dX)) + self.startTime
    delta = int(round(4 / dX))

    if self.pos1 is not None:
      if self.pos1-delta <= pos <= self.pos1+delta:
        self.active = self.grab = 1
        self.CaptureMouse()
        self.Refresh()
        return

    if self.pos2 is not None:
      if self.pos2-delta <= pos <= self.pos2+delta:
        self.active = self.grab = 2
        self.CaptureMouse()
        self.Refresh()
        return

  def OnLeftUp(self, event):
    if self.grab: self.ReleaseMouse()
    self.grab = 0

  def OnMouseMotion(self, event):
    if not self.grab: return

    if not event.Dragging() or not event.LeftIsDown():
      self.grab = 0
      return

    dX = float(self.tickSpacing) / self.division
    pos = int(round(event.GetX() / dX) + self.startTime)

    if self.grab == 1:
      if pos != self.pos1:
        self.pos1 = pos
        self.Refresh()
        self.parent.TrackCursor1(self.pos1)
    elif self.grab == 2:
      if pos != self.pos2:
        self.pos2 = pos
        self.parent.TrackCursor2(self.pos2)
        self.Refresh()
