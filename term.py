## import all of the wxPython GUI package
import wx

import queue

import types
import sys
import string

#---------------------------------------------------------------------------

#
# History -- manage a history buffer of input lines
#

class History:
  def reset_pointer(self): self.pointer = 0

  def flush(self):
    self.lines = []
    self.reset_pointer()

  def add(self, line):
    self.lines.append(line)
    if len(self.lines) > self.size: del self.linex[0]
    self.reset_pointer()

  def recall_up(self):
    if len(self.lines) == 0: return ''
    self.pointer = (self.pointer + 1 + len(self.lines)) % len(self.lines)
    return self.lines[self.pointer]

  def recall_down(self):
    if len(self.lines) == 0: return ''
    self.pointer = (self.pointer + 1) % len(self.lines)
    return self.lines[self.pointer]

  def __init__(self, size=100):
    self.size = size
    self.flush()

##############################################################
#
#     Term -- terminal with read-only display and single-input line


class MyTextCtrl(wx.TextCtrl):
  def __init__(self, parent, id, title, orig, size, style):
    super().__init__(parent, id, title, orig, size, style)
    self.parent = parent

    self.Bind(wx.EVT_CHAR,self.OnChar) #wx.EVT_CHAR(self, self.OnChar)

  def OnChar(self, event):
    self.parent.RawChar(event.GetKeyCode())
    event.Skip()

class Term(wx.Window):
  def __init__(self, parent, id, orig, dimension, font, q):
    self.parent = parent

    # This queue is used for sending input strings to the EVBU command interpreter
    self.queue = q

    # This queue is used for sending text strings from the interpreter to be
    # displayed by us.
    self.writequeue = queue.Queue()

    # This indicates whether we're passing single characters to the EVBU or whole
    # lines.
    self.cbreak = 0

    # List of previously entered lines for recalling with up/down arrows
    self.history = History(100)

    dc = wx.ClientDC(parent)
    dc.SetFont(font)
    ch = dc.GetCharHeight()
    cw = dc.GetCharWidth()

    # Slop approach
    w = dimension[0]*cw + 25
    h = dimension[1]*ch + ch + 18

    super().__init__(parent, id, orig, wx.Size(w,h), wx.NO_BORDER)

    self.Bind(wx.EVT_SIZE,self.OnSize) #wx.EVT_SIZE(self, self.OnSize)
    self.sizer = wx.BoxSizer(wx.VERTICAL)

    # Slop approach
    h = dimension[1]*ch + 8

    self.display = wx.TextCtrl(self, 200, '', wx.Point(0,0), wx.Size(w,h), wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH|wx.TE_NOHIDESEL)

    sep = 4
    h2 = ch + 8

    self.input   = MyTextCtrl(self, 201, '', wx.Point(0,h+sep), wx.Size(w,h2), wx.TE_PROCESS_ENTER|wx.TE_RICH)

    self.display.SetFont(font)
    self.display.SetDefaultStyle(wx.TextAttr(wx.GREEN, wx.BLACK, font))
    self.display.SetBackgroundColour(wx.BLACK)

    self.input.SetFont(font)
    self.input.SetBackgroundColour(wx.BLACK)
    self.input.SetForegroundColour(wx.WHITE)

    self.Bind(wx.EVT_TEXT_ENTER,self.OnInput,id=201) #wx.EVT_TEXT_ENTER(self, 201, self.OnInput)
    self.Bind(wx.EVT_BUTTON,self.OnWriteQueue,id=301) #wx.EVT_BUTTON(self, 301, self.OnWriteQueue)

    # Try using a sizer
    self.sizer.Add(self.display, 1, wx.EXPAND)
    self.sizer.Add(w, 5, 0, wx.EXPAND)
    self.sizer.Add(self.input, 0, wx.EXPAND)
    self.SetAutoLayout(True)
    self.SetSizer(self.sizer)
    self.sizer.Fit(self)

    # Now try to figure out actual sizes...doesn't seem to work
    #(X,Y) = self.display.GetSizeTuple()
    #(x,y) = self.display.GetClientSize()
    #print('Display:', (X,Y), (x,y))
    #dX = X-x
    #dY = Y-y
    #self.display.SetClientSize(wx.Size(dimension[0]*cw + dX, dimension[1]*ch + dY))

    #(X,Y) = self.input.GetSizeTuple()
    #(x,y) = self.input.GetClientSize()
    #print('Input:', (X,Y), (x,y))
    #dX = X-x
    #dY = Y-y
    #self.input.SetClientSize(wx.Size(dimension[0]*cw + dX, 1*ch + dY))

  def OnSize(self, event):
    #print 'OnSize:', event.GetSize()
    #print 'Client size:', self.GetClientSize()
    self.Layout()

  def SetCBreak(self, cbreak):
    self.cbreak = cbreak
    self.input.Clear()

  def RawChar(self, keycode):
    if self.cbreak:
      if 0 < keycode < 256: self.queue.put(chr(keycode))
    else:
      if keycode == wx.WXK_UP: self.input.SetValue(self.history.recall_up())
      elif keycode == wx.WXK_DOWN: self.input.SetValue(self.history.recall_down())
      elif keycode == wx.WXK_ESCAPE: self.input.Clear()

  def OnInput(self, event):
    if self.cbreak:
      event.Skip()
      return

    s = self.input.GetValue()
    self.display.AppendText(s+'\n')
    self.input.Clear()

    # Send s to the EVBU command queue
    self.queue.put(s)
    if s: self.history.add(s)
    self.history.reset_pointer()

  def write(self, s):
    '''Write a big help string one line at a time, to improve scrolling behavior of wx.TextCtrl.'''
    lines = s.split('\n')

    for line in lines[:-1]: self.writequeue.put(line+'\n')
    self.writequeue.put(lines[-1])
    wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, 301))

  def OnWriteQueue(self, event):
    try:
      self.display.AppendText(self.writequeue.get(0))
      wx.PostEvent(self, wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, 301))
    except queue.Empty: pass

#---------------------------------------------------------------------------
if __name__ == '__main__':
    class MyFrame(wx.Frame):

      def __init__(self, parent, id, title):
        # First, call the base class' __init__ method to create the frame
        super().__init__(parent, id, title, wx.Point(-1, -1), wx.Size(800, 450))

        self.Bind(wx.EVT_CLOSE,self.OnCloseWindow) #EVT_CLOSE(self, self.OnCloseWindow)

        self.term = Term(self, -1, wx.Point(0,0), wx.Size(610,430))

      def OnCloseWindow(self, event): self.Destroy()

    class MyApp(wx.App):

        # wx.Windows calls this method to initialize the application
        def OnInit(self):

            # Create an instance of our customized Frame class
            frame = MyFrame(None, -1, 'This is a test')
            frame.Show(True)

            # Tell wx.Windows that this is our main window
            self.SetTopWindow(frame)

            # Return a success flag
            return True

    app = MyApp(0)     # Create an instance of the application class
    app.MainLoop()     # Tell it to start processing events
