
.SUFFIXES: .c .s19

.c.s19:
	@echo Compiling $< ...
	@m6811-elf-gcc -o $*.s19 -mshort -fshort-double -fomit-frame-pointer -O2 -Wl,--oformat,srec -Wl,-m,m68hc11elfb $< -lc -lbuffalo
	@m6811-elf-gcc -o $*.s -mshort -fshort-double -fomit-frame-pointer -O2 -S $<
	@chmod 644 $*.s19

TARGETS=$(wildcard *.c)

default:
	@echo
	@echo Type \'make all\' to build the S19 files from source. Make sure
	@echo to keep copies of the existing files in case compilation fails.
	@echo

all: $(TARGETS:.c=.s19)

clean:
	-rm -f *.s19 *.s
