CURRENT_BANK: equ $8E
NEWBANK: equ $16
FONT_BANK: equ $10
VAR_PREV_BANK: equ $CAFC
VAR_IMG_TYPE: equ $CAFD
VAR_IS_FIRST: equ $CAFE
VAR_TEXT_TYPE: equ $CAFF

get_next_txtcode: equ $0F3E

    org $0061
Hook_newbank_wrapper:
    push af
    ld a, ($7FFE)
    ld (VAR_PREV_BANK), a

    ld a, NEWBANK
    ld ($2100), a
    jp NEWBANK_main
Hook_newbank_restore:
    ldh a, (CURRENT_BANK)
    ld ($2100), a
    ret
Hook_newbank_restore_specific_bank:
    ld ($2100), a
    ret
Hook_newbank_restore_reg_specific_bank:
    ld ($2100), a
    pop af
    ret
Hook_newbank_restore_reg:
    ldh a, (CURRENT_BANK)
    ld ($2100), a
    pop af
    ret
Hook_newbank_jmp_specific_bank:
    ld ($2100), a
    jp (hl)

get_next_txtcode_newbank:
    push bc
    call get_next_txtcode
    ld a, NEWBANK
    ld ($2100), a
    ld a, b
    pop bc
    ret

get_next_txtcode_menu:
    ldh a, (CURRENT_BANK)
    ld ($2100), a
    ld a, ($C901)
    ld e, a
    ld d, $00
    ld hl, $4032
    add hl, de
    ld l, (hl)
    ld a, NEWBANK
    ld ($2100), a
    ld a, l
    ret

get_byte_from_specific_bank:
    push af
    ld a, ($7FFE)
    ld (VAR_PREV_BANK), a
    pop af
    ld ($2100), a
    ld a, (hl)
    push af
    ld a, (VAR_PREV_BANK)
    ld ($2100), a
    pop af
    ret

get_ptr_from_specific_bank:
    ld ($2100), a
    ldi a, (hl)
    ld h, (hl)
    ld l, a
    ld a, NEWBANK
    ld ($2100), a
    ret

get_tile_from_specific_bank:
    ld ($2100), a
    call $87B
    ld a, $0F
    ld ($2100), a
    ret

    db $88,$88,$88,$88
    org $7A00
Hook_new_menu:
    ld a, $8E
    call $7EB
    call $7F4
    ld hl, $8000
    ld bc, $1800
    call $7DC
    call $823
    ld hl, $4000
    ld de, $8000
    ld a, $02
    call get_tile_from_specific_bank
    ld hl, $7B00
    ld de, $9000
    call $87B
    ld hl, $7E00
    ld de, $D000
    call $87B
    ld hl, $D000
    ld de, $9C00
    ld bc, $1412
    call $809
    ld a, $07
    ld ($C8E7), a
    ldh ($4B), a
    ld a, $90
    ld ($C8E6), a
    ldh ($4A), a

    ld a, $02
    ld ($C8FF), a
    jp $58FE

    db $88,$88,$88,$88
; 코드 패치 Hook 오프셋 리스트 (실제 쓰는 위치는 NEWBANK_HOOK_OFFSET_TABLE 주소) (끝은 0xFFFF)
    dd $EC2, $1476, $14EF, $157F, $E6F
    dd $2996, $29A3, $2A64, $2A71
    dd $3D0D, $1A2D, $1A51, $1AAD, $1AD1, $3A3A, $3BA2, $3BC5
    dd $3914
    dd $16BF
    dd $1B17
    dd $2119
    dd $24A5, $2558
    dd $26BC
    dd $2D56
    dd $2D32
    dd $3C073, $3C13E, $3C146, $3C181, $3C405, $3C413, $3C3FA
    dd $87C, $89C, $8F9
    dd $1AC, $3DA17, $3DA49, $3DA63, $3DA7A
    dd $FFFF
    db $99,$99,$99,$99

NEWBANK_HOOK_OFFSET_TABLE: equ $7F00

    org $7500
