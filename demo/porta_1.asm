;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/ccH8qogh.i -quiet -dumpbase porta_1.c -mshort -O2 -fshort-double -fomit-frame-pointer -o porta_1.s
; Compiled:     Mon Jan 21 11:22:31 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

Main                proc
                    des
                    ldx       #4134
                    ldb       ,x
                    orb       #-120
                    stb       ,x
                    ldx       #4096
                    clrb
                    stb       ,x
                    ldy       #8
_1@@                ldb       ,x
                    sty       _.tmp
                    orb       _.tmp+1
                    stb       ,x
                    xgdy
                    asld
                    xgdy
                    cpy       #128
                    ble       _1@@
                    ldy       #8
                    ldx       #4096
Loop@@              sty       _.tmp
                    ldb       _.tmp+1
                    comb
                    sty       _.xy
                    tsy
                    stb       ,y
                    ldb       ,x
                    andb      ,y
                    ldy       _.xy
                    stb       ,x
                    xgdy
                    asld
                    xgdy
                    cpy       #128
                    ble       Loop@@
                    clrd
                    ins
                    rts
