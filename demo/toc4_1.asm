;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:    /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/ccURMSLv.i -quiet -dumpbase toc4_1.c -mshort -O2 -fshort-double -fomit-frame-pointer -o toc4_1.s
; Compiled:   Mon Jan 21 11:52:21 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

tocISR              proc
                    ldx       _.tmp
                    pshx
                    ldx       _.z
                    pshx
                    ldx       _.xy
                    pshx
                    ldx       #4131
                    ldb       #16
                    stb       ,x
                    ldx       #4096
                    ldb       ,x
                    eorb      #16
                    stb       ,x
                    ldx       #4124
                    ldd       ,x
                    addd      #2000
                    std       ,x
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
                    ldx       -30
                    ldd       #tocISR
                    std       1,x
                    ldx       #4096
                    clrb
                    stb       ,x
                    ldx       #4110
                    ldd       ,x
                    addd      #2000
                    std       4124
                    ldx       #4131
                    ldb       #16
                    stb       ,x
_1@@                ldb       ,x
                    bitb      #16
                    beq       _1@@
                    ldx       #4096
                    ldb       ,x
                    orb       #16
                    stb       ,x
                    ldx       #4124
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #16
                    stb       ,x
_2@@                ldb       ,x
                    bitb      #16
                    beq       _2@@
                    ldx       #4096
                    ldb       ,x
                    andb      #-17
                    stb       ,x
                    ldx       #4124
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #16
                    stb       ,x
                    ldb       #12
                    stb       4128
_3@@                ldb       ,x
                    bitb      #16
                    beq       _3@@
                    ldx       #4124
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #16
                    stb       ,x
                    ldb       #8
                    stb       4128
_4@@                ldb       ,x
                    bitb      #16
                    beq       _4@@
                    ldx       #4124
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #16
                    stb       ,x
                    ldb       #4
                    stb       4128
_5@@                ldb       ,x
                    bitb      #16
                    beq       _5@@
                    ldx       #4124
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #16
                    stb       ,x
_6@@                ldb       ,x
                    bitb      #16
                    beq       _6@@
                    ldx       #4124
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #16
                    stb       ,x
                    stb       4130
                    clr       4128
                    jsr       InterruptsON
                    ldx       #4096
_7@@                ldb       ,x
                    bitb      #16
                    beq       _7@@
                    ldx       #4096
_8@@                ldb       ,x
                    bitb      #16
                    bne       _8@@
                    jsr       InterruptsOFF
                    ldb       #4
                    stb       4128
                    ldx       #4107
                    ldb       #16
                    stb       ,x
                    clrd
                    rts
