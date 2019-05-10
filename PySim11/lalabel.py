'''
This module implements the name of a waveform in the logic analyzer frame
'''

## import all of the wxPython GUI package
import wx
import wx.lib.colourdb
wx.lib.colourdb.updateColourDB()

import types

#---------------------------------------------------------------------------

##############################################################
#
#     LALabel -- a logic analyzer label to accompany data
#

def _iswxColour(w):
  # I'm not sure of a good way to make sure something is
  # a wx.Colour object. isinstance(w, wx.Colour) doesn't
  # seem to work.
  return hasattr(w, 'Blue')

class LALabel(wx.Window):
  def __init__(self, parent, id, orig, size):
    super().__init__(parent, id, orig, size, wx.SUNKEN_BORDER)

    self.Bind(wx.EVT_PAINT,self.OnPaint) #EVT_PAINT(self, self.OnPaint)
    self.Bind(wx.EVT_SIZE,self.OnSize) #EVT_SIZE(self, self.OnSize)
    self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightClick) #EVT_RIGHT_DOWN(self, self.OnRightClick)
    self.Bind(wx.EVT_LEFT_DCLICK,self.OnLeftDoubleClick) #EVT_LEFT_DCLICK(self, self.OnLeftDoubleClick)

    self.textColor = wx.WHITE
    self.textWidth = 2
    self.backgroundColor = wx.Colour('DIM GREY')

    self.parent = parent
    self.label = ""

  def SetLabel(self, L):
    assert type(L) is types.StringType
    self.label = L

  def GetLabel(self): return self.label

  def OnLeftDoubleClick(self, event):
    self.parent.OnLeftDoubleClick(event, self)

  def OnRightClick(self, event):
    self.parent.OnRightClick(event, self)

  def GetTextColor(self): return self.textColor

  def SetTextColor(self, C):
    assert _iswxColour(C)
    self.textColor = C
    self.Refresh()

  def GetBackgroundColor(self): return self.backgroundColor

  def SetBackgroundColor(self, C):
    assert _iswxColour(C)
    self.backgroundColor = C
    self.Refresh()

  def GetTextWidth(self): return self.textWidth

  def SetTextWidth(self, W):
    assert type(W) is types.IntType
    assert W > 0
    self.textWidth = W
    self.Refresh()

  def OnPaint(self, event):
    dc = wx.PaintDC(self)
    (W, H) = self.GetClientSize()

    bg = wx.Brush(self.backgroundColor, wx.SOLID)
    dc.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
    dc.SetTextForeground(self.textColor)
    dc.SetTextBackground(self.backgroundColor)
    dc.SetBackground(bg)
    dc.Clear()
    (w,h) = dc.GetTextExtent(self.label)

    x = int((W-w)/2)
    y = int((H-h)/2)
    dc.DrawText(self.label, x, y)

  def OnSize(self, event): pass
