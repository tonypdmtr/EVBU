;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/cc8miWfY.i -quiet -dumpbase ex1.c -mshort -O2 -fshort-double -fomit-frame-pointer -o ex1.s
; Compiled:     Mon Jan 21 11:22:30 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

Main                proc
                    clrx
                    ldy       #4131
                    ldd       #4096
                    std       _.z
Loop@@              ldd       4110
                    addd      #2000
                    std       4120
                    ldb       #64
                    stb       ,y
                    inx
_1@@                ldb       ,y
                    bitb      #64
                    beq       _1@@
                    stx       _.xy
                    ldx       _.z
                    ldb       ,x
                    eorb      #64
                    stb       ,x
                    ldx       _.xy
                    cpx       #2
                    ble       Loop@@
                    clrd
                    rts
