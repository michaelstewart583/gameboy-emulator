import sys
import argparse
import emulator
import time
import threading
from tkinter import * 
from tkinter.ttk import *

#VBlank
IEF_VBLANK = 0b00000001 # V-Blank
rIE = 0xFFFF # interrupt enable register

#VRAM
_VRAM = 0x8000
_VRAM8000 = 0x8000
_VRAM8800 = 0x8800
_VRAM9000 = 0x9000

START_TILESET = 0x8000
START_TILEMAP1 = 0x9800
START_TILEMAP2 = 0x9C00

#for wait for vblank
SCRN_Y = 144
SCRN_X = 160
rLY = 0xFF44

#Background
rBGP = 0xFF47

#LCD Control
rLCDC = 0xFF40

LCDCF_OFF     = 0b00000000 # LCD Control Operation
LCDCF_ON      = 0b10000000 # LCD Control Operation
LCDCF_WIN9800 = 0b00000000 # Window Tile Map Display Select
LCDCF_WIN9C00 = 0b01000000 # Window Tile Map Display Select
LCDCF_WINOFF  = 0b00000000 # Window Display
LCDCF_WINON   = 0b00100000 # Window Display
LCDCF_BG8800  = 0b00000000 # BG & Window Tile Data Select
LCDCF_BG8000  = 0b00010000 # BG & Window Tile Data Select
LCDCF_BG9800  = 0b00000000 # BG Tile Map Display Select
LCDCF_BG9C00  = 0b00001000 # BG Tile Map Display Select
LCDCF_OBJ8    = 0b00000000 # OBJ Construction
LCDCF_OBJ16   = 0b00000100 # OBJ Construction
LCDCF_OBJOFF  = 0b00000000 # OBJ Display
LCDCF_OBJON   = 0b00000010 # OBJ Display
LCDCF_BGOFF   = 0b00000000 # BG Display
LCDCF_BGON    = 0b00000001 # BG Display

#background
rSCY = 0xFF42
rSCX = 0xFF43

#joypad
rP1 = 0xFF00

P1F_5 = 0b00100000 # P15 out port, set to 0 to get buttons
P1F_4 = 0b00010000 # P14 out port, set to 0 to get dpad

P1F_GET_DPAD = P1F_5
P1F_GET_BTN  = P1F_4
P1F_GET_NONE = P1F_4 | P1F_5

JOYPAD_BUTTON_MAP =      \
    {"Up"      : "UP",     
     "Down"    : "DOWN",    
     "Left"    : "LEFT",   
     "Right"   : "RIGHT",  
     "Enter"   : "START",  
     "Shift_R" : "SELECT", 
     "a"       : "B",      
     "s"       : "A"}

JOYPAD_BUTTON_TO_BITS = \
    {"DOWN"   : 0b00001000,
     "UP"     : 0b00000100,
     "LEFT"   : 0b00000010,
     "RIGHT"  : 0b00000001,
     "START"  : 0b00001000,
     "SELECT" : 0b00000100,
     "A"      : 0b00000010,
     "B"      : 0b00000001}

