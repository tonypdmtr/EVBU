# This is the CMD.PY file from the Python 1.5.2 distribution.
# This has been significantly modified for use with EVBU by Andrew Sterian.
# As this is not an original work, it is not covered by the license (GPL)
# of the EVBU program but is instead covered by the license of the Python
# distribution.
#
# The cmdloop() member has been modified for implementation in a
# windowing environment. It is now expected to be the main loop of a
# separate thread. The only thing we've retained in this class
# is the help handling. EOF handling is removed, raw_input() is removed
# (hence so has readline functionality). Since cmdloop() is changed,
# self.intro has been removed too.
#
# We've added a self.write method instead of using print.
################################################################################
#
# A generic class to build line-oriented command interpreters
#
# Interpreters constructed with this class obey the following conventions:
#
# 1. End of file on input is processed as the command 'EOF'.
# 2. A command is parsed out of each line by collecting the prefix composed
#    of characters in the identchars member.
# 3. A command 'foo' is dispatched to a method 'do_foo()'; the do_ method
#    is passed a single argument consisting of the remainder of the line.
# 4. Typing an empty line repeats the last command.  (Actually, it calls the
#    method 'emptyline', which may be overridden in a subclass.)
# 5. There is a predefined 'help' method.  Given an argument 'topic', it
#    calls the command 'help_topic'.  With no arguments, it lists all topics
#    with defined help_ functions, broken into up to three topics; documented
#    commands, miscellaneous help topics, and undocumented commands.
# 6. The command '?' is a synonym for 'help'.  The command '!' is a synonym
#    for 'shell', if a do_shell method exists.
#
# The 'default' method may be overridden to intercept commands for which there
# is no do_ method.
#
# The data member 'self.ruler' sets the character used to draw separator lines
# in the help messages.  If empty, no ruler line is drawn.  It defaults to "=".
#
# If the value of 'self.intro' is nonempty when the cmdloop method is called,
# it is printed out on interpreter startup.  This value may be overridden
# via an optional argument to the cmdloop() method.
#
# The data members 'self.doc_header', 'self.misc_header', and
# 'self.undoc_header' set the headers used for the help function's
# listings of documented functions, miscellaneous topics, and undocumented
# functions respectively.
#
# These interpreters use raw_input; thus, if the readline module is loaded,
# they automatically support Emacs-like command history and editing features.
#

import string
import sys
import linecache

PROMPT = '(Cmd) '
IDENTCHARS = string.ascii_letters + string.digits + '_'

class Cmdbase:
  prompt = PROMPT
  identchars = IDENTCHARS
  ruler = '='
  lastcmd = ''
  cmdqueue = []
  doc_leader = ""
  doc_header = "\nDocumented commands (type help <topic>):\n"
  misc_header = "\nMiscellaneous help topics:\n"
  undoc_header = "\nUndocumented commands:\n"
  nohelp = "*** No help on %s\n"

  def __init__(self): self.write = sys.stdout.write

  def cmdloop(self):
    self.preloop()

    stop = None
    while not stop:
      if self.cmdqueue:
        line = self.cmdqueue[0]
        del self.cmdqueue[0]
      elif self.queue:
        line = self.queue.get()
        if line is 0: return
      else: assert 0, "cmdloop has no input queue"

      line = self.precmd(line)
      stop = self.onecmd(line)
      stop = self.postcmd(stop, line)
    self.postloop()

  def precmd(self, line): return line

  def postcmd(self, stop, line): return stop

  def preloop(self): pass

  def postloop(self): pass

  def onecmd(self, line):
    line = line.strip()
    if line == '!':
      if hasattr(self, 'do_shell'): line = 'shell'
      else: return self.default(line)
    elif not line: return self.emptyline()
    self.lastcmd = line
    i, n = 0, len(line)
    while i < n and line[i] in self.identchars+'?': i += 1
    cmd, arg = line[:i], line[i:].strip()
    if cmd == '?': cmd = 'help'
    if cmd == '': return self.default(line)
    else:
      try: func = getattr(self, 'do_' + cmd)
      except AttributeError: return self.default(line)
      return func(arg)

  def emptyline(self):
    if self.lastcmd:
      self.write(self.lastcmd+'\n')
      return self.onecmd(self.lastcmd)

  def default(self, line): self.write(f'*** Unknown syntax: {line}')

  def do_help(self, arg):
    if arg:
      # XXX check arg syntax
      try: func = getattr(self, 'help_' + arg)
      except:
        try:
          doc=getattr(self, 'do_' + arg).__doc__
          if doc:
            self.write(doc)
            return
        except: pass
        self.write(self.nohelp % (arg,))
        return
      func()
    else:
      # Inheritance says we have to look in class and
      # base classes; order is not important.
      names = []
      classes = [self.__class__]
      while classes:
        aclass = classes[0]
        if aclass.__bases__: classes = classes + list(aclass.__bases__)
        names = names + dir(aclass)
        del classes[0]
      cmds_doc = []
      cmds_undoc = []
      help = {}
      for name in names:
        if name[:5] == 'help_': help[name[5:]]=1
      names.sort()
      # There can be duplicates if routines overridden
      prevname = ''
      for name in names:
        if name[:3] == 'do_':
          if name == prevname: continue
          prevname = name
          cmd=name[3:]
          if cmd in help:
            cmds_doc.append(cmd)
            del help[cmd]
          elif getattr(self, name).__doc__:
            cmds_doc.append(cmd)
          else: cmds_undoc.append(cmd)
      self.write(self.doc_leader)
      self.print_topics(self.doc_header,   cmds_doc,   15,80)
      self.print_topics(self.misc_header,  help.keys(),15,80)
      self.print_topics(self.undoc_header, cmds_undoc, 15,80)

  def print_topics(self, header, cmds, cmdlen, maxcol):
    if cmds:
      self.write(header)
      if self.ruler:
        self.write(self.ruler * len(header))
        self.write('\n')
      cmds_per_line,junk=divmod(maxcol,cmdlen)
      col=cmds_per_line
      for cmd in cmds:
        if col==0: self.write('\n')
        self.write( (("%-"+str(cmdlen)+"s") % cmd))
        col = (col+1) % cmds_per_line
      self.write('\n')