NEWBANK_main:
    push bc
    push de
    push hl
    ld hl, $0000
    add hl, sp
    ld bc, $0008
    add hl, bc
    ldi a, (hl)
    ld b, (hl)
    ld c, a
    dec bc
    dec bc
    dec bc

    ld hl, NEWBANK_HOOK_OFFSET_TABLE
    ld a, $FE
    push af
NEWBANK_find_hook_offset:
    pop af
    inc a
    inc a
    push af
    ldi a, (hl)
    ld d, (hl)
    inc hl
    ld e, a
    ld a, d
    cp $FF
    jr z, NEWBANK_find_hook_offset_error
    cp b
    jr nz, NEWBANK_find_hook_offset
    ld a, e
    cp c
    jr nz, NEWBANK_find_hook_offset
    jr NEWBANK_jump_hook
NEWBANK_find_hook_offset_error: ; 테이블에 맞는 오프셋이 없음
    jr NEWBANK_find_hook_offset_error

NEWBANK_jump_hook:
    pop af
    ld hl, NEWBANK_handler_table
    ld c, a
    ld b, $00
    add hl, bc
    ldi a, (hl)
    ld h, (hl)
    ld l, a
    jp (hl)

NEWBANK_handler_table:
    dw Hook_get_font, Hook_get_font2, Hook_get_font3, Hook_get_font4, Hook_convert_code
    dw Hook_get_text1_1, Hook_get_text1_2, Hook_get_text1_1, Hook_get_text1_2
    dw Hook_get_text2_1, Hook_get_text2_2, Hook_get_text2_3, Hook_get_text2_2, Hook_get_text2_4, Hook_get_text2_5, Hook_get_text2_6, Hook_get_text2_7
    dw Hook_get_text3_1
    dw Hook_get_text4_1
    dw Hook_get_text5_1
    dw Hook_get_text6_1
    dw Hook_get_text7_1, Hook_get_text7_2
    dw Hook_get_text8_1
    dw Hook_get_text9_1
    dw Hook_get_text10_1
    dw Hook_get_text11_1, Hook_get_text11_2, Hook_get_text11_3, Hook_get_text11_4, Hook_get_text11_5, Hook_get_text11_6, Hook_get_text11_7
    dw Hook_decompress_image_1, Hook_decompress_image_2, Hook_decompress_image_3
    dw Hook_opening_menu_select, Hook_opening_menu_select2, Hook_opening_menu_select3, Hook_opening_menu_select4, Hook_opening_menu_select5

Hook_return:
    jp Hook_newbank_restore
Hook_return_specific_bank:
    jp Hook_newbank_restore_specific_bank
Hook_return_reg_specific_bank:
    jp Hook_newbank_restore_reg_specific_bank
Hook_return_reg:
    push af
    jp Hook_newbank_restore_reg
Hook_return_jmp_specific_bank:
    jp Hook_newbank_jmp_specific_bank

Hook_get_font:
    pop hl
    pop de
    pop bc
    pop af
    cp $E0
    jr c, Hook_get_font_fallback
    cp $EA
    jr nc, Hook_get_font_fallback
    sub $E0
    push af
    call get_next_txtcode_newbank
    ld l, a
    pop af
    push bc
    ld c, a 
    srl a
    srl a
    ld b, a
    sla a
    sla a
    ld h, a
    ld a, c
    sub h
    ld h, a
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld a, b
    pop bc
    ld de, $4000
    add hl, de
    pop de
    ld de, $0ED2
    push de
    ld d, a
    ld a, FONT_BANK
    add d
    jp Hook_return_specific_bank
Hook_get_font_fallback:
    ld l, a
    ld h, $00
    jp Hook_return


Hook_get_font2:
    pop hl
    pop de
    pop bc
    pop af
    cp $E0
    jr c, Hook_get_font2_fallback
    cp $EA
    jr nc, Hook_get_font2_fallback
    sub $E0
    push af

    call get_next_txtcode_menu
    ld hl, $C901
    inc (hl)

    ld l, a
    pop af
    push bc
    ld c, a 
    srl a
    srl a
    ld b, a
    sla a
    sla a
    ld h, a
    ld a, c
    sub h
    ld h, a
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld a, b
    pop bc
    ld de, $4000
    add hl, de
    pop de
    ld de, $1486
    push de
    ld d, a
    ld a, FONT_BANK
    add d
    jp Hook_return_specific_bank
