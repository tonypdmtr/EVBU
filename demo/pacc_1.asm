;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/cccOnvha.i -quiet -dumpbase pacc_1.c -mshort -O2 -fshort-double -fomit-frame-pointer -o pacc_1.s
; Compiled:     Mon Jan 21 11:22:30 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

?gotOV              @var      2

?LC0                fcs       'Pulse accumulator overflow occurred at cycle:'
?LC1                fcs       LF

paovfISR            proc
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
                    ldx       #1
                    stx       ?gotOV
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
                    ldb       #-6
                    stb       ,x
                    tsx
                    ldb       ,x
                    orb       #80
                    stb       ,y
                    ldb       #32
                    stb       4132
                    ldx       #4133
                    stb       ,x
                    ldx       -36
                    ldd       #paovfISR
                    std       1,x
                    jsr       InterruptsON
_1@@                ldd       ?gotOV
                    beq       _1@@
                    ldx       #4135
                    ldb       ,x
                    cmpb      #3
                    bhi       Done@@
Loop@@              ldb       4133
                    bitb      #16
                    beq       Loop@@
                    ldb       #16
                    stb       4133
                    ldb       4135
                    jsr       disp8
                    ldd       #?LC1
                    jsr       outstr
                    ldb       4135
                    cmpb      #3
                    bls       Loop@@
Done@@              clrd
                    ins
                    rts
