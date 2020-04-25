;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/ccuEh1o0.i -quiet -dumpbase rtif_1.c -mshort -O2 -fshort-double -fomit-frame-pointer -o rtif_1.s
; Compiled:     Tue Jan 22 14:48:50 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

?done               @var      2

rtifISR             proc
                    ldx       _.tmp
                    pshx
                    ldx       _.z
                    pshx
                    ldx       _.xy
                    pshx
                    ldx       #4133
                    ldb       #64
                    stb       ,x
                    ldx       #4096
                    ldb       ,x
                    eorb      #64
                    stb       ,x
                    ldd       #1
                    std       ?done
                    pulx
                    stx       _.xy
                    pulx
                    stx       _.z
                    pulx
                    stx       _.tmp
                    rti

;*******************************************************************************

Main                proc
                    bsr       InterruptsOFF
                    ldx       -16
                    ldd       #rtifISR
                    std       1,x
                    ldx       #4096
                    clrb
                    stb       ,x
                    ldx       #4133
_1@@                ldb       ,x
                    bitb      #64
                    beq       _1@@
                    ldx       #4096
                    ldb       ,x
                    eorb      #64
                    stb       ,x
                    ldx       #4133
                    ldb       #64
                    stb       ,x
                    stb       4132
                    bsr       InterruptsON
_2@@                ldd       ?done
                    beq       _2@@
                    clrd
                    rts