Hook_get_font2_fallback:
    ld l, a
    ld h, $00
    jp Hook_return


Hook_get_font3:
    pop hl
    pop de
    pop bc
    pop af
    cp $E0
    jr c, Hook_get_font3_fallback
    cp $EA
    jr nc, Hook_get_font3_fallback
    sub $E0
    push af

    push bc
    ld hl, sp+8
    ldi a, (hl)
    ld b, (hl)
    ld hl, $FFB8
    ldi (hl), a
    ld (hl), b
    ld hl, sp+8
    ldi a, (hl)
    ld b, (hl)
    ld c, a
    inc bc
    ld hl, sp+8
    ld a, c
    ldi (hl), a
    ld (hl), b
    pop bc

    call get_next_txtcode_newbank
    ld l, a
    pop af
    push bc
    ld c, a 
    srl a
    srl a
    ld b, a
    sla a
    sla a
    ld h, a
    ld a, c
    sub h
    ld h, a
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld a, b
    pop bc
    ld de, $4000
    add hl, de
    pop de
    ld de, $14FF
    push de
    ld d, a
    ld a, FONT_BANK
    add d
    jp Hook_return_specific_bank
Hook_get_font3_fallback:
    ld l, a
    ld h, $00
    jp Hook_return


Hook_get_font4:
    pop hl
    pop de
    pop bc
    pop af
    cp $E0
    jr c, Hook_get_font4_fallback
    cp $EA
    jr nc, Hook_get_font4_fallback
    sub $E0
    push af

    push bc
    ld hl, sp+8
    ldi a, (hl)
    ld b, (hl)
    ld hl, $FFB8
    ldi (hl), a
    ld (hl), b
    ld hl, sp+8
    ldi a, (hl)
    ld b, (hl)
    ld c, a
    inc bc
    ld hl, sp+8
    ld a, c
    ldi (hl), a
    ld (hl), b
    pop bc

    call get_next_txtcode_newbank
    ld l, a
    pop af
    push bc
    ld c, a 
    srl a
    srl a
    ld b, a
    sla a
    sla a
    ld h, a
    ld a, c
    sub h
    ld h, a
    add hl, hl
    add hl, hl
    add hl, hl
    add hl, hl
    ld a, b
    pop bc
    ld de, $4000
    add hl, de
    pop de
    ld de, $158F
    push de
    ld d, a
    ld a, FONT_BANK
    add d
    jp Hook_return_specific_bank
Hook_get_font4_fallback:
    ld l, a
    ld h, $00
    jp Hook_return


Hook_convert_code:
    pop hl
    pop de
    pop bc
    pop af
    cp $E0
    jr c, Hook_convert_code_fallback
    cp $EA
    jr nc, Hook_convert_code_fallback
    push af
    ldh a, ($BD)
    or a
    jr z, Hook_convert_code_line_top
    ld c, $8C
    jr Hook_convert_code_line_not_top
Hook_convert_code_line_top:
    ld c, $81
Hook_convert_code_line_not_top:
    pop af
    pop de
    ld de, $0EC1
    push de
    jp Hook_return_reg
Hook_convert_code_fallback:
    cp $14
    jr nc, Hook_convert_code_fallback_label
    pop de
    ld de, $0E73
    push de
    jp Hook_return_reg
Hook_convert_code_fallback_label:
    pop de
    ld de, $0E79
    push de
    jp Hook_return_reg


Hook_get_text1_1:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $29F3
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text1_1_type0
    ld l, $FD
Hook_get_text1_1_type0:
    jp Hook_return

Hook_get_text1_2:
    pop hl
    pop de
    pop bc
    pop af
    ldh a, ($B8)
    ld l, a
    ldh a, ($B9)
    ld h, a
    ld a, $12
    jp Hook_return_specific_bank

