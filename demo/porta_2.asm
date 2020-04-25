;*******************************************************************************
; Start MC68HC11 gcc assembly output
; gcc compiler 2.95.3 20010315 (release)+m68hc1x-20010922
; Command:      /usr/lib/gcc-lib/m6811-elf/2.95.3/cc1 /tmp/ccWZLUin.i -quiet -dumpbase porta_2.c -mshort -O2 -fshort-double -fomit-frame-pointer -o porta_2.s
; Compiled:     Mon Jan 21 11:22:31 2002
; (META)compiled by GNU C version 2.95.3 20010315 (release).
;*******************************************************************************

                    #Uses     defs.inc

Main                proc
                    ldx       _.d1
                    pshx
                    ldx       #4110
                    ldd       ,x
                    std       _.d1
                    ldd       ,x
                    subd      _.d1
                    cpd       #4999
                    bhi       Done@@
                    ldx       #4096
                    ldy       #4110
Loop@@              ldb       ,x
                    andb      #7
                    aslb:4
                    stb       ,x
                    ldd       ,y
                    subd      _.d1
                    cpd       #4999
                    bls       Loop@@
Done@@              clrd
                    pulx
                    stx       _.d1
                    rts
