'''
Command-line interface to PySim11 that mimics the Motorola 68HC11 EVBU
'''

import sys
import string
import cmdbase

from safestruct import *

import EVBUoptions
from EVBUutil import *
from G import *
from PySim11 import asm,ops,mapsym,PySim11,BFORCE_ALWAYS,BFORCE_NEVER
from PySim11.s19 import *

class EVBUCmd(cmdbase.Cmdbase):
  def __init__(self, simstate, parent, write=sys.stdout.write, queue=None):
    cmdbase.Cmdbase.__init__(self)
    self.simstate = simstate
    self.parent = parent
    self.write = write
    self.queue = queue
    self.write('''\
68HC11 EVBU Simulator Version %d.%d. PySim11 Version %d.%d.
Copyright 1999-2002 Andrew Sterian.
Python 3 and wxPython Phoenix adaptation (2019) by Tony Papadimitriou <tonyp@acm.org>

EVBU comes with ABSOLUTELY NO WARRANTY. This is free software licensed under
the terms of the GNU General Public License (GPL). You are welcome to
redistribute this software under certain conditions. For more details, see
the file named COPYING that comes with this software.

Type 'help overview' for a summary of all commands. Type 'quit' to exit.
''' % (EVBUoptions.EVBUVersionMajor, EVBUoptions.EVBUVersionMinor,\
       PySim11.PySim11VersionMajor, PySim11.PySim11VersionMinor))

    self.lastMDaddr = 0     # Last address displayed with MD
    self.lastASMaddr = 0    # Last address displayed with ASM

  def do_quit(self, line):
    if self.parent and hasattr(self.parent, 'Quit'): self.parent.Quit()

  def help_quit(self): self.write("This command terminates the EVBU session\n")

  def do_print(self, line):
    "PRINT <value>"
    try: val = getu16(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return
    self.write("$%04X  &%u\n" % (val, val))

  def help_print(self): self.write('''\
PRINT <value>
Evaluates the expression as a 16-bit integer and prints the hex
and decimal value. This command is useful for testing out the
interpreter's expression evaluator and for finding the values
of symbols loaded from a MAP file.\
''')

  def do_asm(self, line):
    "ASM [<address>]"
    try: addr = getoptu16(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return
    addr = addr or self.lastASMaddr

    count = 0
    oldPC = self.simstate.ucState.PC
    self.simstate.ucState.setPC(addr)
    while count < 10:
      startPC =  self.simstate.ucState.PC
      try:
        instr, mode, cycles = self.simstate.ifetch_raw()
        parms = self.simstate.decode(mode)
      except ops.IllegalOperation:
        instr = 'ILLOP'
        mode = None
        parms = None

      bytecount = self.simstate.ucState.PC - startPC
      bytes = [0]*bytecount
      for b in range(0,bytecount):
        bytes[b] = self.simstate.ucMemory.readUns8(startPC+b)
      self.write(asm.dasm_line(startPC, bytes, instr, mode, parms, cycles))
      self.write('\n')
      count += 1

    self.lastASMaddr = self.simstate.ucState.PC
    self.simstate.ucState.setPC(oldPC)

  def help_asm(self): self.write('''\
ASM [<addr>]
Disassemble instructions at the specified address. If the address is ommitted,
disassembly continues from the last disassembled address.\
''')

  def do_l(self, line):
    "L [<num>]"
    if len(line) > 0:
      try: count = getu16(line, self.simstate)
      except Exception as detail:
        self.write(str(detail)+'\n')
        return
    else: count = 20

    if not self.simstate.mapfile:
      self.write("No MAP file loaded\n")
      return

    mapfile = self.simstate.mapfile
    try: srcline, fname, linenum = mapfile.addrmap[self.simstate.ucState.PC]
    except:
      self.write("Current PC not found in MAP file\n")
      return

    try: fnum = mapfile.fnames.index(fname)
    except:
      self.write("Internal error: unable to find filename '%s'\n" % fname)
      return

    self.write('%s:\n' % fname)

    min_line = linenum - int(count/2)
    min_line = max(min_line, 1)
    max_line = min_line + count - 1
    max_line = min(max_line, len(mapfile.files[fnum]))

    lines = mapfile.files[fnum]
    for line in range(min_line, max_line+1):
      try: addr_s = '%04X' % mapfile.linemap[(fnum+1, line)][0]
      except: addr_s = '    '
      self.write("%5d %s %s" % (line, addr_s, lines[line-1]))

  def help_l(self): self.write('''\
L [<num>]
This command displays the source lines around the current PC
value if a MAP file is loaded. The optional argument indicates
the number of lines to display. The line corresponding to the
current PC is centered in the display.\
''')

  def do_bf(self, line):
    "BF <Addr1> <Addr2> <data>"
    try: addr1, addr2, data = getu16u16u8(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return
    if addr2 < addr1:
      self.write("Address 2 is lower than address 1\n")
      return

    for addr in range(addr1,addr2+1):
      self.simstate.ucMemory.writeUns8(addr, data)

    self.write('Memory from $%04X to $%04X filled with $%02X\n' % (addr1, addr2, data))

  def help_bf(self): self.write('''\
BF <Addr1> <Addr2> <data>
This command fills the range of memory from Addr1 through Addr2 with
the 8-bit data value.\
''')

  def do_br(self, line):
    "BR [<address> | -<bpnum> | -all]"
    if len(line) == 0:
      if len(self.simstate.BPlist) == 0:
        self.write('No breakpoints\n')
        return

      self.write('Num  Addr  Count Description\n')
      self.write('--- ------ ----- -------------------------------\n')
      for cnt in range(len(self.simstate.BPlist)):
        br = self.simstate.BPlist[cnt]
        self.write('%3d  $%04X %5d %s\n' % (cnt, br.addr, br.count, br.text))

      return

    do_remove = 0
    if line[0] == '-':
      do_remove = 1
      line = line[1:]
      if line == 'all':
        self.simstate.BPlist = []
        self.write('All breakpoints deleted\n')
        return

    try: addr = getu16(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return

    if do_remove:
      if addr >= len(self.simstate.BPlist):
        self.write('Illegal breakpoint number\n')
        return
      del self.simstate.BPlist[addr]
      self.write('Breakpoint #%d deleted\n' % addr)
      return

    text = 'User breakpoint'
    mapfile = self.simstate.mapfile
    if mapfile:
      try:
        line, fname, linenum = mapfile.addrmap[addr]
        text += f' at {fname} line {linenum}'
        try:
          addr, sym = mapfile.linemap[(mapfile.fnames.index(fname)+1, linenum)]
          if sym: text += f' ({sym})'
        except: pass
      except: pass
    br = PySim11.ucBreakpoint()
    br.addr = addr
    br.text = text
    self.simstate.BPlist.append(br)
    self.write('Breakpoint added at $%04X\n' % addr)

  def help_br(self): self.write('''\
BR [<address> | -<bpnum> | -all]
This command manages breakpoints. The first form, 'BR <address>'
adds a breakpoint at the specified address (which may be a symbol
if a MAP file is loaded). The second form, 'BR -<bpnum>' removes
a breakpoint whose number is given. The first breakpoint is 0.
Breakpoint numbers can be found by issuing a 'BR' command by
itself which simply lists all breakpoints. The final form of this
command, 'BR -all' removes all breakpoints.\
''')

  def do_bulk(self, line):
    "BULK"
    if len(line):
      self.write('No arguments are accepted with this command\n')
      return

    for addr in range(0xB600, 0xB800, 2):
      self.simstate.ucMemory.writeUns16(addr, 0xFFFF)

  def help_bulk(self): self.write('''\
BULK
This command sets all memory locations in internal EEPROM to $FF\
''')

  def do_call(self, line):
    "CALL <address>"
    try: addr = getu16(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return

    self.simstate.ucState.push16(self.simstate.ucMemory, 0xFFFF)  # Dummy return address
    br = PySim11.ucBreakpoint()
    br.addr = 0xFFFF
    br.text = "CALL breakpoint"
    br.autoremove = 1
    self.simstate.BPlist.append(br)

    self.simstate.ucState.setPC(addr)
    self.simstate.step()
    self.simstate.ucState.display(self.write)
    self.write('\n')
    self.simstate.printNextInstruction()

  def help_call(self): self.write('''\
CALL <address>
Begin execution at the specified address as a subroutine call. The
corresponding RTS instruction terminates execution.\
''')

  def do_cyc(self, line):
    "CYC ['reset']"
    if len(line):
      if line=='reset':
        self.simstate.cycles = 0
        self.simstate.ucEvents.notifyEvent(self.simstate.ucEvents.CycReset)
      else:
        self.write('Illegal argument. Type "help cyc" for usage information\n')
      return
    self.write('%d cycles\n' % self.simstate.cycles)

  def help_cyc(self): self.write('''\
CYC ['reset']
With no parameters, this command displays the number of cycles executed so far.
The command 'CYC reset' resets the cycle counter to 0 and resets (i.e., clears)
the parallel I/O waveform display.\
''')

  def do_go(self, line):
    "GO [<address>]"
    if len(line):
      try: addr = getu16(line, self.simstate)
      except Exception as detail:
        self.write(str(detail)+'\n')
        return
      self.simstate.ucState.setPC(addr)

    self.simstate.cycles = 0
    self.simstate.ucEvents.notifyEvent(self.simstate.ucEvents.CycReset)

    self.simstate.step()
    self.simstate.ucState.display(self.write)
    self.write('\n')
    self.simstate.printNextInstruction()

  def help_help(self): self.write("Duh!\n")

  def help_go(self): self.write('''\
GO [<address>]
Execution begins at the specified address, or at the current PC value if no
address is given. Execution terminates at a breakpoint or an SWI instruction.
The cycle counter is reset to 0 and the parallel I/O waveform display is
reset.\
''')

  def do_load(self, line):
    "LOAD <filename>"
    try: addr, diag = ReadS19(line, self.simstate.ucMemory)
    except Exception as detail:
      if detail: self.write(str(detail)+'\n')
      return
    if diag: self.write(diag)
    self.write(f'Load of "{line}" successful\n')

    statusstr = mapsym.LoadMapFile(line, self.simstate)
    if statusstr: self.write(statusstr+'\n')

  def help_load(self): self.write('''\
LOAD <filename>
The S19 file specified is loaded into memory. If a MAP file
is present in the same directory, it is loaded too.\
''')

  def do_loadmap(self, line):
    "LOADMAP <mapfilename>"
    if len(line)==0:
      self.write('Expecting MAP file name\n')
      return

    from PySim11.mapsym import add_extension
    line = add_extension(line)
    try: fid = open(line, 'rt')
    except Exception as detail:
      if detail: self.write(str(detail)+'\n')
      return

    try: mf = mapsym.MapFile(fid)
    except Exception as detail:
      mf = None
      if detail: self.write(str(detail)+'\n')
    fid.close()

    if mf:
      self.simstate.mapfile = mf
      self.write('Loaded MAP file "%s"\n' % line)

  def help_loadmap(self): self.write('''\
LOADMAP <mapfilename>
This command loads a MAP file with the given filename. Normally,
a MAP file is loaded when an S19 file is loaded, using the S19
file's name and an extension of MAP. This command can be used
to load an alternate MAP file.\
''')

  def do_md(self, line):
    "MD [<address1> [<address2>]]"
    try: addr1, addr2 = getoptu16optu16(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return
    addr1 = addr1 or self.lastMDaddr
    addr2 = addr2 or min(addr1 + 255, 0xFFFF)
    self.lastMDaddr = (addr2+1) & 0xFFFF
    self.simstate.ucMemory.display8(addr1, addr2, self.write)

  def help_md(self): self.write('''\
MD [<address1> [<address2>]]
Memory beginning at address1 is displayed up to address2, or for 256 bytes
if address2 is ommitted. If address1 is ommitted, memory is displayed starting
from the last display address.\
''')

  def do_mm(self, line):
    "MM <address> [<value>]"
    try: addr, val = getu16optu16(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return

    if val is not None:
      self.simstate.ucMemory.writeUns8(addr, val)
      return

    self.write('Type "." to exit this mode\n')

    done = 0
    while not done:
      try: line = self.lineinput(*('%04X: %02X ' %
                  (addr, self.simstate.ucMemory.readUns8(addr)),))
      except EOFError: return

      if len(line) == 0: addr += 1
      elif line[0] == '.': done = 1
      else:
        try:
          val = getu8(line, self.simstate)
          self.simstate.ucMemory.writeUns8(addr, val)
          addr += 1
        except: pass

  def help_mm(self): self.write('''\
MM <address> [<value>]
This command enters memory modify mode at the given address. Each
byte can be left unchanged by pressing ENTER, or a new value can
be entered to overwrite the current value. Memory modify mode is
terminated when a period '.' is entered.\
''')

  def do_move(self, line):
    "MOVE <address1> <address2> [<dest>]"
    try:
      addr1, addr2, dest = getu16u16optu16(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return
    dest = dest or addr1+1

    memlen = addr2-addr1+1
    if memlen < 1:
      self.write("Nothing to move\n")
      return

    tempmem = [0]*memlen
    for addr in range(addr1,addr2+1):
      tempmem[addr-addr1] = self.simstate.ucMemory.readUns8(addr)
    for addr in range(dest, dest+memlen):
      self.simstate.ucMemory.writeUns8(addr, tempmem[addr-dest])

    self.write("Memory from $%04X-$%04X moved to $%04X-$%04X\n" % (addr1, addr2, dest, dest+memlen-1))

  def help_move(self): self.write('''\
MOVE <address1> <address2> [<dest>]
Copy memory from address1 through address2 to memory starting at dest. If
dest is ommitted, it defaults to address+1.\
''')

  def do_p(self, line):
    "P"
    if len(line) > 0:
      self.write('This command takes no parameters\n')
      return
    self.simstate.step()
    self.simstate.ucState.display(self.write)
    self.write('\n')
    self.simstate.printNextInstruction()

  def help_p(self): self.write('''\
P
Proceed to execute code at the current program counter. The cycle
counter and parallel I/O waveform display are unaffected.\
''')

  def do_rm(self, line):
    "RM [P|Y|X|A|B|D|C|S [val]]"
    fields = line.split()
    if len(fields) == 0:
      self.simstate.ucState.display(self.write)
      self.write('\n')
      self.simstate.printNextInstruction()
      return

    if len(fields) > 2:
      self.write('Too many arguments\n')
      return

    fields[0] = fields[0].upper()
    if len(fields[0]) > 1 or fields[0][0] not in 'PYXABDCS':
      self.write('Expecting register name (P, X, Y, A, B, D, C, or S)\n')
      return

    if fields[0] == 'P'  : fields[0] = 'PC'
    elif fields[0] == 'C': fields[0] = 'CC'
    elif fields[0] == 'S': fields[0] = 'SP'

    done = 0
    if len(fields) > 1:
      try:
        if fields[0][0] in 'ABC': val = getu8(fields[1], self.simstate)
        else: val = getu16(fields[1], self.simstate)
      except Exception as detail:
        self.write(str(detail)+'\n')
        return
      exec('self.simstate.ucState.set%s(val)' % fields[0])
      done = 1

    while not done:
      nibbles = 2 if fields[0][0] in 'ABC' else 4
      if fields[0][0] in 'D': curval = self.simstate.ucState.D()
      else: curval = eval('self.simstate.ucState.%s' % fields[0])
      try:
        s = self.lineinput(*((('%%s: %%0%dX ' % nibbles) % (fields[0], curval)),))
      except EOFError: return
      try:
        if nibbles == 2: val = getu8(s, self.simstate)
        else: val = getu16(s, self.simstate)
        exec('self.simstate.ucState.set%s(val)' % fields[0])
        done = 1
      except: pass
    self.simstate.ucState.display(self.write)
    self.write('\n')
    self.simstate.printNextInstruction()

  def lineinput(self, prompt):
    self.write(prompt)
    s = self.queue.get()
    return s

  def help_rm(self): self.write('''\
RM [P|Y|X|A|B|D|C|S [val]]
With no arguments, this command displays the current register set.
If a parameter is given, the register with the given name can be
modified. The third optional argument sets the value of the
register. If omitted, the current value is printed and a new
value is accepted from the user.\
''')

  def do_stopwhen(self, line):
    "STOPWHEN <cycles>"
    try:
      cycs = getu32(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return

    self.simstate.step(0, 0, cycs)
    self.simstate.ucState.display(self.write)
    self.write('\n')
    self.simstate.printNextInstruction()

  def help_stopwhen(self): self.write('''\
STOPWHEN <cycles>
Execution continues at the current program location and stops either
when an SWI is encountered or the given number of cycles have been
executed.\
''')

  def do_s(self, line):
    "S"
    if len(line) > 0:
      self.write("This command takes no parameters\n")
      return

    SPval = (self.simstate.ucState.SP + 1) & 0xFFFF
    retaddr = self.simstate.ucMemory.readUns16(SPval)

    br = PySim11.ucBreakpoint()
    br.addr = retaddr
    br.text = None
    br.autoremove = 1
    self.simstate.BPlist.append(br)

    self.simstate.step()
    self.simstate.ucState.display(self.write)
    self.write('\n')
    self.simstate.printNextInstruction()

  def help_s(self): self.write('''\
S
Skip over subroutine call. This command is equivalent to
issuing a STOPAT command with the target address equal to
the last 16-bit value on the stack.\
''')

  def do_stopat(self, line):
    "STOPAT <addr>"
    try: addr = getu16(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return

    br = PySim11.ucBreakpoint()
    br.addr = addr
    br.text = "STOPAT breakpoint"
    br.autoremove = 1
    self.simstate.BPlist.append(br)

    self.simstate.step()
    self.simstate.ucState.display(self.write)
    self.write('\n')
    self.simstate.printNextInstruction()

  def help_stopat(self): self.write('''\
STOPAT <addr>
Begin execution at the current PC and stop when the given address is reached.\
''')

  def evbu_trace(self, line, bforce):
    if len(line):
      try: count = getu16(line, self.simstate)
      except Exception as detail:
        self.write(str(detail)+'\n')
        return
    else: count = 1
    self.simstate.step(count, trace=1, branchForce = bforce)

  def do_t(self, line):
    "T [n]"
    self.evbu_trace(line, 0)

  def do_tn(self, line):
    "TN [n]"
    self.evbu_trace(line, BFORCE_NEVER)

  def do_ty(self, line):
    "TY [n]"
    self.evbu_trace(line, BFORCE_ALWAYS)

  def help_t(self): self.write('''\
T [n]
Trace through program execution for 'n' instructions, or just 1 instruction
if no parameter is specified.\
''')

  def help_tn(self): self.write('''\
TN [n]
Trace through program execution for 'n' instructions, or just 1 instruction
if no parameter is specified. If the next instruction is a branch, it is
NOT TAKEN regardless of the condition codes state.\
''')

  def help_ty(self): self.write('''\
TY [n]
Trace through program execution for 'n' instructions, or just 1 instruction
if no parameter is specified. If the next instruction is a branch, it is
TAKEN regardless of the condition codes state.\
''')

  def do_verf(self, line):
    "VERF <filename>"
    try: addr, diag = VerifyS19(line, self.simstate.ucMemory)
    except Exception as detail:
      if detail: self.write(str(detail)+'\n')
      return
    if diag: self.write(diag)
    self.write(f'Verify of "{line}" successful\n')

  def help_verf(self): self.write('''\
VERF <filename>
This command loads the S19 file specified and compares its contents with
the current contents of memory. The first discrepancy (if any) is
reported.\
''')

  def do_pshb(self, line):
    "PSHB byte"
    try: val = getu8(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return
    self.simstate.ucState.push8(self.simstate.ucMemory, val)

  def help_pshb(self): self.write('''\
PSHB byte
This command pushes the 8-bit 'byte' parameter onto the stack.\
''')

  def do_pshw(self, line):
    "PSHW word"
    try: val = getu16(line, self.simstate)
    except Exception as detail:
      self.write(str(detail)+'\n')
      return
    self.simstate.ucState.push16(self.simstate.ucMemory, val)

  def help_pshw(self): self.write('''\
PSHW word
This command pushes the 16-bit 'word' parameter onto the stack.\
''')


  def help_overview(self): self.write('''\
LOAD     -- Load S19 file             | BF    -- Block fill memory
LOADMAP  -- Load MAP file             | BULK  -- Erase EEPROM
VERF     -- Verify memory/S19 file    | CYC   -- Print/clear cycle counter
                                      | HELP  -- Get help on any command
ASM      -- Disassemble instructions  | MOVE  -- Move memory blocks
BR       -- Set/clear breakpoints     | PRINT -- Evaluate expressions
CALL     -- Call subroutine           | PSHB  -- Push a byte on the stack
GO       -- Run from address          | PSHW  -- Push a word on the stack
L        -- List source lines         | QUIT  -- Exit the program
MD       -- Display memory contents   |
MM       -- Modify memory contents    | Expressions:
P        -- Run at current address    |  [$]HHHH : Hex numbers
RM       -- Print/modify registers    |  %BBBB   : Binary numbers
S        -- Run to end of subroutine  |  &DDDD   : Decimal numbers
STOPAT   -- Run to address            |  -DDDD   : Negative decimals
STOPWHEN -- Run for number of cycles  |  @NNNN   : Octal numbers
T        -- Single-step instructions  |  sym     : Symbol if MAP file loaded
TN       -- Skip next branch          |
TY       -- Take next branch          | Default base is hexadecimal. The
                                      | leading $ sign is optional.\
''')

if __name__ == "__main__":
  import threading
  import queue

  ## import all of the wxPython GUI package
  import wx

  from evbuframe import EVBUFrame

  class MyApp(wx.App):

      # wxWindows calls this method to initialize the application
      def OnInit(self):

          # Queue with unlimited elements for communicating between
          # GUI thread and EVBU thread.
          evbqueue = queue.Queue()

          # Event used to stop the simulator while it's executing
          # Normally, the flag is set. When the user wants to stop
          # executing, the flag is cleared by the GUI and the GUI
          # waits for it to be re-set by PySim11
          simbreak = threading.Event()
          simbreak.set()

          # Create an instance of our customized Frame class
          frame = EVBUFrame(None, -1, "EVBU", evbqueue, simbreak)

          arglist = sys.argv

          EVBUoptions.parseArgs(arglist)

          # I think this improves performance. I'm not sure if it has
          # ill effects with respect to responsiveness, however.
          sys.setswitchinterval(0.010) #sys.setcheckinterval(1000)

          simstate = PySim11.SimState(frame, frame.term.write, simbreak)

          if S19FileName:
            try: addr, diag = ReadS19(S19FileName, simstate.ucMemory)
            except Exception as detail:
              if detail: print(detail)
              return false
            if diag: print(diag)
            simstate.ucState.setPC(addr)

            mapsym.LoadMapFile(S19FileName, simstate)

          if StartPC is not None: simstate.ucState.setPC(StartPC)

          evb = EVBUCmd(simstate, frame, frame.term.write, evbqueue)

          if UseBuffaloServices:
            import buffalo
            bstate = buffalo.BuffaloServices(evb)

          frame.Show(True)

          # Tell wxWindows that this is our main window
          self.SetTopWindow(frame)

          frame.SetEVBU(evb)

          if LoadAndGo: pass  # I'm not sure how to handle this now
            #self.evbthread = threading.Thread(group=None, target=evb.simstate.step)
            #self.evbthread.start()
          else:
            self.evbthread = threading.Thread(group=None, target=evb.cmdloop)
            self.evbthread.start()

          frame.term.input.SetFocus()

          # Return a success flag
          return True

  app = MyApp(0)     # Create an instance of the application class
  app.MainLoop()     # Tell it to start processing events
