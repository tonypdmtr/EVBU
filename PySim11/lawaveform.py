#################################################################
#
# LAWaveform -- Grouping class for a label and data display

import types
import sys
import os.path

## import all of the wxPython GUI package
import wx

from PySim11.ladata import LAData
from PySim11.lalabel import LALabel
from PySim11.lawaveprops_dlg import LAWaveformProperties, PortInfo

_LA_LABELWIDTH = 100

class LAWaveform(wx.Window):
  def __init__(self, parent, id, orig, size, attr):
    super().__init__(parent, id, orig, size, attr)

    self.data = None     # Contains object of class LAData
    self.label = None    # Contains object of class LALabel
    self.stimfile = None # File name when an input, ignored when isinput == 0
    self.portpin = None  # String indicating name (e.g., 'PA6', 'PC3')
    self.isinput = 0     # May be 1 without stimulus file

    self.parent = parent

    self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightClick) #EVT_RIGHT_DOWN(self, self.OnRightClick)
    self.Bind(wx.EVT_LEFT_DCLICK,self.OnLeftDoubleClick) #EVT_LEFT_DCLICK(self, self.OnLeftDoubleClick)
    self.Bind(wx.EVT_SIZE,self.OnSize) #EVT_SIZE(self, self.OnSize)

  def FindNextEdgeFromX(self, x):
    if self.data: return self.data.FindNextEdgeFromX(x)

  def TrackCursor1(self, xpos):
    if self.data: self.data.TrackCursor1(xpos)

  def TrackCursor2(self, xpos):
    if self.data: self.data.TrackCursor2(xpos)

  def MinTime(self):
    assert not self.IsEmpty()
    assert self.data
    return self.data.MinTime()

  def MaxTime(self):
    assert not self.IsEmpty()
    assert self.data
    return self.data.MaxTime()

  def IsEmpty(self):
    if self.data: return self.data.IsEmpty()
    return 1

  def OnSize(self, event):
    if self.data:
      (myw,myh) = self.GetClientSize()
      (oldw, oldh) = self.data.GetSize()
      neww = myw - _LA_LABELWIDTH - 5
      if neww >= 100: self.data.SetSize(wx.Size(neww, oldh))
    event.Skip()

  def SetTickSpacing(self, spacing):
    if self.data: self.data.SetTickSpacing(spacing)

  def RefreshData(self):
    if self.data: self.data.Refresh()
    if self.label: self.label.Refresh()

  def GetPortPin(self): return self.portpin

  def GetEvents(self):
    if self.data: return self.data.GetEvents()
    return []

  def IsInput(self): return self.isinput

  def StimulusFile(self): return self.stimfile

  def Edit(self, lastPath):
    newPath = lastPath

    (w,h) = self.GetClientSize()

    d = LAWaveformProperties(self, -1, "Waveform Properties", wx.Point(-1,-1), lastPath)
    d.SetValues(self.portpin, self.stimfile)

    if d.ShowModal() == wx.ID_OK:
      dlgdata = d.SlurpData()
      if len(dlgdata['pin']) and dlgdata['pin'] != self.portpin:
        self.label = LALabel(self, -1, wx.Point(0, 0), wx.Size(_LA_LABELWIDTH, h))
        self.data = LAData(self, -1, wx.Point(_LA_LABELWIDTH+5, 0), wx.Size(w-_LA_LABELWIDTH-5,h))

        self.label.SetLabel(dlgdata['pin'])
        self.stimfile = dlgdata['filename']
        self.portpin = dlgdata['pin']
        self.isinput = ((dlgdata['IO'] == 'I') or ((dlgdata['IO'] == 'IO') and self.stimfile))
      elif dlgdata['filename'] != self.stimfile:
        self.stimfile = dlgdata['filename']
        self.isinput = ((dlgdata['IO'] == 'I') or ((dlgdata['IO'] == 'IO') and self.stimfile))

      if self.stimfile:
        newPath = os.path.dirname(self.stimfile)
        if len(newPath) == 0: newPath = lastPath

      return (1, newPath)
    return (0, None)

  def SetStartTime(self, T):
    assert type(T) in [types.IntType, types.LongType]
    assert self.data
    self.data.SetStartTime(T)

  def SetDivision(self, D):
    assert type(D) in [types.IntType, types.LongType]
    assert self.data
    self.data.SetDivision(D)

  def Append(self, T, V, autoRefresh=1):
    assert type(T) in [types.IntType, types.LongType]
    assert self.data
    self.data.Append(T, V, autoRefresh)

  def AppendRel(self, DT, V, autoRefresh=1):
    assert type(DT) in [types.IntType, types.LongType]
    assert self.data
    self.data.AppendRel(DT, V, autoRefresh)

  def SetLineColor(self, C): self.data.SetLineColor(C)
  def SetLabelColor(self, C): self.label.SetTextColor(C)
  def SetDataBackground(self, C): self.data.SetBackgroundColor(C)
  def SetLabelBackground(self, C): self.label.SetBackgroundColor(C)

  def OnLeftDoubleClick(self, event, subobject=None):
    if hasattr(self.parent, 'OnLeftDoubleClick'):
      self.parent.OnLeftDoubleClick(event, self, subobject)

  def OnRightClick(self, event, subobject=None):
    if hasattr(self.parent, 'OnRightClick'):
      self.parent.OnRightClick(event, self, subobject)

  def OnCycReset(self):
    if not self.isinput or not self.stimfile: self.data.Clear()

  def LoadStimulus(self):
    assert self.isinput

    if not self.stimfile:
      wx.MessageBox("You must first Edit this waveform to specify a stimulus file", "First things first", wx.OK|wx.CENTRE)
      return

    if self.data and not self.data.LoadFromFile(self.stimfile): pass # What to do?
