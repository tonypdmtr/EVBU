;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/ccYXHmob.i -quiet -dumpbase pacc_2.c -mshort -O2 -fshort-double -fomit-frame-pointer -o pacc_2.s
; Compiled:     Mon Jan 21 11:22:31 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

?gotOV              @var      1

?LC0                fcs       'Pulse accumulator interrupt occurred at cycle:'
?LC1                fcs       LF

paifISR             proc
                    ldx       _.tmp
                    pshx
                    ldx       _.z
                    pshx
                    ldx       _.xy
                    pshx
                    pshx
                    des
                    ldx       #4110
                    ldd       ,x
                    tsy
                    std       ,y
                    ldx       #4135
                    ldb       ,x
                    stb       2,y
                    ldx       #4133
                    ldb       #48
                    stb       ,x
                    ldd       #?LC0
                    bsr       outstr
                    tsx
                    ldd       ,x
                    bsr       disp16
                    ldd       #?LC1
                    bsr       outstr
                    tsx
                    ldb       2,x
                    bsr       disp8
                    ldd       #?LC1
                    bsr       outstr
                    clr       4132
                    ldb       #1
                    stb       ?gotOV
                    pulx
                    ins
                    pulx
                    stx       _.xy
                    pulx
                    stx       _.z
                    pulx
                    stx       _.tmp
                    rti

;*******************************************************************************

Main                proc
                    des
                    jsr       InterruptsOFF
                    ldy       #4134
                    ldb       ,y
                    andb      #127
                    tsx
                    stb       ,x
                    ldx       #4135
                    clrb
                    stb       ,x
                    tsx
                    ldb       ,x
                    orb       #80
                    stb       ,y
                    ldb       #16
                    stb       4132
                    ldx       #4133
                    stb       ,x
                    ldx       -38
                    ldd       #paifISR
                    std       1,x
                    jsr       InterruptsON
_1@@                ldb       ?gotOV
                    beq       _1@@
                    clrd
                    ins
                    rts
