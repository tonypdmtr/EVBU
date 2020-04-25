;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/cc5nqvZN.i -quiet -dumpbase portd_2.c -mshort -O2 -fshort-double -fomit-frame-pointer -o portd_2.s
; Compiled:     Mon Jan 21 11:22:31 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

?LC0                fcs       'Port D is now: '
?LC1                fcs       LF

Main                proc
                    ldx       _.d1
                    pshx
                    ldx       _.d2
                    pshx
                    clr       4105
                    ldy       #4110
                    ldd       ,y
                    std       _.d2
                    ldx       #4104
                    ldb       ,x
                    stb       _.d1+1
                    ldd       ,y
                    bra       Cont@@

Loop@@              ldx       #4104
                    ldb       ,x
                    cmpb      _.d1+1
                    beq       _1@@
                    ldb       4104
                    stb       _.d1+1
                    ldd       #?LC0
                    bsr       outstr
                    ldb       _.d1+1
                    bsr       disp8
                    ldd       #?LC1
                    bsr       outstr
_1@@                ldx       #4110
                    ldd       ,x
Cont@@              subd      _.d2
                    cpd       #9999
                    bls       Loop@@
                    clrd
                    pulx
                    stx       _.d2
                    pulx
                    stx       _.d1
                    rts
