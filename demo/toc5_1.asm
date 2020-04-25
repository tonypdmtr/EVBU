;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:    /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/ccn80SrC.i -quiet -dumpbase toc5_1.c -mshort -O2 -fshort-double -fomit-frame-pointer -o toc5_1.s
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
                    ldb       #8
                    stb       ,x
                    ldx       #4096
                    ldb       ,x
                    eorb      #8
                    stb       ,x
                    ldx       #4126
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
                    ldb       #8
                    stb       4134
                    bsr       InterruptsOFF
                    ldx       -32
                    ldd       #tocISR
                    std       1,x
                    ldx       #4096
                    clrb
                    stb       ,x
                    ldx       #4110
                    ldd       ,x
                    addd      #2000
                    std       4126
                    ldx       #4131
                    ldb       #8
                    stb       ,x
_1@@                ldb       ,x
                    bitb      #8
                    beq       _1@@
                    ldx       #4096
                    ldb       ,x
                    orb       #8
                    stb       ,x
                    ldx       #4126
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #8
                    stb       ,x
_2@@                ldb       ,x
                    bitb      #8
                    beq       _2@@
                    ldx       #4096
                    ldb       ,x
                    andb      #-9
                    stb       ,x
                    ldx       #4126
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #8
                    stb       ,x
                    ldb       #3
                    stb       4128
_3@@                ldb       ,x
                    bitb      #8
                    beq       _3@@
                    ldx       #4126
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #8
                    stb       ,x
                    ldb       #2
                    stb       4128
_4@@                ldb       ,x
                    bitb      #8
                    beq       _4@@
                    ldx       #4126
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #8
                    stb       ,x
                    ldb       #1
                    stb       4128
_5@@                ldb       ,x
                    bitb      #8
                    beq       _5@@
                    ldx       #4126
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #8
                    stb       ,x
_6@@                ldb       ,x
                    bitb      #8
                    beq       _6@@
                    ldx       #4126
                    ldd       ,x
                    addd      #2000
                    std       ,x
                    ldx       #4131
                    ldb       #8
                    stb       ,x
                    stb       4130
                    clr       4128
                    jsr       InterruptsON
                    ldx       #4096
_7@@                ldb       ,x
                    bitb      #8
                    beq       _7@@
                    ldx       #4096
_8@@                ldb       ,x
                    bitb      #8
                    bne       _8@@
                    jsr       InterruptsOFF
                    ldb       #1
                    stb       4128
                    ldx       #4107
                    ldb       #8
                    stb       ,x
                    clrd
                    rts
