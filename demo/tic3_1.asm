;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/cco3OtMf.i -quiet -dumpbase tic3_1.c -mshort -O2 -fshort-double -fomit-frame-pointer -o tic3_1.s
; Compiled:     Tue Jan 22 14:28:27 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

?intcount           @var      2

?LC0                fcs       LF

ticISR              proc
                    ldx       _.tmp
                    pshx
                    ldx       _.z
                    pshx
                    ldx       _.xy
                    pshx
                    ldx       #4131
                    ldb       #1
                    stb       ,x
                    ldx       #4116
                    ldd       ,x
                    bsr       disp16
                    ldd       #?LC0
                    bsr       outstr
                    ldd       ?intcount
                    incd
                    std       ?intcount
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
                    ldx       -22
                    ldd       #ticISR
                    std       1,x
                    ldb       #3
                    stb       4129
                    ldx       #4131
                    ldb       #1
                    stb       ,x
_1@@                ldb       ,x
                    bitb      #1
                    beq       _1@@
                    ldx       #4116
                    ldd       ,x
                    bsr       disp16
                    ldd       #?LC0
                    bsr       outstr
                    ldx       #4131
                    ldb       #1
                    stb       ,x
_2@@                ldb       ,x
                    bitb      #1
                    beq       _2@@
                    ldx       #4116
                    ldd       ,x
                    bsr       disp16
                    ldd       #?LC0
                    bsr       outstr
                    ldb       #1
                    stb       4130
                    ldx       #4131
                    stb       ,x
                    bsr       InterruptsON
_3@@                ldd       ?intcount
                    cpd       #1
                    ble       _3@@
                    clrd
                    rts
