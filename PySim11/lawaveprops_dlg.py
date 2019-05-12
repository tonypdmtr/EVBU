import wx

PortInfo = { \
  'PA7': ('IO','''\
Port A:7  PA7/PAI/OC1
When an output, this pin
may be driven by Output
Compare 1. When an input,
this pin serves as the
pulse accumulator input.
This pin's direction is
set by the DDRA7 bit in
the PACTL register.'''),
  'PA6': ('O', '''\
Port A:6  PA6/OC2
This output pin may be
driven by Output Compare
2.'''),
  'PA5': ('O', '''\
Port A:4  PA5/OC3
This output pin may be
driven by Output Compare
3.'''),
  'PA4': ('O', '''\
Port A:4  PA4/OC4
This output pin may be
driven by Output Compare
4.'''),
  'PA3': ('IO','''\
Port A:3  PA3/OC5/IC4
When an output, this pin
may be driven by Output
Compare 5. When an input,
this pin serves as Input
Capture 4. This pin's
direction is set by the
DDRA3 bit in the PACTL
register.'''),
  'PA2': ('I', '''\
Port A:2  PA2/IC1
This input pin may be
used as Input Capture
1.'''),
  'PA1': ('I', '''\
Port A:1  PA1/IC2
This input pin may be
used as Input Capture
2.'''),
  'PA0': ('I', '''\
Port A:0  PA2/IC3
This input pin may be
used as Input Capture
3.'''),
  'PB7': ('O', '''\
Port B:7  PB7
This is an output pin,
but it is not available
when the 68HC11 operates
in expanded mode.'''),
  'PB6': ('O', '''\
Port B:6  PB6
This is an output pin,
but it is not available
when the 68HC11 operates
in expanded mode.'''),
  'PB5': ('O', '''\
Port B:5  PB5
This is an output pin,
but it is not available
when the 68HC11 operates
in expanded mode.'''),
  'PB4': ('O', '''\
Port B:4  PB4
This is an output pin,
but it is not available
when the 68HC11 operates
in expanded mode.'''),
  'PB3': ('O', '''\
Port B:3  PB3
This is an output pin,
but it is not available
when the 68HC11 operates
in expanded mode.'''),
  'PB2': ('O', '''\
Port B:2  PB2
This is an output pin,
but it is not available
when the 68HC11 operates
in expanded mode.'''),
  'PB1': ('O', '''\
Port B:1  PB1
This is an output pin,
but it is not available
when the 68HC11 operates
in expanded mode.'''),
  'PB0': ('O', '''\
Port B:0  PB0
This is an output pin,
but it is not available
when the 68HC11 operates
in expanded mode.'''),
  'PC7': ('IO', '''\
Port C:7  PC7
This is a bidirectional
pin whose direction is
controlled by the DDRC
register. Port C is not
available in expanded
mode.'''),
  'PC6': ('IO', '''\
Port C:6  PC6
This is a bidirectional
pin whose direction is
controlled by the DDRC
register. Port C is not
available in expanded
mode.'''),
  'PC5': ('IO', '''\
Port C:5  PC5
This is a bidirectional
pin whose direction is
controlled by the DDRC
register. Port C is not
available in expanded
mode.'''),
  'PC4': ('IO', '''\
Port C:4  PC4
This is a bidirectional
pin whose direction is
controlled by the DDRC
register. Port C is not
available in expanded
mode.'''),
  'PC3': ('IO', '''\
Port C:3  PC3
This is a bidirectional
pin whose direction is
controlled by the DDRC
register. Port C is not
available in expanded
mode.'''),
  'PC2': ('IO', '''\
Port C:2  PC2
This is a bidirectional
pin whose direction is
controlled by the DDRC
register. Port C is not
available in expanded
mode.'''),
  'PC1': ('IO', '''\
Port C:1  PC1
This is a bidirectional
pin whose direction is
controlled by the DDRC
register. Port C is not
available in expanded
mode.'''),
  'PC0': ('IO', '''\
Port C:0  PC0
This is a bidirectional
pin whose direction is
controlled by the DDRC
register. Port C is not
available in expanded
mode.'''),
  'PD5': ('IO', '''\
Port D:5  PD5/SS
This is a bidirectional
pin whose direction is
controlled by the DDRD
register. PD5 is not
available when the SPI
peripheral is enabled.'''),
  'PD4': ('IO', '''\
Port D:4  PD4/SCK
This is a bidirectional
pin whose direction is
controlled by the DDRD
register. PD4 is not
available when the SPI
peripheral is enabled.'''),
  'PD3': ('IO', '''\
Port D:3  PD3/MOSI
This is a bidirectional
pin whose direction is
controlled by the DDRD
register. PD3 is not
available when the SPI
peripheral is enabled.'''),
  'PD2': ('IO', '''\
Port D:2  PD2/MISO
This is a bidirectional
pin whose direction is
controlled by the DDRD
register. PD2 is not
available when the SPI
peripheral is enabled.'''),
  'PD1': ('IO', '''\
Port D:1  PD1/TxD
This is a bidirectional
pin whose direction is
controlled by the DDRD
register. PD1 is not
available when the SCI
peripheral is enabled.'''),
  'PD0': ('IO', '''\
Port D:0  PD0/RxD
This is a bidirectional
pin whose direction is
controlled by the DDRD
register. PD0 is not
available when the SCI
peripheral is enabled.'''),
  'PE7': ('I', '''\
Port E:7  PE7/AN7
This is an input pin
that is also an A/D
input channel.'''),
  'PE6': ('I', '''\
Port E:6  PE6/AN6
This is an input pin
that is also an A/D
input channel.'''),
  'PE5': ('I', '''\
Port E:5  PE5/AN5
This is an input pin
that is also an A/D
input channel.'''),
  'PE4': ('I', '''\
Port E:4  PE4/AN4
This is an input pin
that is also an A/D
input channel.'''),
  'PE3': ('I', '''\
Port E:3  PE3/AN3
This is an input pin
that is also an A/D
input channel.'''),
  'PE2': ('I', '''\
Port E:2  PE2/AN2
This is an input pin
that is also an A/D
input channel.'''),
  'PE1': ('I', '''\
Port E:1  PE1/AN1
This is an input pin
that is also an A/D
input channel.'''),
  'PE0': ('I', '''\
Port E:0  PE0/AN0
This is an input pin
that is also an A/D
input channel.''')
  }

