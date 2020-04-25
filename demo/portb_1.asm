;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/ccZszSYr.i -quiet -dumpbase portb_1.c -mshort -O2 -fshort-double -fomit-frame-pointer -o portb_1.s
; Compiled:     Mon Jan 21 11:22:31 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

Main                proc
                    clr       4100
                    ldy       #1
                    ldx       #4100
Loop@@              sty       _.xy
                    xgdy
                    ldb       ,x
                    xgdy
                    sty       _.z
                    ldy       _.xy
                    stx       _.xy
                    ldx       _.z
                    sty       _.tmp
                    xgdx
                    orb       _.tmp+1
                    ldx       _.xy
                    stb       ,x
                    xgdy
                    asld
                    xgdy
                    cpy       #128
                    ble       Loop@@
                    ldy       #1
                    ldx       #4100
_1@@                sty       _.tmp
                    ldb       _.tmp+1
                    comb
                    andb      ,x
                    stb       ,x
                    xgdy
                    asld
                    xgdy
                    cpy       #128
                    ble       _1@@
                    clrd
                    rts
