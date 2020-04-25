;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:    /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/ccEQWXLl.i -quiet -dumpbase toc1_1.c -mshort -O2 -fshort-double -fomit-frame-pointer -o toc1_1.s
; Compiled:   Mon Jan 21 11:46:29 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

?flag               @var      1

tocISR              proc
                    ldx       _.tmp
                    pshx
                    ldx       _.z
                    pshx
                    ldx       _.xy
                    pshx
                    ldx       #4131
                    ldb       #-128
                    stb       ,x
                    lsr       4109
                    ldx       #4118
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldd       #1
                    std       ?flag
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
                    ldx       -24
                    ldd       #tocISR
                    std       1,x
                    ldx       #4096
                    clrb
                    stb       ,x
                    ldb       #-120
                    stb       4134
                    ldx       #4110
                    ldd       ,x
                    std       4118
                    ldb       #-8
                    stb       4108
                    clr       4109
                    clrx
                    ldd       #4118
                    ldy       #4131
                    std       _.z
_1@@                ldb       4109
                    aslb
                    orb       #8
                    stb       4109
                    stx       _.xy
                    ldx       _.z
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldb       #-128
                    stb       ,y
                    ldx       _.xy
_2@@                ldb       ,y
                    bpl       _2@@
                    inx
                    cpx       #4
                    ble       _1@@
                    ldx       #4118
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #-128
                    stb       ,x
                    stb       4130
                    lsr       4109
                    jsr       InterruptsON
                    clrx
                    stx       _.tmp
                    ldy       _.tmp
_3@@                sty       ?flag
                    inx
_4@@                ldd       ?flag
                    beq       _4@@
                    cpx       #4
                    ble       _3@@
                    ldb       #-120
                    stb       4109
                    ldb       #-128
                    stb       4107
                    clrd
                    rts