class LAWaveformProperties(wx.Dialog):

  def __init__(self, parent, id, title, orig, lastPath):
    super().__init__(parent, id, title, orig, wx.DLG_SZE(parent,wx.Size(160,184)), wx.CAPTION|wx.DIALOG_MODAL)

    wx.StaticText(self, -1, "Port Pin", wx.DLG_PNT(self,wx.Point(10,10)), wx.DLG_SZE(self,wx.Size(21,9)), wx.ALIGN_LEFT)

    self.lastPath = lastPath

    names = PortInfo.keys()
    names.sort()

    self.listbox = wx.ListBox(self, 100, wx.DLG_PNT(self,wx.Point(10,20)), wx.DLG_SZE(self,wx.Size(46,90)), names, wx.LB_SINGLE)
    self.stimulusfile = wx.StaticText(self, -1, "Stimulus File", wx.DLG_PNT(self,wx.Point(10,114)), wx.DLG_SZE(self,wx.Size(36,9)), wx.ALIGN_LEFT)
    self.stimulusfile.Enable(0)

    self.filename = wx.TextCtrl(self, 101, "", wx.DLG_PNT(self,wx.Point(10,123)), wx.DLG_SZE(self,wx.Size(100,13)), wx.TE_PROCESS_ENTER)
    self.filename.Enable(0)
    self.browse = wx.Button(self, 102, "Browse", wx.DLG_PNT(self,wx.Point(116,123)), wx.DLG_SZE(self,wx.Size(32,12)))
    self.browse.Enable(0)
    wx.StaticBox(self, -1, "Port Pin Info", wx.DLG_PNT(self,wx.Point(60,10)), wx.DLG_SZE(self,wx.Size(90,100)))

    self.pininfo = wx.StaticText(self, 103, "", wx.DLG_PNT(self,wx.Point(62,21)), wx.DLG_SZE(self,wx.Size(86,85)), wx.ALIGN_LEFT|wx.ST_NO_AUTORESIZE)

    wx.StaticLine(self, -1, wx.DLG_PNT(self,wx.Point(5,145)), wx.DLG_SZE(self,wx.Size(148,2)), wx.LI_HORIZONTAL)
    self.okbutton = wx.Button(self, wx.ID_OK, "OK", wx.DLG_PNT(self,wx.Point(34, 152)), wx.DLG_SZE(self,wx.Size(32,12)))
    self.okbutton.Enable(0)
    wx.Button(self, wx.ID_CANCEL, "Cancel", wx.DLG_PNT(self,wx.Point(86, 152)), wx.DLG_SZE(self,wx.Size(32,12)))

    self.Bind(wx.EVT_LISTBOX,self.OnListBox,id=100) #EVT_LISTBOX(self, 100, self.OnListBox)
    self.Bind(wx.EVT_LISTBOX_DCLICK,self.OnListBoxDoubleClick,id=100) #EVT_LISTBOX_DCLICK(self, 100, self.OnListBoxDoubleClick)
    self.Bind(wx.EVT_BUTTON,self.OnBrowse,id=102) #EVT_BUTTON(self, 102, self.OnBrowse)
    self.Bind(wx.EVT_TEXT_ENTER,self.OnTextEnter,id=101) #EVT_TEXT_ENTER(self, 101, self.OnTextEnter)
    self.Bind(wx.EVT_BUTTON,self.OnOk,id=wx.ID_OK) #EVT_BUTTON(self, wx.ID_OK, self.OnOk)

  def OnOk(self, event):
    # Don't allow OK button when no selection. We kind-of handle
    # this by disabling the OK button before something is selected,
    # but it turns out that the thing can be UN-selected (Shift-Click)
    # and the listbox doesn't get an event notification. So this is
    # a fallback.
    if len(self.listbox.GetStringSelection()): event.Skip()

  def SetValues(self, portpin, filename):
    notnull = 1

    if portpin is not None:
      self.listbox.SetStringSelection(portpin)
      self.pininfo.SetLabel(PortInfo[portpin][1])
      self.okbutton.Enable(1)
      if PortInfo[portpin][0] == 'O': notnull = 0

    notnull = notnull and (not (filename is None))
    self.filename.Enable(notnull)
    self.browse.Enable(notnull)
    self.stimulusfile.Enable(notnull)
    if notnull: self.filename.SetValue(filename)
    else: self.filename.SetValue("")

  def OnTextEnter(self, event):
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, wx.ID_OK))

  def OnListBoxDoubleClick(self, event):
    s = event.GetString()
    assert s in PortInfo
    self.okbutton.Enable(1)
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, wx.ID_OK))

  def OnListBox(self, event):
    s = event.GetString()
    assert s in PortInfo
    self.pininfo.SetLabel(PortInfo[s][1])
    self.okbutton.Enable(1)
    if PortInfo[s][0] == 'O':
      self.filename.Enable(0)
      self.browse.Enable(0)
      self.stimulusfile.Enable(0)
    else:
      self.filename.Enable(1)
      self.browse.Enable(1)
      self.stimulusfile.Enable(1)

  def OnBrowse(self, event):
    s = wx.FileSelector("Select stimulus file", self.lastPath, "", ".sti", "Stimulus files (*.sti)|*.sti|All files (*.*)|*.*", wx.OPEN|wx.FILE_MUST_EXIST, self)
    if s: self.filename.SetValue(s)

  def SlurpData(self):
    d = {}
    d['pin'] = self.listbox.GetStringSelection()
    d['filename'] = self.filename.GetValue()
    d['IO'] = PortInfo[d['pin']][0]
    return d

if __name__ == "__main__":
  app = wx.App()
  d = LAWaveformProperties(None, -1, "Waveform Properties", wx.Point(-1,-1))
  if d.ShowModal() == wx.ID_OK:
    dlgdata = d.SlurpData()
    print(dlgdata['pin'])
    print(dlgdata['filename'])
    print(dlgdata['IO'])