Hook_get_text2_1:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $48DF
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text2_1_type0
    ld hl, $4921
Hook_get_text2_1_type0:
    ld a, $01
    jp Hook_return_specific_bank

Hook_get_text2_2:
    pop hl
    pop de
    pop bc
    pop af
    xor a
    ldh ($BC), a
    ld a, $12
    ldh (CURRENT_BANK), a
    ldh ($B7), a
    jp Hook_return_specific_bank

Hook_get_text2_3:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $FFBD
    ld a, $01
    ldh (CURRENT_BANK), a
    jp Hook_return_specific_bank

Hook_get_text2_4:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $C902
    ld a, $01
    ldh (CURRENT_BANK), a
    jp Hook_return_specific_bank

Hook_get_text2_5:
    pop hl
    pop de
    pop bc
    pop af
    ldh a, ($B9)
    ld h, a
    ld a, $12
    ldh ($B7), a
    jp Hook_return_specific_bank

Hook_get_text2_6:
    pop hl
    pop de
    pop bc
    pop af
    ldh a, ($B9)
    ld h, a
    ldh a, ($B7)
    jp Hook_return_specific_bank

Hook_get_text2_7:
    pop hl
    pop de
    pop bc
    pop af
    ld a, ($C901)
    jp Hook_return_reg

Hook_get_text3_1:
    pop hl
    pop de
    pop bc
    pop af
    ld de, $4BF6
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text3_1_type0
    ld de, $4C0A
Hook_get_text3_1_type0:
    jp Hook_return

Hook_get_text4_1:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $6A8A
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text4_1_type0
    ld hl, $6B12
Hook_get_text4_1_type0:
    ld a, $08
    jp Hook_return_specific_bank

Hook_get_text5_1:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $7C38
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text5_1_type0
    ld hl, $7C46
Hook_get_text5_1_type0:
    ld a, $08
    jp Hook_return_specific_bank

Hook_get_text6_1:
    pop hl
    pop de
    pop bc
    pop af
    ld h, $00
    ld a, b
    cp $5B
    jr z, Hook_get_text6_1_0x25B16
    cp $6B
    jr z, Hook_get_text6_1_0x2AB05
    cp $59
    jr z, Hook_get_text6_1_0x2D9A9
Error:
    jp Error
Hook_get_text6_1_0x25B16:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text6_1_0x25B16_type0
    ld bc, $5B38
    add hl, bc
    ld a, $15
    ldh ($B7), a
    ld a, $09
    jp Hook_return_specific_bank
Hook_get_text6_1_0x25B16_type0:
    add hl, bc
    ld a, $14
    ldh ($B7), a
    ld a, $09
    jp Hook_return_specific_bank
Hook_get_text6_1_0x2AB05:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text6_1_0x2AB05_type0
    ld bc, $6B2B
Hook_get_text6_1_0x2AB05_type0:
    add hl, bc
    ld a, $16
    ldh ($B7), a
    ld a, $0A
    jp Hook_return_specific_bank
Hook_get_text6_1_0x2D9A9:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text6_1_0x2D9A9_type0
    ld bc, $59CF
    add hl, bc
    ld a, $18
    ldh ($B7), a
    ld a, $0B
    jp Hook_return_specific_bank
Hook_get_text6_1_0x2D9A9_type0:
    add hl, bc
    ld a, $17
    ldh ($B7), a
    ld a, $0B
    jp Hook_return_specific_bank

Hook_get_text7_1:
    pop hl
    pop de
    pop bc
    pop af
    ld h, $00
    ld a, b
    cp $40
    jr z, Hook_get_text7_1_0x2C000
    cp $49
    jr z, Hook_get_text7_1_0x2C945
    cp $50
    jr z, Hook_get_text7_1_0x2D05E
Error2:
    jp Error2
Hook_get_text7_1_0x2C000:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text7_1_0x2C000_type0
    ld bc, $4024
Hook_get_text7_1_0x2C000_type0:
    add hl, bc
    ld a, $19
    ldh ($B7), a
    ld a, $0B
    jp Hook_return_specific_bank
