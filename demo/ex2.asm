;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/ccpaXrj4.i -quiet -dumpbase ex2.c -mshort -O2 -fshort-double -fomit-frame-pointer -o ex2.s
; Compiled:     Mon Jan 21 11:22:30 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

?LC0                fcs       'Port A changed at cycle '
?LC1                fcs       LF

Main                proc
                    pshx
                    ldx       _.d1
                    pshx
                    ldx       #4096
                    ldb       ,x
                    stb       _.d1+1
                    clrd
Loop@@              incd
                    tsx
                    std       2,x
_1@@                ldb       4096
                    cmpb      _.d1+1
                    beq       _1@@
                    xgdx
                    ldb       4096
                    stb       _.d1+1
                    xgdx
                    ldd       #?LC0
                    bsr       outstr
                    ldx       #4110
                    ldd       ,x
                    bsr       disp16
                    ldd       #?LC1
                    bsr       outstr
                    tsx
                    ldd       2,x
                    cpd       #2
                    ble       Loop@@
                    clrd
                    pulx
                    stx       _.d1
                    pulx
                    rts
