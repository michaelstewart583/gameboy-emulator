import typing

class Emulator:
    def __init__(self, rom: list[int], verbose: bool = False) -> None:
        self.init_mem(rom)
        self.init_regs()
        self.init_isa()
        self._interrupts_enabled = True
        self._verbose = verbose

    def init_mem(self, rom: list[int]) -> None:
        assert len(rom) <= 0x8000
        self._mem = rom + [0 for i in range(0, 0x10000 - len(rom))]

    def init_regs(self):
        self._regs = {}
        self._regs["a"] = 0
        self._regs["f"] = 0

        self._regs["b"] = 0
        self._regs["c"] = 0

        self._regs["d"] = 0
        self._regs["e"] = 0

        self._regs["h"] = 0
        self._regs["l"] = 0

        self._regs["sp"] = 0xFFFE
        self._regs["pc"] = 0x0100

    def init_isa(self):
        self._isa = {}
        self._isa[0xF3] = self.disable_interrupts
        self._isa[0xFB] = self.enable_interrupts

        self._isa[0xC3] = self.jump
        self._isa[0xC2] = self.jp_nz_n16
        self._isa[0xCA] = self.jp_z_n16
        self._isa[0xD2] = self.jp_nc_n16
        self._isa[0xDA] = self.jp_c_n16

        self._isa[0x3E] = lambda: self.ld_r8_n8("a")
        self._isa[0x06] = lambda: self.ld_r8_n8("b")
        self._isa[0x0E] = lambda: self.ld_r8_n8("c")
        self._isa[0x16] = lambda: self.ld_r8_n8("d")
        self._isa[0x1E] = lambda: self.ld_r8_n8("e")
        self._isa[0x26] = lambda: self.ld_r8_n8("h")
        self._isa[0x2E] = lambda: self.ld_r8_n8("l")
        
        self._isa[0xEA] = self.ld_mem_n16_a
        self._isa[0xFA] = self.ld_a_mem_n16
        
        self._isa[0X04] = lambda: self.inc_8_bit("b")
        self._isa[0X0C] = lambda: self.inc_8_bit("c")
        self._isa[0X14] = lambda: self.inc_8_bit("d")
        self._isa[0X1C] = lambda: self.inc_8_bit("e")
        self._isa[0X24] = lambda: self.inc_8_bit("h")
        self._isa[0X2C] = lambda: self.inc_8_bit("l")
        self._isa[0x3C] = lambda: self.inc_8_bit("a")

        self._isa[0X05] = lambda: self.dec_8_bit("b")
        self._isa[0X0D] = lambda: self.dec_8_bit("c")
        self._isa[0X15] = lambda: self.dec_8_bit("d")
        self._isa[0X1D] = lambda: self.dec_8_bit("e")
        self._isa[0X25] = lambda: self.dec_8_bit("h")
        self._isa[0X2D] = lambda: self.dec_8_bit("l")
        self._isa[0X3D] = lambda: self.dec_8_bit("a")

        self._isa[0XFE] = self.cp_n8
        self._isa[0XB8] = lambda: self.cp_r8("b")
        self._isa[0XB9] = lambda: self.cp_r8("c")
        self._isa[0XBA] = lambda: self.cp_r8("d")
        self._isa[0XBB] = lambda: self.cp_r8("e")
        self._isa[0XBC] = lambda: self.cp_r8("h")
        self._isa[0XBD] = lambda: self.cp_r8("l")
        self._isa[0XBD] = lambda: self.cp_r8("a")

    def run(self) -> None:
        while True:
            opcode = self.fetch()
            instr = self.decode(opcode)
            instr()

    def decode(self, opcode: int):
        if opcode not in self._isa:
            raise Exception("instruction {0:02X} not supported".format(opcode))
            return None
        return self._isa[opcode]

    def fetch(self) -> int:
        pc = self._regs["pc"]

        if self._verbose:
            print("{0:04X}".format(pc), end="\t")

        opcode = self._mem[pc]
        pc += 1

        if self._verbose:
            print("{0:02X}".format(opcode), end=" ")

        # is a 2-byte opcode
        if opcode == 0xCB:
            opcode2 = self._mem[pc]
            pc += 1
            opcode = (opcode << 8) | opcode2
            if self._verbose:
                print("{0:02X}".format(opcode2), end=" ")

        self._regs["pc"] = pc

        return opcode

    def fetch_operands(self, bytes: int = 0) -> list[int]:
        pc = self._regs["pc"]
        operands = self._mem[pc:pc + bytes]
        self._regs["pc"] = self._regs["pc"] + bytes
        if self._verbose:
            for i in operands:
                print("{0:02X}".format(i), end=" ")
        return operands

    def to_little(self, operands: list[int]) -> int:
        assert len(operands) == 2
        return operands[1] << 8 | operands[0]
    
    def set_z(self) -> None:
        self._regs["f"] = self._regs["f"] | 0B10000000

    def set_c(self) -> None:
        self._regs["f"] = self._regs["f"] | 0B00010000

    def unset_z(self) -> None:
        self._regs["f"] = self._regs["f"] & 0B01111111

    def unset_c(self) -> None:
        self._regs["f"] = self._regs["f"] & 0B11101111

    def z_is_set(self) -> bool:
        return (self._regs["f"] & 0B10000000) != 0
    
    def c_is_set(self) -> bool:
        return (self._regs["f"] & 0B00010000) != 0

    def disable_interrupts(self):
        instr = self.fetch_operands(0)
        if self._verbose:
            print("di")
        self._interrupts_enabled = False

    def enable_interrupts(self):
        instr = self.fetch_operands(0)
        if self._verbose:
            print("ei")
        self._interrupts_enabled = True

    def jump(self) -> None:
        instr = self.fetch_operands(2)
        if self._verbose:
            print("jp", end=" ")
        new_address = self.to_little(instr)
        if self._verbose:
            print("{0:04X}".format(new_address))
        self._regs["pc"] = new_address

    def ld_r8_n8(self, reg: str) -> None:
        instr = self.fetch_operands(1)
        if self._verbose:
            print(f"ld {reg}, n8")
        self._regs[reg] = instr[0]

    def ld_mem_n16_a(self) -> None:
        instr = self.fetch_operands(2)
        if self._verbose:
            print("ld [n16], a")
        address = self.to_little(instr)
        self._mem[address] = self._regs["a"]

    def ld_a_mem_n16(self) -> None:
        instr = self.fetch_operands(2)
        if self._verbose:
            print("ld a, [n16]")
        address = self.to_little(instr)
        self._regs["a"] = self._mem[address]

    def inc_8_bit(self, reg: str) -> None:
        if self._verbose:
            print(f"inc {reg}")
        self._regs[reg] += 1
        if self._regs[reg] == 256:
            self._regs[reg] = 0
            self.set_c()
            self.set_z()
        else:
            self.unset_c()
            self.unset_z()    

    def dec_8_bit(self, reg: str) -> None:
        if self._verbose:
            print(f"dec {reg}")
        self._regs[reg] -= 1
        if self._regs[reg] == -1:
            self._regs[reg] = 255
            self.set_c()
            self.unset_z()
        elif self._regs[reg] == 0:
            self.set_z()
            self.unset_c()   
        else:
            self.unset_c()
            self.unset_z()

    def cp_n8(self) -> None:
        instr = self.fetch_operands(1)
        if self._verbose:
            print("cp n8")
        if instr[0] == self._regs["a"]:
            self.set_z()
            self.unset_c()
        elif instr[0] > self._regs["a"]:
            self.unset_z()
            self.set_c()
        else:
            self.unset_c()
            self.unset_z()

    def cp_r8(self, reg: str):
        if self._verbose:
            print("cp", reg)
        if self._regs["a"] == self._regs[reg]:
            self.set_z()
            self.unset_c()
        elif self._regs["a"] > self._regs[reg]:
            self.unset_z()
            self.unset_c()
        else:
            self.unset_z()
            self.set_c()

    def jp_nz_n16(self) -> None:
        if (self._verbose):
            print("jp nz, n16")
        if (not self.z_is_set()):
            self.jump()

    def jp_z_n16(self) -> None:
        if (self._verbose):
            print("jp z, n16")
        if (self.z_is_set()):
            self.jump()

    def jp_c_n16(self) -> None:
        if (self._verbose):
            print("jp c, n16")
        if (self.c_is_set()):
            self.jump()

    def jp_nc_n16(self) -> None:
        if (self._verbose):
            print("jp nc, n16")
        if (not self.c_is_set()):
            self.jump()
        

def read_rom(file_name: str, verbose: bool = False) -> list[int]:
    rom = []
    with open(file_name, "rb") as f:
        rom = list(f.read())
        if verbose:
            print("read:", len(rom), "bytes")
    return rom

def print_rom(rom: list[int], start: int = 0, end: int = 0x8000) -> None:
    for address in range(start, end, 0x10):
        print("{0:04X}".format(address), end="\t")
        for i in range(0,16):
            print("{0:02X}".format(rom[address + i]), end=" ")
        print()

if __name__ == "__main__":
    verbose = True
    rom = read_rom("game.gb", verbose)
    if verbose:
        print_rom(rom)

    emulator = Emulator(rom, verbose)
    emulator.run()