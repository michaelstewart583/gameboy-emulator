
.PHONY: all

all: function_add.gb

function_add.gb: function_add.asm
	rgbasm -o main.o function_add.asm
	rgblink -o main.gb main.o
	rgbfix -v -p 0xFF main.gb