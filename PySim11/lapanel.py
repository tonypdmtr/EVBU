'''
The panel is the main window in a LAFrame.
'''

## import all of the wxPython GUI package
import wx
import wx.lib.colourdb
wx.lib.colourdb.updateColourDB()

import operator
import types
import sys
import queue as Queue

from PySim11.lawaveform import LAWaveform
from PySim11.ladata     import LAData
from PySim11.lalabel    import LALabel
from PySim11.lacursors  import LACursors

#---------------------------------------------------------------------------

##############################################################
#
#     LAPanel -- A panel for LAData displays and controls
#
#  This class displays controls and LAData windows for several
#  lines of data.

_LA_TOP_Y      = 70
_LA_HEIGHT     = 50
_LA_VSPACING   = 55

# Colors for successive traces
_LA_DATA_COLORS = [
  wx.WHITE, wx.RED, wx.BLUE, wx.GREEN, wx.CYAN, wx.YELLOW,
  wx.Colour('MAGENTA'),                      #wx.MAGENTA
  wx.Colour('PINK')                          #wx.PINK
  ]
_LA_LAST_COLOR = -1

# Background color definitions for input waveforms and output waveforms
_LA_INDATA_COLOR = wx.Colour('DIM GRAY')
_LA_OUTDATA_COLOR = wx.BLACK