OPCODES = """0x00	nop	1	1	----
0x01	ld bc,n16	3	3	----
0x02	ld [bc],a	1	2	----
0x03	inc bc	1	2	----
0x04	inc b	1	1	Z0H-
0x05	dec b	1	1	Z1H-
0x06	ld b,n8	2	2	----
0x07	rlca	1	1	000C
0x08	ld [n16],sp	3	5	----
0x09	add hl,bc	1	2	-0HC
0x0A	ld a,[bc]	1	2	----
0x0B	dec bc	1	2	----
0x0C	inc c	1	1	Z0H-
0x0D	dec c	1	1	Z1H-
0x0E	ld c,n8	2	2	----
0x0F	rrca	1	1	000C
0x10	stop	2	1	----
0x11	ld de,n16	3	3	----
0x12	ld [de],a	1	2	----
0x13	inc de	1	2	----
0x14	inc d	1	1	Z0H-
0x15	dec d	1	1	Z1H-
0x16	ld d,n8	2	2	----
0x17	rla	1	1	000C
0x18	jr s8	2	3	----
0x19	add hl,de	1	2	-0HC
0x1A	ld a,[de]	1	2	----
0x1B	dec de	1	2	----
0x1C	inc e	1	1	Z0H-
0x1D	dec e	1	1	Z1H-
0x1E	ld e,n8	2	2	----
0x1F	rra	1	1	000C
0x20	jr nz,s8	2	3/2	----
0x21	ld hl,n16	3	3	----
0x22	ldi [hl],a	1	2	----
0x23	inc hl	1	2	----
0x24	inc h	1	1	Z0H-
0x25	dec h	1	1	Z1H-
0x26	ld h,n8	2	2	----
0x27	daa	1	1	Z-0C
0x28	jr z,s8	2	3/2	----
0x29	add hl,hl	1	2	-0HC
0x2A	ldi a,[hl]	1	2	----
0x2B	dec hl	1	2	----
0x2C	inc l	1	1	Z0H-
0x2D	dec l	1	1	Z1H-
0x2E	ld l,n8	2	2	----
0x2F	cpl	1	1	-11-
0x30	jr nc,s8	2	3/2	----
0x31	ld sp,n16	3	3	----
0x32	ldd [hl],a	1	2	----
0x33	inc sp	1	2	----
0x34	inc [hl]	1	3	Z0H-
0x35	dec [hl]	1	3	Z1H-
0x36	ld [hl],n8	2	3	----
0x37	scf	1	1	-001
0x38	jr c,s8	2	3/2	----
0x39	add hl,sp	1	1	----
0x3A	ldd a,[hl]	1	2	----
0x3B	dec sp	1	1	----
0x3C	inc a	1	1	Z0H-
0x3D	dec a	1	1	----
0x3E	ld a,n8	2	2	----
0x3F	ccf	1	1	Z0HC
0x40	ld b,b	1	1	----
0x41	ld b,c	1	1	Z0HC
0x42	ld b,d	1	1	----
0x43	ld b,e	1	1	Z0HC
0x44	ld b,h	1	1	----
0x45	ld b,l	1	1	Z0HC
0x46	ld b,[hl]	1	2	----
0x47	ld b,a	1	1	Z0HC
0x48	ld c,b	1	1	----
0x49	ld c,c	1	1	Z0HC
0x4A	ld c,d	1	1	----
0x4B	ld c,e	1	1	Z0HC
0x4C	ld c,h	1	1	----
0x4D	ld c,l	1	1	Z0HC
0x4E	ld c,[hl]	1	2	----
0x4F	ld c,a	1	1	Z1HC
0x50	ld d,b	1	1	----
0x51	ld d,c	1	1	Z1HC
0x52	ld d,d	1	1	----
0x53	ld d,e	1	1	Z1HC
0x54	ld d,h	1	1	----
0x55	ld d,l	1	1	11HC
0x56	ld d,[hl]	1	2	----
0x57	ld d,a	1	1	Z1HC
0x58	ld e,b	1	1	----
0x59	ld e,c	1	1	Z1HC
0x5A	ld e,d	1	1	----
0x5B	ld e,e	1	1	Z1HC
0x5C	ld e,h	1	1	----
0x5D	ld e,l	1	1	Z1HC
0x5E	ld e,[hl]	1	2	----
0x5F	ld e,a	1	1	Z010
0x60	ld h,b	1	1	----
0x61	ld h,c	1	1	Z010
0x62	ld h,d	1	1	----
0x63	ld h,e	1	1	Z010
0x64	ld h,h	1	1	----
0x65	ld h,l	1	1	Z010
0x66	ld h,[hl]	1	2	----
0x67	ld h,a	1	1	Z000
0x68	ld l,b	1	1	----
0x69	ld l,c	1	1	Z000
0x6A	ld l,d	1	1	----
0x6B	ld l,e	1	1	Z000
0x6C	ld l,h	1	1	----
0x6D	ld l,l	1	1	1000
0x6E	ld l,[hl]	1	2	----
0x6F	ld l,a	1	1	Z000
0x70	ld [hl],b	1	2	----
0x71	ld [hl],c	1	1	Z000
0x72	ld [hl],d	1	2	----
0x73	ld [hl],e	1	1	Z000
0x74	ld [hl],h	1	2	----
0x75	ld [hl],l	1	1	Z000
0x76	halt	1	1	----
0x77	ld [hl],a	1	1	Z1HC
0x78	ld a,b	1	1	----
0x79	ld a,c	1	1	Z1HC
0x7A	ld a,d	1	1	----
0x7B	ld a,e	1	1	----
0x7C	ld a,h	1	1	----
0x7D	ld a,l	1	1	----
0x7E	ld a,[hl]	1	2	----
0x7F	ld a,a	1	1	----
0x80	add a,b	1	1	Z0HC
0x81	add a,c	1	1	Z0HC
0x82	add a,d	1	1	Z0HC
0x83	add a,e	1	1	Z0HC
0x84	add a,h	1	1	Z0HC
0x85	add a,l	1	1	Z0HC
0x86	add a,[hl]	1	2	Z0HC
0x87	add a,a	1	1	Z0HC
0x88	adc a,b	1	1	Z0HC
0x89	adc a,c	1	1	Z0HC
0x8A	adc a,d	1	1	Z0HC
0x8B	adc a,e	1	1	Z0HC
0x8C	adc a,h	1	1	Z0HC
0x8D	adc a,l	1	1	Z0HC
0x8E	adc a,[hl]	1	2	Z0HC
0x8F	adc a,a	1	1	Z0HC
0x90	sub b	1	1	Z1HC
0x91	sub c	1	1	Z1HC
0x92	sub d	1	1	Z1HC
0x93	sub e	1	1	Z1HC
0x94	sub h	1	1	Z1HC
0x95	sub l	1	1	Z1HC
0x96	sub [hl]	1	2	Z1HC
0x97	sub a	1	1	11HC
0x98	sbc a,b	1	1	Z1HC
0x99	sbc a,c	1	1	Z1HC
0x9A	sbc a,d	1	1	Z1HC
0x9B	sbc a,e	1	1	Z1HC
0x9C	sbc a,h	1	1	Z1HC
0x9D	sbc a,l	1	1	Z1HC
0x9E	sbc a,[hl]	1	2	Z1HC
0x9F	sbc a,a	1	1	Z1HC
0xA0	and b	1	1	Z010
0xA1	and c	1	1	Z010
0xA2	and d	1	1	Z010
0xA3	and e	1	1	Z010
0xA4	and h	1	1	Z010
0xA5	and l	1	1	Z010
0xA6	and [hl]	1	2	Z010
0xA7	and a	1	1	Z010
0xA8	xor b	1	1	Z000
0xA9	xor c	1	1	Z000
0xAA	xor d	1	1	Z000
0xAB	xor e	1	1	Z000
0xAC	xor h	1	1	Z000
0xAD	xor l	1	1	Z000
0xAE	xor [hl]	1	2	Z000
0xAF	xor a	1	1	1000
0xB0	or b	1	1	Z000
0xB1	or c	1	1	Z000
0xB2	or d	1	1	Z000
0xB3	or e	1	1	Z000
0xB4	or h	1	1	Z000
0xB5	or l	1	1	Z000
0xB6	or [hl]	1	2	Z000
0xB7	or a	1	1	Z000
0xB8	cp b	1	1	Z1HC
0xB9	cp c	1	1	Z1HC
0xBA	cp d	1	1	Z1HC
0xBB	cp e	1	1	Z1HC
0xBC	cp h	1	1	Z1HC
0xBD	cp l	1	1	Z1HC
0xBE	cp [hl]	1	2	Z1HC
0xBF	cp a	1	1	11HC
0xC0	ret nz	1	5/2	----
0xC1	pop bc	1	3	----
0xC2	jp nz,n16	3	4/3	----
0xC3	jp n16	3	4	----
0xC4	call nz,n16	3	6/3	----
0xC5	push bc	1	4	----
0xC6	add a,n8	2	2	Z0HC
0xC7	rst 00h	1	4	----
0xC8	ret z	1	5/2	----
0xC9	ret	1	4	----
0xCA	jp z,n16	3	4/3	----
0xCB	prefix	-	-	----
0xCC	call z,n16	3	6/3	----
0xCD	call n16	3	6	----
0xCE	adc a,n8	2	2	Z0HC
0xCF	rst 08h	1	4	----
0xD0	ret nc	1	5/2	----
0xD1	pop de	1	3	----
0xD2	jp nc,n16	3	4/3	----
0xD3	-	-	-	----
0xD4	call nc,n16	3	6/3	----
0xD5	push de	1	4	----
0xD6	sub n8	2	2	Z1HC
0xD7	rst 10h	1	4	----
0xD8	ret c	1	5/2	----
0xD9	reti	1	4	----
0xDA	jp c,n16	3	4/3	----
0xDB	-	-	-	----
0xDC	call c,n16	3	6/3	----
0xDD	-	-	-	----
0xDE	sbc a,n8	2	2	Z1HC
0xDF	rst 18h	1	4	----
0xE0	ldh [a8],a	2	3	----
0xE1	pop hl	1	3	----
0xE2	ld [c],a	1	2	----
0xE3	-	-	-	----
0xE4	-	-	-	----
0xE5	push hl	1	4	----
0xE6	and n8	2	2	Z010
0xE7	rst 20h	1	4	----
0xE8	add sp,s8	2	4	00HC
0xE9	jp hl	1	1	----
0xEA	ld [n16],a	3	4	----
0xEB	-	-	-	----
0xEC	-	-	-	----
0xED	-	-	-	----
0xEE	xor n8	2	2	Z000
0xEF	rst 28h	1	4	----
0xF0	ldh a,[a8]	2	3	----
0xF1	pop af	1	3	ZNHC
0xF2	ld a,[c]	2	3	----
0xF3	di	1	1	----
0xF4	-	-	-	----
0xF5	push af	1	4	----
0xF6	or n8	2	2	Z000
0xF7	rst 30h	1	4	----
0xF8	ld hl,sp	2	3	00HC
0xF9	ld sp,hl	1	2	----
0xFA	ld a,[n16]	3	4	----
0xFB	ei	1	1	----
0xFC	-	-	-	----
0xFD	-	-	-	----
0xFE	cp n8	2	2	Z1HC
0xFF	rst 38h	1	4	----
0xCB00	rlc b	2	2	Z00C
0xCB01	rlc c	2	2	Z00C
0xCB02	rlc d	2	2	Z00C
0xCB03	rlc e	2	2	Z00C
0xCB04	rlc h	2	2	Z00C
0xCB05	rlc l	2	2	Z00C
0xCB06	rlc [hl]	2	4	Z00C
0xCB07	rlc a	2	2	Z00C
0xCB08	rrc b	2	2	Z00C
0xCB09	rrc c	2	2	Z00C
0xCB0A	rrc d	2	2	Z00C
0xCB0B	rrc e	2	2	Z00C
0xCB0C	rrc h	2	2	Z00C
0xCB0D	rrc l	2	2	Z00C
0xCB0E	rrc [hl]	2	4	Z00C
0xCB0F	rrc a	2	2	Z00C
0xCB10	rl b	2	2	Z00C
0xCB11	rl c	2	2	Z00C
0xCB12	rl d	2	2	Z00C
0xCB13	rl e	2	2	Z00C
0xCB14	rl h	2	2	Z00C
0xCB15	rl l	2	2	Z00C
0xCB16	rl [hl]	2	4	Z00C
0xCB17	rl a	2	2	Z00C
0xCB18	rr b	2	2	Z00C
0xCB19	rr c	2	2	Z00C
0xCB1A	rr d	2	2	Z00C
0xCB1B	rr e	2	2	Z00C
0xCB1C	rr h	2	2	Z00C
0xCB1D	rr l	2	2	Z00C
0xCB1E	rr [hl]	2	4	Z00C
0xCB1F	rr a	2	2	Z00C
0xCB20	sla b	2	2	Z00C
0xCB21	sla c	2	2	Z00C
0xCB22	sla d	2	2	Z00C
0xCB23	sla e	2	2	Z00C
0xCB24	sla h	2	2	Z00C
0xCB25	sla l	2	2	Z00C
0xCB26	sla [hl]	2	4	Z00C
0xCB27	sla a	2	2	Z00C
0xCB28	sra b	2	2	Z00C
0xCB29	sra c	2	2	Z00C
0xCB2A	sra d	2	2	Z00C
0xCB2B	sra e	2	2	Z00C
0xCB2C	sra h	2	2	Z00C
0xCB2D	sra l	2	2	Z00C
0xCB2E	sra [hl]	2	4	Z00C
0xCB2F	sra a	2	2	Z00C
0xCB30	swap b	2	2	Z000
0xCB31	swap c	2	2	Z000
0xCB32	swap d	2	2	Z000
0xCB33	swap e	2	2	Z000
0xCB34	swap h	2	2	Z000
0xCB35	swap l	2	2	Z000
0xCB36	swap [hl]	2	4	Z000
0xCB37	swap a	2	2	Z000
0xCB39	srl c	2	2	Z00C
0xCB39	srl c	2	2	Z00C
0xCB3B	srl e	2	2	Z00C
0xCB3B	srl e	2	2	Z00C
0xCB3D	srl l	2	2	Z00C
0xCB3D	srl l	2	2	Z00C
0xCB3F	srl a	2	2	Z00C
0xCB3F	srl a	2	2	Z00C
0xCB41	bit 0,c	2	2	Z01-
0xCB41	bit 0,c	2	2	Z01-
0xCB43	bit 0,e	2	2	Z01-
0xCB43	bit 0,e	2	2	Z01-
0xCB45	bit 0,l	2	2	Z01-
0xCB45	bit 0,l	2	2	Z01-
0xCB47	bit 0,a	2	2	Z01-
0xCB47	bit 0,a	2	2	Z01-
0xCB49	bit 1,c	2	2	Z01-
0xCB49	bit 1,c	2	2	Z01-
0xCB4B	bit 1,e	2	2	Z01-
0xCB4B	bit 1,e	2	2	Z01-
0xCB4D	bit 1,l	2	2	Z01-
0xCB4D	bit 1,l	2	2	Z01-
0xCB4F	bit 1,a	2	2	Z01-
0xCB4F	bit 1,a	2	2	Z01-
0xCB51	bit 2,c	2	2	Z01-
0xCB51	bit 2,c	2	2	Z01-
0xCB53	bit 2,e	2	2	Z01-
0xCB53	bit 2,e	2	2	Z01-
0xCB55	bit 2,l	2	2	Z01-
0xCB55	bit 2,l	2	2	Z01-
0xCB57	bit 2,a	2	2	Z01-
0xCB57	bit 2,a	2	2	Z01-
0xCB59	bit 3,c	2	2	Z01-
0xCB59	bit 3,c	2	2	Z01-
0xCB5B	bit 3,e	2	2	Z01-
0xCB5B	bit 3,e	2	2	Z01-
0xCB5D	bit 3,l	2	2	Z01-
0xCB5D	bit 3,l	2	2	Z01-
0xCB5F	bit 3,a	2	2	Z01-
0xCB5F	bit 3,a	2	2	Z01-
0xCB61	bit 4,c	2	2	Z01-
0xCB61	bit 4,c	2	2	Z01-
0xCB63	bit 4,e	2	2	Z01-
0xCB63	bit 4,e	2	2	Z01-
0xCB65	bit 4,l	2	2	Z01-
0xCB65	bit 4,l	2	2	Z01-
0xCB67	bit 4,a	2	2	Z01-
0xCB67	bit 4,a	2	2	Z01-
0xCB69	bit 5,c	2	2	Z01-
0xCB69	bit 5,c	2	2	Z01-
0xCB6B	bit 5,e	2	2	Z01-
0xCB6B	bit 5,e	2	2	Z01-
0xCB6D	bit 5,l	2	2	Z01-
0xCB6D	bit 5,l	2	2	Z01-
0xCB6F	bit 5,a	2	2	Z01-
0xCB6F	bit 5,a	2	2	Z01-
0xCB71	bit 6,c	2	2	Z01-
0xCB71	bit 6,c	2	2	Z01-
0xCB73	bit 6,e	2	2	Z01-
0xCB73	bit 6,e	2	2	Z01-
0xCB75	bit 6,l	2	2	Z01-
0xCB75	bit 6,l	2	2	Z01-
0xCB77	bit 6,a	2	2	Z01-
0xCB77	bit 6,a	2	2	Z01-
0xCB79	bit 7,c	2	2	Z01-
0xCB79	bit 7,c	2	2	Z01-
0xCB7A	bit 7,d	2	2	Z01-
0xCB7B	bit 7,e	2	2	Z01-
0xCB7B	bit 7,e	2	2	Z01-
0xCB7C	bit 7,h	2	2	Z01-
0xCB7D	bit 7,l	2	2	Z01-
0xCB7D	bit 7,l	2	2	Z01-
0xCB7E	bit 7,[hl]	2	3	Z01-
0xCB7F	bit 7,a	2	2	Z01-
0xCB7F	bit 7,a	2	2	Z01-
0xCB80	res 0,b	2	2	----
0xCB81	res 0,c	2	2	----
0xCB81	res 0,c	2	2	----
0xCB82	res 0,d	2	2	----
0xCB83	res 0,e	2	2	----
0xCB83	res 0,e	2	2	----
0xCB84	res 0,h	2	2	----
0xCB85	res 0,l	2	2	----
0xCB85	res 0,l	2	2	----
0xCB86	res 0,[hl]	2	4	----
0xCB87	res 0,a	2	2	----
0xCB87	res 0,a	2	2	----
0xCB88	res 1,b	2	2	----
0xCB89	res 1,c	2	2	----
0xCB89	res 1,c	2	2	----
0xCB8A	res 1,d	2	2	----
0xCB8B	res 1,e	2	2	----
0xCB8B	res 1,e	2	2	----
0xCB8C	res 1,h	2	2	----
0xCB8D	res 1,l	2	2	----
0xCB8D	res 1,l	2	2	----
0xCB8E	res 1,[hl]	2	4	----
0xCB8F	res 1,a	2	2	----
0xCB8F	res 1,a	2	2	----
0xCB90	res 2,b	2	2	----
0xCB91	res 2,c	2	2	----
0xCB91	res 2,c	2	2	----
0xCB92	res 2,d	2	2	----
0xCB93	res 2,e	2	2	----
0xCB93	res 2,e	2	2	----
0xCB94	res 2,h	2	2	----
0xCB95	res 2,l	2	2	----
0xCB95	res 2,l	2	2	----
0xCB96	res 2,[hl]	2	4	----
0xCB97	res 2,a	2	2	----
0xCB97	res 2,a	2	2	----
0xCB98	res 3,b	2	2	----
0xCB99	res 3,c	2	2	----
0xCB99	res 3,c	2	2	----
0xCB9A	res 3,d	2	2	----
0xCB9B	res 3,e	2	2	----
0xCB9B	res 3,e	2	2	----
0xCB9C	res 3,h	2	2	----
0xCB9D	res 3,l	2	2	----
0xCB9D	res 3,l	2	2	----
0xCB9E	res 3,[hl]	2	4	----
0xCB9F	res 3,a	2	2	----
0xCB9F	res 3,a	2	2	----
0xCBA0	res 4,b	2	2	----
0xCBA1	res 4,c	2	2	----
0xCBA1	res 4,c	2	2	----
0xCBA2	res 4,d	2	2	----
0xCBA3	res 4,e	2	2	----
0xCBA3	res 4,e	2	2	----
0xCBA4	res 4,h	2	2	----
0xCBA5	res 4,l	2	2	----
0xCBA5	res 4,l	2	2	----
0xCBA6	res 4,[hl]	2	4	----
0xCBA7	res 4,a	2	2	----
0xCBA7	res 4,a	2	2	----
0xCBA8	res 5,b	2	2	----
0xCBA9	res 5,c	2	2	----
0xCBA9	res 5,c	2	2	----
0xCBAA	res 5,d	2	2	----
0xCBAB	res 5,e	2	2	----
0xCBAB	res 5,e	2	2	----
0xCBAC	res 5,h	2	2	----
0xCBAD	res 5,l	2	2	----
0xCBAD	res 5,l	2	2	----
0xCBAE	res 5,[hl]	2	4	----
0xCBAF	res 5,a	2	2	----
0xCBAF	res 5,a	2	2	----
0xCBB0	res 6,b	2	2	----
0xCBB1	res 6,c	2	2	----
0xCBB1	res 6,c	2	2	----
0xCBB2	res 6,d	2	2	----
0xCBB3	res 6,e	2	2	----
0xCBB3	res 6,e	2	2	----
0xCBB4	res 6,h	2	2	----
0xCBB5	res 6,l	2	2	----
0xCBB5	res 6,l	2	2	----
0xCBB6	res 6,[hl]	2	4	----
0xCBB7	res 6,a	2	2	----
0xCBB7	res 6,a	2	2	----
0xCBB8	res 7,b	2	2	----
0xCBB9	res 7,c	2	2	----
0xCBB9	res 7,c	2	2	----
0xCBBA	res 7,d	2	2	----
0xCBBB	res 7,e	2	2	----
0xCBBB	res 7,e	2	2	----
0xCBBD	res 7,l	2	2	----
0xCBBF	res 7,a	2	2	----
0xCBC1	set 0,c	2	2	----
0xCBC3	set 0,e	2	2	----
0xCBC5	set 0,l	2	2	----
0xCBC7	set 0,a	2	2	----
0xCBC9	set 1,c	2	2	----
0xCBCB	set 1,e	2	2	----
0xCBCD	set 1,l	2	2	----
0xCBCF	set 1,a	2	2	----
0xCBD1	set 2,c	2	2	----
0xCBD3	set 2,e	2	2	----
0xCBD5	set 2,l	2	2	----
0xCBD7	set 2,a	2	2	----
0xCBD9	set 3,c	2	2	----
0xCBDB	set 3,e	2	2	----
0xCBDD	set 3,l	2	2	----
0xCBDF	set 3,a	2	2	----
0xCBE1	set 4,c	2	2	----
0xCBE3	set 4,e	2	2	----
0xCBE5	set 4,l	2	2	----
0xCBE7	set 4,a	2	2	----
0xCBE9	set 5,c	2	2	----
0xCBEB	set 5,e	2	2	----
0xCBED	set 5,l	2	2	----
0xCBEF	set 5,a	2	2	----
0xCBF1	set 6,c	2	2	----
0xCBF3	set 6,e	2	2	----
0xCBF5	set 6,l	2	2	----
0xCBF7	set 6,a	2	2	----
0xCBF9	set 7,c	2	2	----
0xCBFB	set 7,e	2	2	----
0xCBFD	set 7,l	2	2	----
0xCBFE	set 7,[hl]	2	4	----
0xCBFF	set 7,a	2	2	----"""

