
.PHONY: all

all: jp_nz_test.gb

jp_nz_test.gb: jp_nz_test.asm
	rgbasm -o main.o jp_nz_test.asm
	rgblink -o main.gb main.o
	rgbfix -v -p 0xFF main.gb