class LAPanel(wx.Panel):
  # Future support for time units?
  Cycles = 1
  Ms     = 2
  Us     = 3
  Ns     = 4

  def __init__(self, parent, id, orig, size, attr):
    super().__init__(parent, id, orig, size, attr)
    self.parent = parent

    (w,h) = self.GetClientSize()
    self.cursors = LACursors(self, -1, wx.Point(5+100+5, _LA_TOP_Y-10), wx.Size(w-5-100-5-5, 10))
    self.isSimulating = 0

    # The PySim11 thread calls our functions to post window update
    # commands using this queue. We use a fake button with ID
    # of 301. The event handler for this button pulls an object
    # from the queue. Each object in the queue is a 2-tuple
    # (func, parms) which is simply invoked as func(*parms)
    # in the handler.
    self.queue = Queue.Queue(0)

    # E-clock frequency. Not used right now.
    self.fE = 2.0e6

    # Pathnames for *.STI files
    self.lastSTIPath = "."

    self.Bind(wx.EVT_SIZE,self.OnSize) #EVT_SIZE(self, self.OnSize)
    self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightClick) #EVT_RIGHT_DOWN(self, self.OnRightClick)
    self.Bind(wx.EVT_LEFT_DCLICK,self.OnLeftDoubleClick) #EVT_LEFT_DCLICK(self, self.OnLeftDoubleClick)

    # Right-click pop-up menu handlers, some also correspond to main menu items
    self.Bind(wx.EVT_MENU,self.OnAddTrace) #EVT_MENU(self, 401, self.OnAddTrace)
    self.Bind(wx.EVT_MENU,self.OnAddTrace) #EVT_MENU(parent, 401, self.OnAddTrace)
    self.Bind(wx.EVT_MENU,self.OnDeleteTrace) #EVT_MENU(self, 402, self.OnDeleteTrace)
    self.Bind(wx.EVT_MENU,self.OnEditTrace) #EVT_MENU(self, 403, self.OnEditTrace)
    self.Bind(wx.EVT_MENU,self.OnReloadStimulus) #EVT_MENU(self, 404, self.OnReloadStimulus)
    self.Bind(wx.EVT_MENU,self.OnC1Here) #EVT_MENU(self, 405, self.OnC1Here)
    self.Bind(wx.EVT_MENU,self.OnC2Here) #EVT_MENU(self, 406, self.OnC2Here)
    self.Bind(wx.EVT_MENU,self.OnC1ToNextEdge) #EVT_MENU(self, 407, self.OnC1ToNextEdge)
    self.Bind(wx.EVT_MENU,self.OnC2ToNextEdge) #EVT_MENU(self, 408, self.OnC2ToNextEdge)
    self.Bind(wx.EVT_MENU,self.OnZoomInHere) #EVT_MENU(self, 409, self.OnZoomInHere)

    self.startTime = 0
    self.division = 100       # cycles/division
    self.tickSpacing = 50      # pixels/division
    self.units = LAPanel.Cycles
    self.cursors.SetDivision(self.division)
    self.cursors.SetTickSpacing(self.tickSpacing)

    # self.waveforms contains LAWaveform objects
    self.waveforms = []

    self.clickxy = None
    self.clickwaveform = None
    self.clickwobj = None

    # These methods of arranging things on the screen is yucky, but I'm not
    # familiar enough with the whole layout constraints thing to do it the
    # "right" way just yet.

    # Start time text control
    wx.StaticBox(self, -1, "Start Time",                    wx.Point(5,   10), wx.Size(176,40))
    self.startTimeText = wx.TextCtrl(self, 100, "0",        wx.Point(10,  25), wx.Size(68,20), wx.TE_PROCESS_ENTER)
    self.startTimeUnits = wx.StaticText(self, -1, "cyc",    wx.Point(80,  28), wx.Size(25,20))
    self.startTimePDivButton = wx.Button(self, 111, "+div", wx.Point(105, 19), wx.Size(37,15))
    self.startTimeMDivButton = wx.Button(self, 112, "-div", wx.Point(140, 19), wx.Size(37,15))
    self.startTimeZeroButton = wx.Button(self, 101, "zero", wx.Point(105, 33), wx.Size(72,15))

    self.Bind(wx.EVT_TEXT_ENTER,self.OnStartTimeChange) #EVT_TEXT_ENTER(self, 100, self.OnStartTimeChange)
    self.Bind(wx.EVT_BUTTON,self.OnZeroStartTime) #EVT_BUTTON(self, 101, self.OnZeroStartTime)
    self.Bind(wx.EVT_BUTTON,self.OnPDiv) #EVT_BUTTON(self, 111, self.OnPDiv)
    self.Bind(wx.EVT_BUTTON,self.OnMDiv) #EVT_BUTTON(self, 112, self.OnMDiv)

    # Division text control
    wx.StaticBox(self, -1, "Scale",                         wx.Point(186, 10), wx.Size(134,40))
    self.divisionText = wx.TextCtrl(self, 102, "100",       wx.Point(191,25),  wx.Size(68,20), wx.TE_PROCESS_ENTER)
    self.divisionUnits = wx.StaticText(self, -1, "cyc/div", wx.Point(262,28),  wx.Size(50,20))

    self.Bind(wx.EVT_TEXT_ENTER,self.OnDivisionChange, id=102) #EVT_TEXT_ENTER(self, 102, self.OnDivisionChange)

    # Zoom buttons
    wx.StaticBox(self, -1, "Zoom",                          wx.Point(325, 10), wx.Size(165,40))
    self.zoomInButton = wx.Button(self, 103, "In",          wx.Point(380, 19), wx.Size(50,15))
    self.zoomOutButton = wx.Button(self, 104, "Out",        wx.Point(380, 33), wx.Size(50,15))
    self.zoomAllButton = wx.Button(self, 105, "All",        wx.Point(435, 19), wx.Size(50,15))
    self.zoomMaxButton = wx.Button(self, 106, "Max",        wx.Point(435, 33), wx.Size(50,15))

    self.Bind(wx.EVT_BUTTON,self.OnZoomIn, id=103) #EVT_BUTTON(self, 103, self.OnZoomIn)
    self.Bind(wx.EVT_BUTTON,self.OnZoomOut, id=104) #EVT_BUTTON(self, 104, self.OnZoomOut)
    self.Bind(wx.EVT_BUTTON,self.OnZoomAll, id=105) #EVT_BUTTON(self, 105, self.OnZoomAll)
    self.Bind(wx.EVT_BUTTON,self.OnZoomMax, id=106) #EVT_BUTTON(self, 106, self.OnZoomMax)

    ##############
    # Cursors
    ##############
    wx.StaticBox(self, -1, "Cursors",                       wx.Point(495, 10), wx.Size(325,40))
    wx.StaticText(self, -1, "C1",                           wx.Point(500, 30), wx.Size(20, 15))
    self.c1TimeText = wx.TextCtrl(self, 113, "0",           wx.Point(520, 26), wx.Size(70, 20), wx.TE_PROCESS_ENTER)
    wx.StaticText(self, -1, "C2",                           wx.Point(600, 30), wx.Size(20, 15))
    self.c2TimeText = wx.TextCtrl(self, 114, "0",           wx.Point(620, 26), wx.Size(70, 20), wx.TE_PROCESS_ENTER)
    wx.StaticText(self, -1, "C2-C1",                        wx.Point(700, 30), wx.Size(45, 15))
    self.deltaCTimeText = wx.TextCtrl(self, 115, "0",       wx.Point(745, 26), wx.Size(70, 20), wx.TE_READONLY)

    self.Bind(wx.EVT_TEXT_ENTER,self.OnTextC1,id=113) #EVT_TEXT_ENTER(self, 113, self.OnTextC1)
    self.Bind(wx.EVT_TEXT_ENTER,self.OnTextC2,id=114) #EVT_TEXT_ENTER(self, 114, self.OnTextC2)

    # From future import...

    # Units radio buttons
    #wx.StaticBox(self, -1, "Units",                         wx.Point(495, 10), wx.Size(165,40))
    #self.unitsCycRadio = wx.RadioButton(self, 107, "cycles",wx.Point(540, 18), wx.Size(65, 15))
    #self.unitsMsRadio  = wx.RadioButton(self, 108, "ms",    wx.Point(605, 18), wx.Size(50, 15))
    #self.unitsUsRadio  = wx.RadioButton(self, 109, "us",    wx.Point(540, 33), wx.Size(50, 15))
    #self.unitsNsRadio  = wx.RadioButton(self, 110, "ns",    wx.Point(605, 33), wx.Size(50, 15))

    #self.Bind(wx.EVT_BUTTON,self.OnUnitsCyc,id=107) #EVT_BUTTON(self, 107, self.OnUnitsCyc)
    #self.Bind(wx.EVT_BUTTON,self.OnUnitsMs,id=108) #EVT_BUTTON(self, 108, self.OnUnitsMs)
    #self.Bind(wx.EVT_BUTTON,self.OnUnitsUs,id=109) #EVT_BUTTON(self, 109, self.OnUnitsUs)
    #self.Bind(wx.EVT_BUTTON,self.OnUnitsNs,id=110) #EVT_BUTTON(self, 110, self.OnUnitsNs)

    # Fake button used for inter-thread communication
    self.Bind(wx.EVT_BUTTON,self.Queue_handler,id=301) #EVT_BUTTON(self, 301, self.Queue_handler)

    ######
    # Menu bar and accelerators. Note that we are installing a menu
    # bar for our parent, an LAFrame. Now why is this? Why doesn't this code
    # migrate up to laframe.py?
    ######
    parent.menubar = wx.MenuBar()

    waveformMenu = wx.Menu()
    waveformMenu.Append(401, "&Add waveform...\tCtrl-A", "Add a waveform")
    parent.menubar.Append(waveformMenu, "&Waveform")
    self.waveformMenu = waveformMenu

    viewMenu = wx.Menu()
    viewMenu.Append(201, "&Zero\tCtrl-Z", "Set start time to 0")
    viewMenu.Append(211, "&+Div", "Increase start time by one division (also Shift-Right)")
    viewMenu.Append(212, "&-Div", "Decrease start time by one division (also Shift-Left)")
    viewMenu.AppendSeparator()
    viewMenu.Append(203, "Zoom &in\tPage_Up", "Zoom in to the waveforms")
    viewMenu.Append(204, "Zoom &out\tPage_Down", "Zoom out of the waveforms")
    viewMenu.Append(206, "Zoom &max\tCtrl-Page_Up", "Zoom in so one division is approximately one window-width")
    viewMenu.Append(205, "Zoom &all\tCtrl-Page_Down", "Zoom out to view all data")
    viewMenu.AppendSeparator()
    viewMenu.Append(207, "Cursor 1\tCtrl-1", "View or hide cursor 1", 1)
    viewMenu.Append(208, "Cursor 2\tCtrl-2", "View or hide cursor 2", 1)
    parent.menubar.Append(viewMenu, "&View")
    self.viewMenu = viewMenu

    parent.SetMenuBar(parent.menubar)

    self.Bind(wx.EVT_MENU,self.OnZeroStartTime,id=201) #EVT_MENU(parent, 201, self.OnZeroStartTime)
    self.Bind(wx.EVT_MENU,self.OnPDiv,id=211) #EVT_MENU(parent, 211, self.OnPDiv)
    self.Bind(wx.EVT_MENU,self.OnMDiv,id=212) #EVT_MENU(parent, 212, self.OnMDiv)
    self.Bind(wx.EVT_MENU,self.OnZoomIn,id=203) #EVT_MENU(parent, 203, self.OnZoomIn)
    self.Bind(wx.EVT_MENU,self.OnZoomOut,id=204) #EVT_MENU(parent, 204, self.OnZoomOut)
    self.Bind(wx.EVT_MENU,self.OnZoomAll,id=205) #EVT_MENU(parent, 205, self.OnZoomAll)
    self.Bind(wx.EVT_MENU,self.OnZoomMax,id=206) #EVT_MENU(parent, 206, self.OnZoomMax)
    self.Bind(wx.EVT_MENU,self.OnCursor1,id=207) #EVT_MENU(parent, 207, self.OnCursor1)
    self.Bind(wx.EVT_MENU,self.OnCursor2,id=208) #EVT_MENU(parent, 208, self.OnCursor2)

    accel = wx.AcceleratorTable([ \
              (wx.ACCEL_CTRL, ord('a'), 401), \
              (wx.ACCEL_CTRL, ord('z'), 201), \
              (wx.ACCEL_NORMAL, wx.WXK_PAGEUP, 203), \
              (wx.ACCEL_NORMAL, wx.WXK_PAGEDOWN, 204), \
              (wx.ACCEL_CTRL, wx.WXK_PAGEUP, 206), \
              (wx.ACCEL_CTRL, wx.WXK_PAGEDOWN, 205), \
              (wx.ACCEL_CTRL, ord('1'), 207), \
              (wx.ACCEL_CTRL, ord('2'), 208), \
              (wx.ACCEL_SHIFT, wx.WXK_RIGHT, 211), \
              (wx.ACCEL_SHIFT, wx.WXK_LEFT, 212)])
    parent.SetAcceleratorTable(accel)

  def OnPDiv(self, event):
    self.startTimeText.SetValue(str(self.startTime+self.division))
    self.SetStartTime(self.startTime + self.division)

  def OnMDiv(self, event):
    self.startTimeText.SetValue(str(self.startTime-self.division))
    self.SetStartTime(self.startTime - self.division)

  def Cyc2Units(self, u):
    if self.units == LAPanel.Cycles: return u
    elif self.units == LAPanel.Ms: return u / self.fE * 1000
    elif self.units == LAPanel.Us: return u / self.fE * 1e6
    elif self.units == LAPanel.Ns: return u / self.fE * 1e9
    assert 0, "Unknown units in LAPanel"

  def Units2Cyc(self, u):
    if self.units == LAPanel.Cycles: return u
    elif self.units == LAPanel.Ms: return u * self.fE / 1000
    elif self.units == LAPanel.Us: return u * self.fE / 1e6
    elif self.units == LAPanel.Ns: return u * self.fE / 1e9
    assert 0, "Unknown units in LAPanel"

  def OnUnitsCyc(self, event): pass
  def OnUnitsMs(self, event): pass
  def OnUnitsUs(self, event): pass
  def OnUnitsNs(self, event): pass

  def OnZoomOut(self, event):
    newSpacing = self.tickSpacing*4/5
    newSpacing = max(newSpacing,2)
    if newSpacing != self.tickSpacing:
      self.SetTickSpacing(newSpacing)
    else:
      wx.MessageBox("Minimum zoom reached. Increase the scale to see more of the waveform.", "Whoa, there", wx.OK|wx.CENTRE)

  def OnZoomIn(self, event):
    newSpacing = self.tickSpacing*5/4
    if newSpacing == self.tickSpacing: newSpacing = self.tickSpacing+1
    self.SetTickSpacing(newSpacing)

  def OnZoomInHere(self, event):
    assert self.clickwaveform
    assert self.clickwobj
    assert isinstance(self.clickwobj, LAData)

    # Compute what cycle number the user clicked on
    dX = self.clickwobj.GetDX()
    cycles = int(round(self.clickxy[0]/dX)) + self.startTime

    # Then, zoom in
    self.OnZoomIn(None)

    # Only now, we can compute the new dX, scaling factor
    # of pixels/cycle.
    dX = self.clickwobj.GetDX()

    # Now, adjust start time so that desired cycle position is in the middle
    # of the window. We want:
    #    (cycles - startTime)[cycles] * dX[pixels/cycle] = w/2
    (w,h) = self.clickwobj.GetClientSize()
    newStartTime = int(round(cycles - w/(2.0*dX)))
    self.SetStartTime(newStartTime)
    self.startTimeText.SetValue(str(newStartTime))

  def OnZoomAll(self, event):
    if len(self.waveforms) == 0: return

    (width,h) = self.waveforms[0].data.GetClientSize()

    # Try to make w = T [pixels/div] * (1/D) [div/cycles] * C [cycles]
    # where T=tickSpacing, D=division, C=total # of cycles in the data
    # waveforms
    minT = maxT = None
    for w in self.waveforms:
      if not w.IsEmpty():
        if minT is None:
          minT = w.MinTime()
          maxT = w.MaxTime()
        else:
          minT = min(minT, w.MinTime())
          maxT = max(maxT, w.MaxTime())

    if minT is None: return

    if minT < self.startTime:
      self.startTimeText.SetValue(str(minT))
      self.SetStartTime(minT)
    minT = min(minT, self.startTime)

    T = int(width * self.division / (maxT-minT+1))
    T = max(T,2)
    self.SetTickSpacing(T)

  def OnZoomMax(self, event):
    # I'm not sure what I mean with this code. The tick spacing
    # derived here doesn't have a particular optimality to it.
    (w,h) = self.GetClientSize()
    w = w - 10
    if w >= 2: self.SetTickSpacing(w)

  def SetTickSpacing(self, spacing):
    assert type(spacing) is types.IntType
    assert spacing > 0
    self.tickSpacing = spacing
    for w in self.waveforms: w.SetTickSpacing(spacing)
    self.cursors.SetTickSpacing(spacing)

  def GetStartTime(self): return self.startTime

  def SetStartTime(self, T):
    assert type(T) is int
    self.startTime = T
    for D in self.waveforms: D.SetStartTime(T)
    self.cursors.SetStartTime(T)

  def GetDivision(self): return self.division

  def SetDivision(self, T):
    assert type(T) is int
    assert T > 0
    self.division = T
    for D in self.waveforms: D.SetDivision(T)
    self.cursors.SetDivision(T)

  def OnSize(self, event):
    (w,h) = self.GetClientSize()
    w = w - 10
    if w >= 100:
      for wave in self.waveforms:
        (oldw, h) = wave.GetSize()
        wave.SetSize(wx.Size(w,h))
      self.cursors.SetSize(wx.Size(w-5-100, 10))

  def OnZeroStartTime(self, event):
    self.startTimeText.SetValue("0")
    self.SetStartTime(0)

  def OnStartTimeChange(self, event):
    try:
      val = int(self.startTimeText.GetValue())
      self.SetStartTime(val)
    except:
      self.startTimeText.SetValue(str(self.startTime))

  def OnDivisionChange(self, event):
    try:
      val = int(self.divisionText.GetValue())
      self.SetDivision(val)
    except:
      self.divisionText.SetValue(str(self.division))

  def OnRightClick(self, event, waveform=None, wobj=None):
    '''This is either called from a right-click event in the panel proper
    or as a right-click event from an LALabel or LAData propagated
    upward. In the latter case, wobj is the instance of the object that
    first generated the event, waveform is the instance of the
    LAWaveform object that contains it, and the 'event' parameter is the original
    event so event.GetPosition() is (x,y) relative to the sub-object's
    co-ordinates. Note that waveform may be non-None while wobj may
    be None, in case the user clicks in the space between label and data.'''

    if self.isSimulating: return

    m = wx.Menu()
    (x,y) = event.GetPosition()

    m.Append(401, "Add waveform...")
    if waveform:
      # (x,y) are relative to this object
      m.AppendSeparator()
      m.Append(402, "Delete waveform")
      m.Append(403, "Edit waveform...")
      m.AppendSeparator()
      m.Append(404, "Reload stimulus")
      if not waveform.IsInput(): m.Enable(404, 0)
      if wobj and isinstance(wobj, LAData):
        m.AppendSeparator()
        m.Append(405, "Cursor 1 here")
        m.Append(406, "Cursor 2 here")
        m.Append(407, "Cursor 1 to next edge")
        m.Append(408, "Cursor 2 to next edge")
        m.Append(409, "Zoom in here")

    # Finally, we need to compute where, with respect to LAPanel,
    # we need to pop up this menu.
    (mx,my) = (x,y)
    if waveform:
      if wobj:
        (dx,dy) = wobj.GetPositionTuple()
        mx = x + dx
        my = y + dy
      (dx,dy) = waveform.GetPositionTuple()
      mx = x + dx
      my = y + dy

    self.clickxy = (x,y)
    self.clickwaveform = waveform
    self.clickwobj = wobj
    self.PopupMenu(m,(mx,my))
    self.clickxy = None
    self.clickwaveform = None
    self.clickwobj = None

  # Same comments apply as for OnRightClick
  def OnLeftDoubleClick(self, event, waveform=None, wobj=None):
    if waveform:
      self.clickwaveform = waveform
      self.OnEditTrace(event)
      self.clickwaveform = None

  def OnCursor1(self, event):
    if self.cursors.IsEnabled1():
      self.cursors.SetC1Off()
      self.parent.menubar.Check(207, 0)
    else:
      self.cursors.SetC1Pos(self.startTime + 3*self.division)
      self.parent.menubar.Check(207, 1)

  def OnCursor2(self, event):
    if self.cursors.IsEnabled2():
      self.cursors.SetC2Off()
      self.parent.menubar.Check(208, 0)
    else:
      self.cursors.SetC2Pos(self.startTime + 4*self.division)
      self.parent.menubar.Check(208, 1)

  def OnC1Here(self, event):
    assert self.clickwaveform

    x = self.clickxy[0]
    self.cursors.SetC1Pos(x)
    self.parent.menubar.Check(207, 1)

  def OnC2Here(self, event):
    assert self.clickwaveform

    x = self.clickxy[0]
    self.cursors.SetC2Pos(x)
    self.parent.menubar.Check(208, 1)

  def OnC1ToNextEdge(self, event):
    assert self.clickwaveform

    x = self.clickxy[0]
    nextedge = self.clickwaveform.FindNextEdgeFromX(x)
    if nextedge is None:
      wx.MessageBox("No waveform edges exist past this point", "Outta luck", wx.OK|wx.CENTRE)
      return

    self.cursors.SetC1PosCycles(nextedge)
    self.parent.menubar.Check(207, 1)

  def OnC2ToNextEdge(self, event):
    assert self.clickwaveform

    x = self.clickxy[0]
    nextedge = self.clickwaveform.FindNextEdgeFromX(x)
    if nextedge is None:
      wx.MessageBox("No waveform edges exist past this point", "Outta luck", wx.OK|wx.CENTRE)
      return

    self.cursors.SetC2PosCycles(nextedge)
    self.parent.menubar.Check(208, 1)

  def GetWaveformBorderSizes(self):
    if len(self.waveforms):
      wave = self.waveforms[0]
      (w,h) = wave.data.GetClientSize()
      (ww,wh) = wave.data.GetSize()

      return ((ww-w)/2.0, (wh-h)/2.0)
    return (0,0)

  def UpdateCursorsText(self, c1=None, c2=None):
    if c1 is not None: self.c1TimeText.SetValue(str(c1))
    if c2 is not None: self.c2TimeText.SetValue(str(c2))
    c1 = self.cursors.GetC1Pos()
    c2 = self.cursors.GetC2Pos()
    self.deltaCTimeText.SetValue(str(c2-c1))

  def TrackCursor1(self, xpos):
    c1 = xpos
    if xpos is None: c1 = 0

    self.UpdateCursorsText(c1=c1)
    self.c1TimeText.SetValue(str(c1))
    for w in self.waveforms: w.TrackCursor1(xpos)

  def TrackCursor2(self, xpos):
    c2 = xpos
    if xpos is None: c2 = 0
    self.UpdateCursorsText(c2=c2)
    self.c2TimeText.SetValue(str(c2))
    for w in self.waveforms: w.TrackCursor2(xpos)

  def OnAddTrace(self, event):
    global _LA_LAST_COLOR

    (w,h) = self.GetClientSize()
    ix = len(self.waveforms)

    w = LAWaveform(self, -1, wx.Point(5, _LA_TOP_Y+ix*_LA_VSPACING), wx.Size(w-10, _LA_HEIGHT), 0)

    # Open dialog to set properties
    (isOK, newPath) = w.Edit(self.lastSTIPath)

    if isOK:
      self.waveforms.append(w)
      w.SetStartTime(self.startTime)
      w.SetDivision(self.division)
      w.SetTickSpacing(self.tickSpacing)

      _LA_LAST_COLOR = (_LA_LAST_COLOR+1) % len(_LA_DATA_COLORS)
      color = _LA_DATA_COLORS[_LA_LAST_COLOR]
      w.SetLineColor(color)
      w.SetLabelColor(color)

      if w.IsInput():
        w.SetLabelBackground(_LA_INDATA_COLOR)
        w.SetDataBackground(_LA_INDATA_COLOR)
        if w.StimulusFile(): w.LoadStimulus()
      else:
        w.SetLabelBackground(_LA_OUTDATA_COLOR)
        w.SetDataBackground(_LA_OUTDATA_COLOR)

      w.Show(1)

      if newPath: self.lastSTIPath = newPath

      if 0:                                       # Just for testing
        w.Append(0, 0)
        w.Append(20, 1)
        w.Append(30, 0)
        w.Append(40, 1)

  def OnDeleteTrace(self, event):
    assert self.clickwaveform
    for i in range(len(self.waveforms)):
      if self.clickwaveform is self.waveforms[i]:
        (oldX,oldY) = self.waveforms[i].GetPositionTuple()
        self.waveforms[i].Destroy()
        break
    assert i < len(self.waveforms)

    for j in range(i,len(self.waveforms)-1):
      self.waveforms[j] = self.waveforms[j+1]

      (newX, newY) = self.waveforms[j].GetPositionTuple()
      self.waveforms[j].MoveXY(oldX, oldY)
      (oldX, oldY) = (newX, newY)

    del self.waveforms[-1]

  def OnEditTrace(self, event):
    assert self.clickwaveform

    w = self.clickwaveform

    (isOK, newPath) = w.Edit(self.lastSTIPath)

    if isOK:
      w.SetStartTime(self.startTime)
      w.SetDivision(self.division)
      w.SetTickSpacing(self.tickSpacing)

      if w.IsInput():
        w.SetLabelBackground(_LA_INDATA_COLOR)
        w.SetDataBackground(_LA_INDATA_COLOR)
        if w.StimulusFile(): w.LoadStimulus()
      else:
        w.SetLabelBackground(_LA_OUTDATA_COLOR)
        w.SetDataBackground(_LA_OUTDATA_COLOR)
      w.Refresh()

      if newPath: self.lastSTIPath = newPath

  def OnReloadStimulus(self, event):
    assert self.clickwaveform
    assert self.clickwaveform.IsInput()
    self.clickwaveform.LoadStimulus()

  def OnTextC1(self, event):
    s = self.c1TimeText.GetValue()
    try: val = int(s)
    except:
      self.c1TimeText.SetValue(str(self.cursors.GetC1Pos()))
      return

    self.cursors.SetC1PosCycles(val)
    self.parent.menubar.Check(207, 1)

  def OnTextC2(self, event):
    s = self.c2TimeText.GetValue()
    try: val = int(s)
    except:
      self.c2TimeText.SetValue(str(self.cursors.GetC2Pos()))
      return

    self.cursors.SetC2PosCycles(val)
    self.parent.menubar.Check(208, 1)

  def BuildStimulusList(self):
    stimuli = []

    for w in self.waveforms:
      if not w.IsInput(): continue

      events = w.GetEvents()
      if events:
        eventlist = map(operator.__add__, events, [(w.GetPortPin(),)]*len(events))
        stimuli = stimuli + eventlist

    stimuli.sort()
    return stimuli

  ##################################################################
  ##################################################################
  ##################################################################

  def Queue_handler(self, event):
    try: (func, args) = self.queue.get(0)
    except Queue.Empty: return

    func(*args)

    # Come back here for the next event in the queue
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, 301))

  # The following functions are called as fake button handlers
  # to respond to events from the PySim11 thread.

  def OnCycReset_handler(self):
    for w in self.waveforms: w.OnCycReset()
    self.SetStartTime(0)
    self.startTimeText.SetValue("0")

  def IsSimulating_handler(self, sim):
    self.isSimulating = sim
    self.startTimeText.Enable(not sim)
    self.startTimeZeroButton.Enable(not sim)
    self.divisionText.Enable(not sim)
    self.startTimePDivButton.Enable(not sim)
    self.startTimeMDivButton.Enable(not sim)
    self.zoomInButton.Enable(not sim)
    self.zoomOutButton.Enable(not sim)
    self.zoomAllButton.Enable(not sim)
    self.zoomMaxButton.Enable(not sim)

    self.waveformMenu.Enable(401, not sim) # Add waveform

    f = self.viewMenu.Enable
    f(201, not sim)   # Zero
    f(211, not sim)   # +div
    f(212, not sim)   # -div
    f(203, not sim)   # Zoom in
    f(204, not sim)   # Zoom out
    f(205, not sim)   # Zoom all
    f(206, not sim)   # Zoom max

    if not sim:
      for w in self.waveforms: w.RefreshData()

  def Append_handler(self, PortPin, T, V):
    for w in self.waveforms:
      if PortPin == w.GetPortPin(): w.Append(T,V, not self.isSimulating)

  def AppendRel_handler(self, PortPin, DT, V):
    for w in self.waveforms:
      if PortPin == w.GetPortPin(): w.AppendRel(DT,V, not self.isSimulating)

  ##################################################################
  ##################################################################
  ##################################################################

  # The following functions are called from the PySim11 thread
  # and must post to the queue for thread safety

  def OnCycReset(self, event):
    self.queue.put((self.OnCycReset_handler, ()))
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, 301))

  def IsSimulating(self, sim):
    self.queue.put((self.IsSimulating_handler, (sim,)))
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, 301))

  def Append(self, PortPin, T, V):
    self.queue.put((self.Append_handler, (PortPin, T, V)))
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, 301))

  def AppendRel(self, PortPin, DT, V):
    self.queue.put((self.AppendRel_handler, (PortPin, DT, V)))
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, 301))

  ##################################################################
  ##################################################################
  ##################################################################
