'''
This module is the top-level frame for the logic analyzer window
'''

import wx
from PySim11.lapanel import LAPanel

from kcmmemory import getkcmmemoryData

## Create a new frame class, derived from the wxPython Frame.
class LAFrame(wx.Frame):

    def __init__(self, parent, id, title):
        # First, call the base class' __init__ method to create the frame
        super().__init__(parent, id, title, wx.Point(-1, -1), wx.Size(835, 320), wx.DEFAULT_FRAME_STYLE)

        self.Bind(wx.EVT_CLOSE,self.OnCloseWindow) #EVT_CLOSE(self, self.OnCloseWindow)

        # Add the LA panel
        self.la = LAPanel(self, -1, wx.Point(10,10), wx.Size(660,300), wx.TAB_TRAVERSAL)

        self.statusBar = wx.StatusBar(self, -1)
        self.statusBar.SetFieldsCount(1)
        self.statusBar.SetStatusWidths([-1])
        self.statusBar.SetStatusText("", 0)
        self.SetStatusBar(self.statusBar)

        #icon = wx.Icon(getkcmmemoryData(),type=wx.BITMAP_TYPE_XPM_DATA)
        #self.SetIcon(icon)

    # This method is called automatically when the CLOSE event is
    # sent to this window
    def OnCloseWindow(self, event):
        if hasattr(self,'testonly'): self.Destroy()
        else:
          wx.MessageBox("Do not close this window while EVBU is running.", "Bad user!", wx.OK|wx.CENTRE)

if __name__=="__main__":
  app = wx.PySimpleApp()
  f = LAFrame(None, -1, "Stuff")
  f.Show(1)
  f.testonly = 1
  app.MainLoop()