Hook_get_text7_1_0x2C945:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text7_1_0x2C945_type0
    ld bc, $495D
Hook_get_text7_1_0x2C945_type0:
    add hl, bc
    ld a, $17
    ldh ($B7), a
    ld a, $0B
    jp Hook_return_specific_bank
Hook_get_text7_1_0x2D05E:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text7_1_0x2D05E_type0
    ld bc, $5072
Hook_get_text7_1_0x2D05E_type0:
    add hl, bc
    ld a, $18
    ldh ($B7), a
    ld a, $0B
    jp Hook_return_specific_bank

Hook_get_text7_2:
    pop hl
    pop de
    pop bc
    pop af
    ld h, $00
    ld a, b
    cp $40
    jr z, Hook_get_text7_2_0x2C000
    cp $49
    jr z, Hook_get_text7_2_0x2C945
    cp $50
    jr z, Hook_get_text7_2_0x2D05E
Error3:
    jp Error3
Hook_get_text7_2_0x2C000:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text7_2_0x2C000_type0
    ld bc, $4036
Hook_get_text7_2_0x2C000_type0:
    add hl, bc
    ld a, $19
    ldh ($B7), a
    ld a, $0B
    jp Hook_return_specific_bank
Hook_get_text7_2_0x2C945:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text7_2_0x2C945_type0
    ld bc, $4969
Hook_get_text7_2_0x2C945_type0:
    add hl, bc
    ld a, $17
    ldh ($B7), a
    ld a, $0B
    jp Hook_return_specific_bank
Hook_get_text7_2_0x2D05E:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text7_2_0x2D05E_type0
    ld bc, $507E
Hook_get_text7_2_0x2D05E_type0:
    add hl, bc
    ld a, $18
    ldh ($B7), a
    ld a, $0B
    jp Hook_return_specific_bank

Hook_get_text8_1:
    pop hl
    pop de
    pop bc
    pop af
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text8_1_type0
    ld a, l
    add $0A
    ld l, a
Hook_get_text8_1_type0:
    ld a, $18
    ldh ($B7), a
    ld a, $0B
    jp Hook_return_specific_bank

Hook_get_text9_1:
    pop hl
    pop de
    pop bc
    pop af
    ld bc, $74C9
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text9_1_type0
    ld bc, $752D
Hook_get_text9_1_type0:
    ld a, $19
    ldh ($B7), a
    ld a, $0B
    jp Hook_return_specific_bank

Hook_get_text10_1:
    pop hl
    pop de
    pop bc
    pop af
    ld h, $00
    ldh a, ($B7)
    cp $0A
    jr z, Hook_get_text10_1_bankA
    cp $0D
    jr z, Hook_get_text10_1_bankD
    cp $0E
    jr z, Hook_get_text10_1_bankE
Error4:
    jp Error4
Hook_get_text10_1_bankA:
    add hl, hl
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text10_1_bankA_type0
    ld bc, $40B6
    ld a, $1B
    ldh ($B7), a
    ld a, $0A
    jp Hook_return_specific_bank
Hook_get_text10_1_bankA_type0:
    ld a, $1A
    ldh ($B7), a
    ld a, $0A
    jp Hook_return_specific_bank
Hook_get_text10_1_bankD:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text10_1_bankD_type0
    ld bc, $40A2
    ld a, l
    add hl, hl
    cp 27       ; 공간 확보를 위해 테이블 앞쪽부터 이 갯수만큼의 대사를 다른 뱅크로 이동
    jr nc, Hook_get_text10_1_bankD_type1_newbank
    ld a, $15
    ldh ($B7), a
    ld a, $0D
    jp Hook_return_specific_bank
Hook_get_text10_1_bankD_type1_newbank
    ld a, $1F
    ldh ($B7), a
    ld a, $0D
    jp Hook_return_specific_bank
Hook_get_text10_1_bankD_type0:
    ld a, l
    add hl, hl
    cp 27       ; 공간 확보를 위해 테이블 앞쪽부터 이 갯수만큼의 대사를 다른 뱅크로 이동
    jr nc, Hook_get_text10_1_bankD_type0_newbank
    ld a, $14
    ldh ($B7), a
    ld a, $0D
    jp Hook_return_specific_bank
