;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/ccAHNnyS.i -quiet -dumpbase porte_1.c -mshort -O2 -fshort-double -fomit-frame-pointer -o porte_1.s
; Compiled:     Mon Jan 21 11:22:31 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

?LC0                fcs       'Port E is now: '
?LC1                fcs       LF

Main                proc
                    ldx       _.d1
                    pshx
                    ldx       _.d2
                    pshx
                    ldy       #4110
                    ldd       ,y
                    std       _.d2
                    ldx       #4106
                    ldb       ,x
                    stb       _.d1+1
                    ldd       ,y
                    bra       Done@@

Loop@@              ldx       #4106
                    ldb       ,x
                    cmpb      _.d1+1
                    beq       Cont@@
                    ldb       4106
                    stb       _.d1+1
                    ldd       #?LC0
                    bsr       outstr
                    ldb       _.d1+1
                    bsr       disp8
                    ldd       #?LC1
                    bsr       outstr
Cont@@              ldx       #4110
                    ldd       ,x
Done@@              subd      _.d2
                    cpd       #9999
                    bls       Loop@@
                    clrd
                    pulx
                    stx       _.d2
                    pulx
                    stx       _.d1
                    rts
