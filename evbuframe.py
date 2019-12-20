'''
Top-level window (menus, statusbar, etc.) for EVBU GUI
'''

import sys
import os
import string
import queue
import time
from safestruct import *
import wx
from term import Term
import EVBUoptions
from PySim11 import PySim11
from kcmmemory import getkcmmemoryData

class EVBUFrame(wx.Frame):

  def __init__(self, parent, id, title, q, simbreak):
    # Queue for sending user input to cmdloop
    self.queue = q

    # Event flag for stopping simulation
    self.simbreak = simbreak

    # Set to 1 when PySim11 is simulating
    self.isSimulating = 0

    # Handle to EVBUCmd instance
    self.evb = None

    #####################################################
    #
    # Determine sizes
    #
    #####################################################
    dc = wx.ScreenDC()
    font = wx.Font(12 if sys.platform == "win32" else 14, wx.MODERN, wx.NORMAL, wx.NORMAL)
    dc.SetFont(font)
    ch = dc.GetCharHeight()
    cw = dc.GetCharWidth()

    # I hate sizing things. I hate it, I hate it, I hate it. It
    # *never* works the way it's supposed to. GUI's suck.

    # Size ourselves as follows. Try for an 80x25 display. We want
    # to further account for a scrollbar and borders.
    # Unfortunately, wxPython returns 0 for all of the below. Sigh.
    m = wx.SystemSettings.GetMetric

    w = m(wx.SYS_WINDOWMIN_X)*cw + \
        m(wx.SYS_BORDER_X)*2 + \
        m(wx.SYS_EDGE_X)*2 + \
        m(wx.SYS_FRAMESIZE_X)*2 + \
        m(wx.SYS_VSCROLL_X)

    h = m(wx.SYS_WINDOWMIN_Y)*ch + ch + 4 +\
        m(wx.SYS_BORDER_Y)*4 + \
        m(wx.SYS_EDGE_Y)*4 + \
        m(wx.SYS_FRAMESIZE_Y)*2 + \
        m(wx.SYS_CAPTION_Y) + \
        m(wx.SYS_MENU_Y)

    print("Border: %d  Edge: %d  Framesize: %d" % (m(wx.SYS_BORDER_Y), m(wx.SYS_EDGE_Y), m(wx.SYS_FRAMESIZE_Y)))
    print("Caption: %d  Menu: %d" % (m(wx.SYS_CAPTION_Y), m(wx.SYS_MENU_Y)))
    print("Frame: %d x %d" % (w,h))

    # We'll just go with the slop approach
    #w = 80*cw + 30
    #h = 25*ch + ch + 72

    # First, call the base class' __init__ method to create the frame
    super().__init__(parent, id, title, wx.Point(-1, -1), wx.Size(w,h), wx.MAXIMIZE|wx.DEFAULT_FRAME_STYLE)
    self.SetAutoLayout(True)

    self.term = Term(self, -1, wx.Point(0,0), (m(wx.SYS_WINDOWMIN_X),m(wx.SYS_WINDOWMIN_Y)), font, q)

    # The PySim11 thread calls our functions to post window update
    # commands using this queue. We use a fake buttons with ID
    # of 301. The event handler for this button pulls an object
    # from the queue. Each object in the queue is a 2-tuple
    # (func, parms) which is simply invoked as func(*parms)
    # in the handler.
    self.handlerqueue = queue.Queue()
    self.handlerqueuebuttonid = wx.NewIdRef()
    self.Bind(wx.EVT_BUTTON,self.Queue_handler,id=self.handlerqueuebuttonid) #wx.EVT_BUTTON(self, self.handlerqueuebuttonid, self.Queue_handler)

    ##############################################
    #
    # Create menu bar, event table, and accelerator
    #
    ##############################################
    self.menubar = wx.MenuBar()
    self.menuIDs = {}
    fileMenu = wx.Menu()

    #self.menuIDs['Preferences'] = fileMenu.preferencesID = wx.NewIdRef()
    #fileMenu.Append(fileMenu.preferencesID, "&Preferences...\tCtrl-P", "Edit global properties for this application")
    #fileMenu.AppendSeparator()

    self.menuIDs['Load'] = fileMenu.loadID = wx.NewIdRef()
    fileMenu.Append(fileMenu.loadID, "&Load\tCtrl-L", "Load an S19 file")

    self.menuIDs['Exit'] = fileMenu.exitID = wx.NewIdRef()
    fileMenu.Append(fileMenu.exitID, "E&xit\tCtrl-Q", "Exit the program")

    self.menubar.Append(fileMenu, "&File")

    simMenu = wx.Menu()
    self.menuIDs['Stop'] = simMenu.stopID = wx.NewIdRef()
    simMenu.Append(simMenu.stopID, "&Stop\tCtrl-C", "Stop the simulation")
    self.menubar.Append(simMenu, "&Simulation")

    helpMenu = wx.Menu()
    self.menuIDs['About'] = helpMenu.aboutID = wx.NewIdRef()
    helpMenu.Append(helpMenu.aboutID, "&About...", "About this program")
    self.menubar.Append(helpMenu, "&Help")

    self.SetMenuBar(self.menubar)
    self.menubar.Enable(simMenu.stopID, 0)

    self.Bind(wx.EVT_CLOSE,self.OnCloseWindow) #wx.EVT_CLOSE(self, self.OnCloseWindow)
   #self.Bind(wx.EVT_MENU,self.OnPreferences,id=fileMenu.preferencesID) #wx.EVT_MENU(self, fileMenu.preferencesID, self.OnPreferences)
    self.Bind(wx.EVT_MENU,self.OnFileLoad,id=fileMenu.loadID) #wx.EVT_MENU(self, fileMenu.loadID, self.OnFileLoad)
    self.Bind(wx.EVT_MENU,self.OnCloseWindow,id=fileMenu.exitID) #wx.EVT_MENU(self, fileMenu.exitID, self.OnCloseWindow)
    self.Bind(wx.EVT_MENU,self.OnAbout,id=helpMenu.aboutID) #wx.EVT_MENU(self, helpMenu.aboutID, self.OnAbout)
    self.Bind(wx.EVT_MENU,self.OnSimStop,id=simMenu.stopID) #wx.EVT_MENU(self, simMenu.stopID, self.OnSimStop)

    accel = wx.AcceleratorTable([ \
              (wx.ACCEL_CTRL, ord('q'), fileMenu.exitID), \
    #         (wx.ACCEL_CTRL, ord('p'), fileMenu.preferencesID), \
              (wx.ACCEL_CTRL, ord('l'), fileMenu.loadID), \
              (wx.ACCEL_CTRL, ord('c'), simMenu.stopID)])
    self.SetAcceleratorTable(accel)

    ##############################################
    #
    # Create status bar
    #
    ##############################################
    self.statusBar = wx.StatusBar(self, -1, 0)
    self.statusBar.SetFieldsCount(1)
    self.statusBar.SetStatusWidths([-1])
    self.statusBar.SetStatusText("Ready", 0)
    self.SetStatusBar(self.statusBar)
    #self.statusBarBackgroundColor = self.statusBar.GetBackgroundColour()

    self.sizer = wx.BoxSizer(wx.VERTICAL)
    self.sizer.Add(self.term, 1, wx.EXPAND)
    self.sizer.Fit(self)
    self.SetSizer(self.sizer)

    #c1 = wx.LayoutConstraints()
    #c1.top.SameAs(self, wx.Top)
    #c1.left.SameAs(self, wx.Left)
    #c1.right.SameAs(self,wx.Right)
    #c1.bottom.SameAs(self, wx.Bottom)
    #c1.height.AsIs()
    #self.term.SetConstraints(c1)

    #c2 = wx.LayoutConstraints()
    #c2.left.SameAs(self, wx.Left)
    #c2.right.SameAs(self, wx.Right, 10)
    #c2.bottom.SameAs(self, wx.Bottom, 10)
    #c2.top.Below(self.term, 10)
    #c2.height.AsIs()
    #self.statusBar.SetConstraints(c2)

    #self.Layout()

    #self.Bind(wx.EVT_SIZE, self.OnSize) #wx.EVT_SIZE(self, self.OnSize)

    #########################
    #
    # Icon
    #
    #########################
    #self.SetIcon(wx.Icon(getkcmmemoryData(),type=wx.BITMAP_TYPE_XPM_DATA))

  #def OnSize(self, event):
  #  self.Layout()
  #  event.Skip()

  def Quit(self):
    if self.isSimulating:
      wx.MessageBox("Simulation is in progress. Terminate the simulation before quitting the program.", "Hold it, bub", wx.OK|wx.CENTRE)
      return

    self.queue.put(0)
    self.Destroy()

  def OnCloseWindow(self, event): self.Quit()
  def OnPreferences(self, event): pass

  def OnFileLoad(self, event):
    line = wx.FileSelector('Select S19 file', os.getcwd(), '', '.s19', 'S19 files (*.s19)|*.s19|All files (*.*)|*.*', wx.FD_OPEN|wx.FD_FILE_MUST_EXIST, self)
    if line: self.queue.put(f'load {line}')

  def OnAbout(self, event):
    aboutText = '''\
EVBU : A simulator for the Motorola 68HC11

EVBU Version %d.%d
PySim11 Version %d.%d

Andrew Sterian
Padnos College of Engineering & Computing
Grand Valley State University
<steriana@gvsu.edu>
<http://claymore.engineer.gvsu.edu/~steriana/Python>
Modified for Python3 by <tonyp@acm.org>
''' % (EVBUoptions.EVBUVersionMajor, EVBUoptions.EVBUVersionMinor,\
       PySim11.PySim11VersionMajor, PySim11.PySim11VersionMinor)
    wx.MessageBox(aboutText, "About EVBU", wx.OK|wx.CENTRE, self)

  def FlushQueue(self):
    # Flush the queue that sends user data to the EVBU
    try:
      while 1: junk = self.queue.get(0)
    except queue.Empty: pass

  def SetEVBU(self, evb):
    self.evb = evb
    evb.simstate.ucEvents.addHandler(evb.simstate.ucEvents.SimStart, self.OnSimStart)
    evb.simstate.ucEvents.addHandler(evb.simstate.ucEvents.SimEnd, self.OnSimEnd)
    evb.simstate.ucEvents.addHandler(evb.simstate.ucEvents.CharWait, self.OnCharWait)
    evb.simstate.ucEvents.addHandler(evb.simstate.ucEvents.NoCharWait, self.OnNoCharWait)

  # User-generated simulation stop
  def OnSimStop(self, event):
    if not self.isSimulating:
      wx.MessageBox("Simulation not in progress", "Huh?", wx.OK|wx.CENTRE, self)
      return

    # Clear the flag, then wait for PySim11 to set it, indicating a
    # successful break.
    self.simbreak.clear()
    while 1:
      self.simbreak.wait(3.0)
      if self.simbreak.isSet(): break
      else:
        ret = wx.MessageBox("The simulator has not stopped yet. Press OK to try again or Cancel to give up.", "Ooops", wx.OK|wx.CANCEL|wx.CENTRE|wx.ICON_ERROR)
        if ret != wx.OK: return

  ##################################################################
  ##################################################################
  ##################################################################

  # These functions are called as handlers in response to events
  # from PySim11

  def Queue_handler(self, event):
    try: (func, args) = self.handlerqueue.get(0)
    except queue.Empty: return

    func(*args)

    # Come back here for the next event in the queue
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.handlerqueuebuttonid))

  def OnCharWait_handler(self):
    self.statusBar.SetStatusText("Simulating...waiting for a character", 0)
    self.statusBar.Refresh()

  def OnNoCharWait_handler(self, event):
    self.statusBar.SetStatusText("Simulating...", 0)
    self.statusBar.Refresh()

  def OnSimStart_handler(self):
    self.isSimulating = 1
    #self.menubar.Enable(self.menuIDs['Preferences'], 0)
    self.menubar.Enable(self.menuIDs['Exit'], 0)
    self.menubar.Enable(self.menuIDs['Stop'], 1)
    self.term.SetCBreak(1)
    self.statusBar.SetStatusText("Simulating...", 0)

  def OnSimEnd_handler(self):
    self.isSimulating = 0
    #self.menubar.Enable(self.menuIDs['Preferences'], 1)
    self.menubar.Enable(self.menuIDs['Exit'], 1)
    self.menubar.Enable(self.menuIDs['Stop'], 0)
    self.FlushQueue()
    self.term.SetCBreak(0)
    self.statusBar.SetStatusText("Ready", 0)

  ##################################################################
  ##################################################################
  ##################################################################

  # The following functions are called from the PySim11 thread
  # and must post to the queue for thread safety

  def OnCharWait(self, event):
    self.handlerqueue.put((self.OnCharWait_handler, ()))
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.handlerqueuebuttonid))

  def OnNoCharWait(self, event):
    self.handlerqueue.put((self.OnNoCharWait_handler, ()))
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.handlerqueuebuttonid))

  def OnSimStart(self, event):
    self.handlerqueue.put((self.OnSimStart_handler, ()))
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.handlerqueuebuttonid))

  def OnSimEnd(self, event):
    self.handlerqueue.put((self.OnSimEnd_handler, ()))
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.handlerqueuebuttonid))

if __name__ == "__main__":
  class MyApp(wx.App):

      # wx.Windows calls this method to initialize the application
      def OnInit(self):

          # Create an instance of our customized Frame class
          import threading
          frame = EVBUFrame(None, -1, "This is a test",queue.Queue(),threading.Event())
          frame.Show(True)

          # Tell wx.Windows that this is our main window
          self.SetTopWindow(frame)

          # Return a success flag
          return True

  app = MyApp(0)     # Create an instance of the application class
  app.MainLoop()     # Tell it to start processing events