#For now, unused. However, if time may try to implement so that 
#hold works better
class KeyTracker():
    key = ''
    last_press_time = 0
    last_release_time = 0

    def track(self, key):
        self.key = key

    def is_pressed(self):
        return time.time() - self.last_press_time < .1

    def report_key_press(self, event):
        if event.keysym == self.key:
            if not self.is_pressed():
                on_key_press(event)
            self.last_press_time = time.time()

    def report_key_release(self, event):
        if event.keysym == self.key:
            timer = threading.Timer(.1, self.report_key_release_callback, args=[event])
            timer.start()

    def report_key_release_callback(self, event):
        if not self.is_pressed():
            on_key_release(event)
        self.last_release_time = time.time()

class Renderer:
    def __init__(self, master, hamulator, unimplemented = True):
        self._num_presses = 0
        self.master = master
        self._hamulator = hamulator 
        self._unimplemented = unimplemented
         
        self.create()

    def end(self):
        self._ending = True
        self._emuthread.join()

    def key_press(self, e):
        self._num_presses += 1
        #print(("{0}. Yep " + e.keysym) .format(self._num_presses), flush=True)
        if e.keysym in JOYPAD_BUTTON_MAP:
            self._joypad.add(JOYPAD_BUTTON_MAP[e.keysym])
            #print(self._joypad)

    def key_release(self, e):
        #print("{0}. Nope".format(self._num_presses), flush=True)

        if e.keysym in JOYPAD_BUTTON_MAP:
            self._joypad.remove(JOYPAD_BUTTON_MAP[e.keysym])
            #print(self._joypad)

    def init_joypad(self):
        self._joypad = set()
        #self._joypad_byte = 0b11111111

        self._hamulator._mem[rP1] = P1F_GET_NONE

        #self._key_a = KeyTracker()
        #self._key_a.track('b')

        #self._key_b = KeyTracker()
        #self._key_b.track('s')

        self.master.bind('<KeyPress>', lambda e: renderer.key_press(e))
        self.master.bind('<KeyRelease>', lambda e: renderer.key_release(e))
        pass

    def write_joypad_poll_result(self):
        byte = self._hamulator._mem[rP1]
        
        if byte   & P1F_GET_DPAD == P1F_GET_DPAD and \
            self._instr_count - self._instr_last_dpad > 2:

            byte |= 0x0F
            #print("RIGHT in joypad? {}".format("RIGHT" in self._joypad))
            byte &= ~JOYPAD_BUTTON_TO_BITS["UP"]    if "UP"    in self._joypad else 0xFF
            byte &= ~JOYPAD_BUTTON_TO_BITS["DOWN"]  if "DOWN"  in self._joypad else 0xFF
            byte &= ~JOYPAD_BUTTON_TO_BITS["LEFT"]  if "LEFT"  in self._joypad else 0xFF
            byte &= ~JOYPAD_BUTTON_TO_BITS["RIGHT"] if "RIGHT" in self._joypad else 0xFF
            self._instr_last_dpad = self._instr_count
        elif byte & P1F_GET_BTN  == P1F_GET_BTN and \
            self._instr_count - self._instr_last_btn > 6:
            byte |= 0x0F
            byte &= ~JOYPAD_BUTTON_TO_BITS["START"]  if "START"  in self._joypad else 0xFF
            byte &= ~JOYPAD_BUTTON_TO_BITS["SELECT"] if "SELECT" in self._joypad else 0xFF
            byte &= ~JOYPAD_BUTTON_TO_BITS["A"]      if "A"      in self._joypad else 0xFF
            byte &= ~JOYPAD_BUTTON_TO_BITS["B"]      if "B"      in self._joypad else 0xFF
            self._instr_last_btn = self._instr_count

        self._hamulator._mem[rP1] = byte
        #if self._verbose:
        #if byte & P1F_GET_NONE != P1F_GET_NONE:
        #    print("Wrote joypad poll result: {0:02X}".format(byte), flush=True)

    def init(self):
        self._start = time.monotonic()

        self.init_joypad()
        self._instr_count = 0
        self._instr_last_dpad = 0
        self._instr_last_btn  = 0

        self._ending = False
        self._verbose = False
        #self._verbose = True

        # background stuff
        self._bg_x = 0
        self._bg_y = 0
        self._pixmap_changed = True

        if self._verbose:
            print("initting", flush=True)
        #vblank stuff
        self._vblank_lock = threading.Lock()
        self._hamulator._mem[rLCDC] = LCDCF_ON

        self.init_screen()

        # register halt
        self._hamulator._isa[0x76] = lambda: self.halt()

        self._all_ops = {}

        # register unsupported instructions
        ops = OPCODES.split("\n")
        for line in ops:
            args = line.strip().split("\t")
            opcode = int(args[0], 16)
            opcode_bytes = 1 if opcode < 256 else 2
            op_string = args[1]
            operand_bytes = 0 if args[2] == '-' else int(args[2]) - opcode_bytes

            self._all_ops[opcode] = (op_string, operand_bytes)

        self.set_vblank(True)
        if self._verbose:
            print(f"{self.time():.2f} done initting", flush=True)

    def run(self) -> None:
        while not self._ending:
            opcode = self._hamulator.fetch()
            if self._unimplemented and opcode not in self._hamulator._isa:
                self._hamulator._isa[opcode] = lambda: self.print_and_read_operands(self._all_ops[opcode])

            instr = self._hamulator.decode(opcode)
            #(op_string, operand_bytes) = self._instr[opcode]
            #self.fetch_operands(operand_bytes)
            #print(op_string)
            instr()
            self._instr_count += 1
            self.write_joypad_poll_result()

    def time(self):
        return time.monotonic() - self._start

    def halt(self):
        if self._hamulator._verbose:
            print("halt", end="", flush=True)

        if (self._hamulator._mem[rIE] & IEF_VBLANK) != IEF_VBLANK or \
            (self._hamulator._mem[rLCDC] & LCDCF_ON) == LCDCF_OFF or \
            not self._hamulator._interrupts_enabled:
            if self._hamulator._verbose:
                print("    ; skipped (no interrupts or LCD OFF)", end="", flush=True)

            return

        while self._in_vblank and not self._ending and (self._hamulator._mem[rLCDC] & LCDCF_ON) != 0:
            #print("waiting to be done with current vblank", flush=True)
            pass

        while not self._in_vblank and not self._ending and (self._hamulator._mem[rLCDC] & LCDCF_ON) != 0:
            #print("waiting for vblank", flush=True)
            pass

        if self._hamulator._verbose:
            print("    ; completed", flush=True)

    def start_execution(self):
        self._emuthread = threading.Thread(target = self.run)
        self._emuthread.start()

        self.master.after(1, lambda: self.my_update())
     
    def create(self):
        # Creates an object of class canvas
        # with the help of this we can create different shapes
        self.canvas = Canvas(self.master)

        self.init()
        self.canvas.pack(fill = BOTH, expand = 0)
        self.master.after(1, lambda: self.start_execution())

    def init_screen(self):
        self._pixmap      = [[0 for i in range(256)] for j in range(256)]
        self._prev_pixmap = [[0 for i in range(256)] for j in range(256)]
        self._photo = PhotoImage(width=512, height=512)

        #self._rect_ids = [[0 for i in range(160)] for j in range(144)]

        #for j in range(0,100,5):
        #for j in range(0,720,5):
        #    self._hamulator._mem[rLY] = j//5
        #    for i in range(0, 800, 5):
        #        color = self._pixmap[j//5][i//5] #pixmap[(row_start + j//5) % SCRN_Y][(col_start + i//5) % SCRN_X]
        #        fill_color = "#fff"
        #        if color == 3:
        #            fill_color = "#000"
        #        if color == 2:
        #            fill_color = "#555"
        #        if color == 1:
        #            fill_color = "#aaa"

        #        self._photo.put("{" + fill_color +"}", (j//5, i//5))
        #        #self._rect_ids[j//5][i//5] = self.canvas.create_rectangle(i, j, i+5, j+5, outline=fill_color, fill=fill_color)

        self.update_pixmap(self._hamulator)

        #for j in range(0,100,5):
        for j in range(0,512):
            self._hamulator._mem[rLY] = j//5
            for i in range(0,512):
                color = self._pixmap[j % 256][i % 256] #pixmap[(row_start + j//5) % SCRN_Y][(col_start + i//5) % SCRN_X]
                fill_color = "#fff"
                if color == 3:
                    fill_color = "#000"
                if color == 2:
                    fill_color = "#555"
                if color == 1:
                    fill_color = "#aaa"

                self._photo.put("{" + fill_color +"}", (i, j))
                #self._rect_ids[j//5][i//5] = self.canvas.create_rectangle(i, j, i+5, j+5, outline=fill_color, fill=fill_color)

        self._photo_id = self.canvas.create_image(0, 0, image = self._photo, anchor=NW)

        self.canvas.pack(fill = BOTH, expand = 1)

        #simulate vblank
        self._hamulator._mem[rLY] = SCRN_Y
        #time.sleep(0.001)

    def draw_bg(self):
        #only draw if in VBlank and LCD is on
        assert not self._in_vblank

        if self._verbose:
            print("[rLCDC]={0:02X}".format(self._hamulator._mem[rLCDC]), flush=True)
        if (self._hamulator._mem[rLCDC] & LCDCF_ON) == 0:
            return

        self._hamulator._mem[rLY] = 0
        if self._verbose:
            print("[{0:03f}] Drawing screen".format(self.time()), flush=True)

        self.update_pixmap(self._hamulator)

        reload_photo = False

        if self._pixmap_changed: #self._pixmap != self._prev_pixmap:
            if self._verbose:
                print("updating photo", flush=True)
            reload_photo = True
            self.canvas.delete("all")
            self._photo = PhotoImage(width=512, height=512)

            self._hamulator._mem[rLY] = 0

            colors = ["#fff" for i in range(0, 512)]
            color_string = ""
            for j in range(0,512):
                for i in range(0, 512):
                    color = self._pixmap[j % 256][i%256]
                    fill_color = "#fff"
                    if color == 3:
                        fill_color = "#000"
                    if color == 2:
                        fill_color = "#555"
                    if color == 1:
                        fill_color = "#aaa"

                    colors[i] = fill_color
                    #self._photo.put("{" + fill_color +"}", (i, j))
                    #self._rect_ids[j//5][i//5] = self.canvas.create_rectangle(i, j, i+5, j+5, outline=fill_color, fill=fill_color)

                if j == 0:
                    color_string = "{" + " ".join(colors) + "}"
                else:
                    color_string += " {" + " ".join(colors) + "}"
                #print("color=" + fill_color + ", ", (j, i), flush=True)

            self._photo.put(color_string)
            #for j in range(0,720,5):
            #for j in range(0,100,5):
            #    self._hamulator._mem[rLY] = j//5
            #    for i in range(0, 800, 5):
            #        color = self._pixmap[(row_start + j//5) % 256][(col_start + i//5) % 256]
            #        fill_color = "#fff"
            #        if color == 3:
            #            fill_color = "#000"
            #        if color == 2:
            #            fill_color = "#555"
            #        if color == 1:
            #            fill_color = "#aaa"
               
            #    #rect_id = self._rect_ids[j//5][i//5]
            #    #self.canvas.itemconfig(rect_id, outline=fill_color, fill=fill_color)
            #    self._photo.put("{" + fill_color +"}", (j//5, i//5))

            self._photo_id = self.canvas.create_image(0, 0, image = self._photo, anchor=NW)
            self.canvas.pack(fill = BOTH, expand = 1)
            if self._verbose:
                print("done updating photo", flush=True)

            self._bg_x = 0
            self._bg_y = 0

        row_start = self._hamulator._mem[rSCY]
        col_start = self._hamulator._mem[rSCX]
        if self._verbose:
            print("screen offset = x,y=", col_start, row_start, flush=True)

        # this is the delta for
        delta_x = self._bg_x - col_start
        delta_y = self._bg_y - row_start

        if self._bg_x <= -256:
            delta_x += 256
        elif self._bg_x >= 256:
            delta_x -= 256

        if self._bg_y <= -256:
            delta_y += 256
        elif self._bg_y >= 256:
            delta_y -= 256

        self.canvas.move(self._photo_id, delta_x, delta_y)

        #print(f"(before) x={self._bg_x},y={self._bg_y}", flush=True)

        self._bg_x  = col_start
        self._bg_y  = row_start

        #print(f"(after) x={self._bg_x},y={self._bg_y}", flush=True)

        self.canvas.update_idletasks()

        if self._verbose:
            print("[{0:03f}] Drawn".format(self.time()), flush=True)

        #simulate vblank
        self._hamulator._mem[rLY] = SCRN_Y
        #time.sleep(0.001)

    def set_vblank(self, in_vblank):
        if self._verbose:
            print("aquiring...", flush=True)
        self._vblank_lock.acquire()
        
        if in_vblank:
            self._hamulator._mem[rLY] = SCRN_Y
            self._in_vblank = True
            if self._verbose:
                print("[{0:03f}] In     VBlank...".format(self.time()), flush=True)
        else:
            if self._verbose:
                print("[{0:03f}] Out of VBlank...".format(self.time()), flush=True)
            self._in_vblank = False
            self._hamulator._mem[rLY] = 0
            self.draw_bg()

        if self._verbose:
            print("releasing...", flush=True)
        self._vblank_lock.release()

    def my_update(self):
        if self._verbose:
            print("update", flush=True)
        #LCD on
        if (self._hamulator._mem[rLCDC] & LCDCF_ON) != 0:
            self.set_vblank(False)

        #draw screen
        start = time.monotonic()
        self.set_vblank(True)
        elapsed = time.monotonic() - start
        elapsed = int(elapsed * 1000)
        master.after(1, lambda: self.my_update())

    def update_pixmap(self, hamulator):

        # for testing, temporarily write into VRAM.
        #vram_addr = 0x8000
        #for i in range(0x6400, 0x8000):
        #    hamulator._mem[vram_addr] = hamulator._mem[i]
        #    vram_addr += 1

        self._pixmap_changed = False

        lcd_flags = hamulator._mem[rLCDC]

        #convert to signed number if $8800 mode
        base = _VRAM9000 if lcd_flags & LCDCF_BG8800 == LCDCF_BG8800 else _VRAM8000
        tilemap_addr = START_TILEMAP1 if lcd_flags & LCDCF_BG9800 == LCDCF_BG9800 else LCDCF_BG9C00

        bg_palette = hamulator._mem[rBGP]

        palette_map = {0: bg_palette & 0x03, 1: (bg_palette >> 2) & 0x03, 2: (bg_palette >> 4) & 0x03, 3: (bg_palette >> 6) & 0x03}

        # read first tile index in tilemap
        tile_index = hamulator._mem[tilemap_addr]
        #print("tile_index =", tile_index)

        tile = [[0 for i in range(8)] for i in range(8)]

        for tile_row in range(0,32):
            for tile_col in range(0,32):

                tile_index = hamulator._mem[tilemap_addr]

                # convert to signed
                if base == _VRAM9000 and tile_index > 127:
                    tile_index = tile_index - 256

                #print("reading tilemap address 0x{0:04X}".format(tilemap_addr), flush=True)
                #print("with base 0x{0:04X}".format(base), flush=True)
                #print("reading tile index {0} at address 0x{1:04X}".format(tile_index, base + 16 * tile_index), flush=True)

                tile_bytes = hamulator._mem[base + 16 * tile_index : base + 16 * (tile_index + 1)]
                #for i in range(len(tile_bytes)):
                #    print("{0:02X}".format(tile_bytes[i]), end = " ")
                #print()

                tilemap_addr += 1

                byte_index = 0
                # get tile
                for i in range(0,8):
                    byte1 = tile_bytes[byte_index]
                    byte2 = tile_bytes[byte_index + 1]
                    #print("byte1={0:08b}".format(byte1))
                    #print("byte2={0:08b}".format(byte2))
                    power = 1
                    for j in range(7,-1, -1):
                        bit1 = byte1 & power
                        bit2 = byte2 & power
                        tile[i][j] = 2*bit2 + bit1
                        byte1 >>= 1
                        byte2 >>= 1

                    #print("unzipped=[ ", end="")
                    #for k in range(0,8):
                    #    print("{0:02b}".format(tile[i][k]), end=" ")

                    #print("]")

                    byte_index += 2
                # now copy tile into screen
                screen_row = 8 * tile_row
                screen_col = 8 * tile_col
                for i in range(0,8):
                    for j in range(0,8):
                        if self._prev_pixmap[screen_row + i][screen_col + j] != self._pixmap[screen_row + i][screen_col + j]:
                            self._pixmap_changed = True
                        self._prev_pixmap[screen_row + i][screen_col + j] = self._pixmap[screen_row + i][screen_col + j]
                        self._pixmap[screen_row + i][screen_col + j] = palette_map[tile[i][j]]

        #if self._verbose:
        #    for i in range(0,256):
        #        for j in range(0,256):
        #            print(self._pixmap[i][j], end = "")
        #       print(flush=True)

    def print_and_read_operands(self, op_pair):
        op_string = op_pair[0]
        operand_bytes = op_pair[1]
        self._hamulator.fetch_operands(operand_bytes)
        if self._hamulator._verbose:
            print(op_string + " ; unsupported")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hamulator, a GB Emulator.')
    parser.add_argument('-v', help='enable verbose output', action="store_true")
    parser.add_argument('-u', help='print unimplemented instructions', action="store_true")
    parser.add_argument('rom_file', default="game.gb", help='rom file')
    args = parser.parse_args()

    verbose = args.v
    unimplemented = args.u
    file_name = args.rom_file
    rom = emulator.read_rom(file_name, verbose)
    #if verbose:
    #    emulator.print_rom(rom)

    hamulator = emulator.Emulator(rom, verbose)

    # object of class Tk, responsible for creating
    # a tkinter toplevel window
    master = Tk()
    renderer = Renderer(master, hamulator, unimplemented)

    # Sets the title to hamulator
    master.title("Hamulator")

    # Sets the geometry and position
    # of window on the screen
    master.geometry("160x144")

    # hamulator._isa[0x76] = lambda: renderer.update()

    # Infinite loop breaks only by interrupt
    mainloop()

    renderer.end()