Hook_get_text10_1_bankD_type0_newbank
    ld a, $1E
    ldh ($B7), a
    ld a, $0D
    jp Hook_return_specific_bank
Hook_get_text10_1_bankE:
    add hl, hl
    ld a, b
    cp $40
    jr z, Hook_get_text10_1_bankE_0x4000
    cp $6D
    jr z, Hook_get_text10_1_bankE_0x6D85
Error5:
    jp Error5
Hook_get_text10_1_bankE_0x4000:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text10_1_bankE_0x4000_type0
    ld bc, $4094
    ld a, $1D
    ldh ($B7), a
    ld a, $0E
    jp Hook_return_specific_bank
Hook_get_text10_1_bankE_0x4000_type0:
    ld a, $1C
    ldh ($B7), a
    ld a, $0E
    jp Hook_return_specific_bank
Hook_get_text10_1_bankE_0x6D85:
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text10_1_bankE_0x6D85_type0
    ld bc, $6D9F
Hook_get_text10_1_bankE_0x6D85_type0:
    ld a, $12
    ldh ($B7), a
    ld a, $0E
    jp Hook_return_specific_bank

Hook_get_text11_1:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $7FA0
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text11_1_type0
    ld hl, $7FAC
Hook_get_text11_1_type0:
    ld a, $0F
    call get_ptr_from_specific_bank
    ld a, $0F
    jp Hook_return_specific_bank

Hook_get_text11_2:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $7FA2
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text11_2_type0
    ld hl, $7FAE
Hook_get_text11_2_type0:
    ld a, $0F
    call get_ptr_from_specific_bank
    ld a, $0F
    jp Hook_return_specific_bank

Hook_get_text11_3:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $7FA4
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text11_3_type0
    ld hl, $7FB0
Hook_get_text11_3_type0:
    ld a, $0F
    call get_ptr_from_specific_bank
    ld a, $0F
    jp Hook_return_specific_bank

Hook_get_text11_4:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $7FA6
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text11_4_type0
    ld hl, $7FB2
Hook_get_text11_4_type0:
    ld a, $0F
    call get_ptr_from_specific_bank
    ld a, $0F
    jp Hook_return_specific_bank

Hook_get_text11_5:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $7FA8
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text11_5_type0
    ld hl, $7FB4
Hook_get_text11_5_type0:
    ld a, $0F
    call get_ptr_from_specific_bank
    ld a, $0F
    jp Hook_return_specific_bank

Hook_get_text11_6:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $7FAA
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text11_6_type0
    ld hl, $7FB6
Hook_get_text11_6_type0:
    ld a, $0F
    call get_ptr_from_specific_bank
    ld a, $0F
    jp Hook_return_specific_bank

Hook_get_text11_7:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $7FC0
    ld a, (VAR_TEXT_TYPE)
    or a
    jr z, Hook_get_text11_7_type0
    ld hl, $7FC8
Hook_get_text11_7_type0:
    add hl, bc
    ld a, $0F
    call get_ptr_from_specific_bank
    ld a, $1A
    ldh ($B7), a
    ld a, l
    ldh ($B8), a
    ld a, h
    ldh ($B9), a
    ld a, $03
    ldh ($BA), a
    ld a, $0F
    jp Hook_return_specific_bank


Hook_decompress_image_1:
    pop hl
    pop de
    pop bc
    pop af
    ld ($C8A0), a
    ld a, h
    cp $66
    jr nz, Hook_decompress_image_1_fallback
    ld a, l
    cp $04
    jr nz, Hook_decompress_image_1_fallback
    ld a, $01
    ld (VAR_IMG_TYPE), a
    ld hl, $7200
    ld a, $05
    jp Hook_return_specific_bank
Hook_decompress_image_1_fallback:
    xor a
    ld (VAR_IMG_TYPE), a
    ld a, (VAR_PREV_BANK)
    jp Hook_return_specific_bank

Hook_decompress_image_2:
    pop hl
    pop de
    pop bc
    pop af
    ld a, (VAR_IMG_TYPE)
    cp a
    jr z, Hook_decompress_image_2_fallback
    cp $01
    jr z, Hook_decompress_image_2_title
Error6:
    jr Error6
Hook_decompress_image_2_title:
    ld a, ($C8A2)
    push af
    ld a, $05
    jp Hook_return_reg_specific_bank
Hook_decompress_image_2_fallback:
    ld a, ($C8A2)
    push af
    ld a, (VAR_PREV_BANK)
    jp Hook_return_reg_specific_bank

Hook_decompress_image_3:
    pop hl
    pop de
    pop bc
    pop af
    dec c
    jr z, Hook_decompress_image_3_return
    dec b
    ld a, (VAR_PREV_BANK)
    jp Hook_return_specific_bank
Hook_decompress_image_3_return:
    pop hl
    pop hl
    ld a, (VAR_PREV_BANK)
    jp Hook_return_jmp_specific_bank


Hook_opening_menu_select:
    pop hl
    pop de
    pop bc
    pop af
    ld a, (VAR_IS_FIRST)
    cp $00
    jr nz, Hook_opening_menu_select_fallback
    ld a, ($C8FD)
    cp $08
    jr nz, Hook_opening_menu_select_fallback
    pop de
    ld de, Hook_new_menu
    push de
    jp Hook_return
Hook_opening_menu_select_fallback
    ld a, ($C8FD)
    jp Hook_return_reg

Hook_opening_menu_select2:
    pop hl
    pop de
    pop bc
    pop af
    push af
    ld a, (VAR_IS_FIRST)
    cp $00
    jr nz, Hook_opening_menu_select2_fallback
    pop af
    xor a
    ld ($C915), a
    ld a, $0F
    jp Hook_return_specific_bank
Hook_opening_menu_select2_fallback
    pop af
    ld ($C915), a
    ld a, $0F
    jp Hook_return_specific_bank

Hook_opening_menu_select3:
    pop hl
    pop de
    pop bc
    pop af
    ld a, (VAR_IS_FIRST)
    cp $00
    jr nz, Hook_opening_menu_select3_fallback
    ld a, (hl)
    cp $01
    push af
    ld a, $0F
    jp Hook_return_reg_specific_bank
Hook_opening_menu_select3_fallback
    ld a, (hl)
    cp $02
    push af
    ld a, $0F
    jp Hook_return_reg_specific_bank

Hook_opening_menu_select4:
    pop hl
    pop de
    pop bc
    pop af
    ld hl, $5B0D
    ld a, (VAR_IS_FIRST)
    cp $00
    jr nz, Hook_opening_menu_select4_fallback
    ld a, ($C915)
    cp $00
    jr nz, Hook_opening_menu_select4_second
    ld a, $4C
    ldh ($A0), a
    ld a, $0F
    jp Hook_return_specific_bank
Hook_opening_menu_select4_second:
    ld a, $6C
    ldh ($A0), a
    ld a, $0F
    jp Hook_return_specific_bank
Hook_opening_menu_select4_fallback
    ld a, $0F
    jp Hook_return_specific_bank

Hook_opening_menu_select5:
    pop hl
    pop de
    pop bc
    pop af
    ld a, (VAR_IS_FIRST)
    cp $00
    jr nz, Hook_opening_menu_select5_fallback
    di
    ld a, $01
    ld (VAR_IS_FIRST), a
    ld a, $0F
    call get_byte_from_specific_bank
    xor $01
    ld (VAR_TEXT_TYPE), a
    ld a, $00
    ld ($FF40), a
    ld a, $08
    ld ($FFFF), a
    pop bc
    pop hl
    ld hl, $58E7
    push hl
    push bc
    ld a, $0F
    jp Hook_return_specific_bank
Hook_opening_menu_select5_fallback
    ld a, $0F
    call get_byte_from_specific_bank
    ld ($DE08), a
    ld a, $0F
    jp Hook_return_specific_bank
