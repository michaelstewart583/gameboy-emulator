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

        self._isa[0x01] = lambda: self.ld_r16_n16("bc")
        self._isa[0x11] = lambda: self.ld_r16_n16("de")
        self._isa[0x21] = lambda: self.ld_r16_n16("hl")

        self._isa[0x02] = lambda: self.ld_mem_r16_r8("bc", "a")
        self._isa[0x0A] = lambda: self.ld_r8_mem_r16("a", "bc")
        self._isa[0x12] = lambda: self.ld_mem_r16_r8("de", "a")
        self._isa[0x1A] = lambda: self.ld_r8_mem_r16("a", "de")
        self._isa[0x22] = lambda: self.ld_mem_r16_r8("hl", "a")
        self._isa[0x2A] = lambda: self.ld_r8_mem_r16("a", "hl")

        self._isa[0x06] = lambda: self.ld_r8_n8("b")
        self._isa[0x0E] = lambda: self.ld_r8_n8("c")
        self._isa[0x16] = lambda: self.ld_r8_n8("d")
        self._isa[0x1E] = lambda: self.ld_r8_n8("e")
        self._isa[0x26] = lambda: self.ld_r8_n8("h")
        self._isa[0x2E] = lambda: self.ld_r8_n8("l")
        self._isa[0x3E] = lambda: self.ld_r8_n8("a")

        self._isa[0x40] = lambda: self.ld_r8_r8("b", "b")
        self._isa[0x41] = lambda: self.ld_r8_r8("b", "c")
        self._isa[0x42] = lambda: self.ld_r8_r8("b", "d")
        self._isa[0x43] = lambda: self.ld_r8_r8("b", "e") 
        self._isa[0x44] = lambda: self.ld_r8_r8("b", "h") 
        self._isa[0x45] = lambda: self.ld_r8_r8("b", "l") 
        self._isa[0x46] = lambda: self.ld_r8_mem_r16("b", "hl") 
        self._isa[0x47] = lambda: self.ld_r8_r8("b", "a")         
        
        self._isa[0x48] = lambda: self.ld_r8_r8("c", "b") 
        self._isa[0x49] = lambda: self.ld_r8_r8("c", "c") 
        self._isa[0x4A] = lambda: self.ld_r8_r8("c", "d") 
        self._isa[0x4B] = lambda: self.ld_r8_r8("c", "e")
        self._isa[0x4C] = lambda: self.ld_r8_r8("c", "h") 
        self._isa[0x4D] = lambda: self.ld_r8_r8("c", "l") 
        self._isa[0x4E] = lambda: self.ld_r8_mem_r16("c", "hl") 
        self._isa[0x4F] = lambda: self.ld_r8_r8("c", "a") 

        self._isa[0x50] = lambda: self.ld_r8_r8("d", "b") 
        self._isa[0x51] = lambda: self.ld_r8_r8("d", "c") 
        self._isa[0x52] = lambda: self.ld_r8_r8("d", "d") 
        self._isa[0x53] = lambda: self.ld_r8_r8("d", "e")
        self._isa[0x54] = lambda: self.ld_r8_r8("d", "h") 
        self._isa[0x55] = lambda: self.ld_r8_r8("d", "l")
        self._isa[0x56] = lambda: self.ld_r8_mem_r16("d", "hl") 
        self._isa[0x57] = lambda: self.ld_r8_r8("d", "a")          

        self._isa[0x58] = lambda: self.ld_r8_r8("e", "b") 
        self._isa[0x59] = lambda: self.ld_r8_r8("e", "c") 
        self._isa[0x5A] = lambda: self.ld_r8_r8("e", "d") 
        self._isa[0x5B] = lambda: self.ld_r8_r8("e", "e")
        self._isa[0x5C] = lambda: self.ld_r8_r8("e", "h") 
        self._isa[0x5D] = lambda: self.ld_r8_r8("e", "l") 
        self._isa[0x5E] = lambda: self.ld_r8_mem_r16("e", "hl") 
        self._isa[0x5F] = lambda: self.ld_r8_r8("e", "a") 

        self._isa[0x60] = lambda: self.ld_r8_r8("h", "b") 
        self._isa[0x61] = lambda: self.ld_r8_r8("h", "c") 
        self._isa[0x62] = lambda: self.ld_r8_r8("h", "d") 
        self._isa[0x63] = lambda: self.ld_r8_r8("h", "e")
        self._isa[0x64] = lambda: self.ld_r8_r8("h", "h") 
        self._isa[0x65] = lambda: self.ld_r8_r8("h", "l") 
        self._isa[0x66] = lambda: self.ld_r8_mem_r16("h", "hl") 
        self._isa[0x67] = lambda: self.ld_r8_r8("h", "a") 

        self._isa[0x68] = lambda: self.ld_r8_r8("l", "b") 
        self._isa[0x69] = lambda: self.ld_r8_r8("l", "c") 
        self._isa[0x6A] = lambda: self.ld_r8_r8("l", "d") 
        self._isa[0x6B] = lambda: self.ld_r8_r8("l", "e")
        self._isa[0x6C] = lambda: self.ld_r8_r8("l", "h") 
        self._isa[0x6D] = lambda: self.ld_r8_r8("l", "l")
        self._isa[0x6E] = lambda: self.ld_r8_mem_r16("l", "hl")  
        self._isa[0x6F] = lambda: self.ld_r8_r8("l", "a")
    
        self._isa[0x70] = lambda: self.ld_mem_r16_r8("hl", "b")  
        self._isa[0x71] = lambda: self.ld_mem_r16_r8("hl", "c")  
        self._isa[0x72] = lambda: self.ld_mem_r16_r8("hl", "d")  
        self._isa[0x73] = lambda: self.ld_mem_r16_r8("hl", "e")  
        self._isa[0x74] = lambda: self.ld_mem_r16_r8("hl", "h")  
        self._isa[0x75] = lambda: self.ld_mem_r16_r8("hl", "l")  
        self._isa[0x77] = lambda: self.ld_mem_r16_r8("hl", "a")  
 
        self._isa[0x78] = lambda: self.ld_r8_r8("a", "b") 
        self._isa[0x79] = lambda: self.ld_r8_r8("a", "c") 
        self._isa[0x7A] = lambda: self.ld_r8_r8("a", "d") 
        self._isa[0x7B] = lambda: self.ld_r8_r8("a", "e")
        self._isa[0x7C] = lambda: self.ld_r8_r8("a", "h") 
        self._isa[0x7D] = lambda: self.ld_r8_r8("a", "l") 
        self._isa[0x7E] = lambda: self.ld_r8_mem_r16("a", "hl") 
        self._isa[0x7F] = lambda: self.ld_r8_r8("a", "a") 
        
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

        self._isa[0X87] = lambda: self.add_a_r8("a")
        self._isa[0X80] = lambda: self.add_a_r8("b")
        self._isa[0X81] = lambda: self.add_a_r8("c")
        self._isa[0X82] = lambda: self.add_a_r8("d")
        self._isa[0X83] = lambda: self.add_a_r8("e")
        self._isa[0X84] = lambda: self.add_a_r8("h")
        self._isa[0X85] = lambda: self.add_a_r8("l")
        self._isa[0X86] = self.add_a_mem_hl
        self._isa[0XC6] = self.add_a_n8

        self._isa[0X97] = lambda: self.sub_a_r8("a")
        self._isa[0X90] = lambda: self.sub_a_r8("b")
        self._isa[0X91] = lambda: self.sub_a_r8("c")
        self._isa[0X92] = lambda: self.sub_a_r8("d")
        self._isa[0X93] = lambda: self.sub_a_r8("e")
        self._isa[0X94] = lambda: self.sub_a_r8("h")
        self._isa[0X95] = lambda: self.sub_a_r8("l")
        self._isa[0X96] = self.sub_a_mem_hl
        self._isa[0XD4] = self.sub_a_n8

        self._isa[0XC5] = lambda: self.push_r16("bc")
        self._isa[0XD5] = lambda: self.push_r16("de")
        self._isa[0XE5] = lambda: self.push_r16("hl")

        self._isa[0XC1] = lambda: self.pop_r16("bc")
        self._isa[0XD1] = lambda: self.pop_r16("de")
        self._isa[0XE1] = lambda: self.pop_r16("hl")
        
        self._isa[0XCD] = self.call
        self._isa[0XC9] = self.ret

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
    
    def get_16_bit_reg_val(self, reg:str) -> int:
        return self._isa[reg[0]] << 8 | self._isa[reg[1]]
    
    def convert_16_val_to_two_8_bit_vals(self, val: int) -> tuple[int, int]:
        val_0 = val >> 8
        val_1 = val & 0XFF
        return val_0, val_1

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

    def ld_r8_r8(self, reg_1: str, reg_2: str) -> None:
        if self._verbose:
            print("ld r8, r8")
        self._regs[reg_1] = self._regs[reg_2]

    def ld_r8_mem_r16(self, reg_8: str, reg_16: str) -> None:
        if self._verbose:
            print("ld r8, [r16]")
        addr = self.get_16_bit_reg_val(reg_16)
        self._regs[reg_8] = self._mem[addr]
        
    def ld_mem_r16_r8(self, reg_16: str, reg_8: str) -> None:
        if self._verbose:
            print("ld [r16], r8")
        addr = self.get_16_bit_reg_val(reg_16)
        self._mem[addr] = self._reg[reg_8]

    def ld_r16_n16(self, reg: str):
        if self._verbose:
            print("ld [r16], r16")
        val = self.fetch_operands(2)
        val_0, val_1 = self.convert_16_val_to_two_8_bit_vals(val)
        reg_0 = reg[0]
        reg_1 = reg[1]
        self._reg[reg_0] = val_0
        self._reg[reg_1] = val_1

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

    def add_a_r8(self, reg: str) -> None:
        if (self._verbose):
            print(f"add_a_{reg}")
        new_a = self._regs["a"] + self._regs[reg]
        if (new_a == 256):
            self._regs["a"] = 0
            self.set_z()
            self.unset_c()
        elif (new_a > 256):
            self._regs["a"] = new_a % 256
            self.unset_z()
            self.set_c()
        else:
            self._regs["a"] = new_a
            self.unset_c()
            self.unset_z()

    def add_a_mem_hl(self) -> None:
        if (self._verbose):
            print("add_a_mem_hl")
        new_a = self._regs["a"] + self._mem[self.get_16_bit_reg_val("hl")]
        if (new_a == 256):
            self._regs["a"] = 0
            self.set_z()
            self.unset_c()
        elif (new_a > 256):
            self._regs["a"] = new_a % 256
            self.set_c()
            self.unset_z()
        else:
            self._regs["a"] = new_a
            self.unset_z()
            self.unset_c()

    def add_a_n8(self) -> None:
        if (self._verbose):
            print(f"add_a_n8")
        instr = self.fetch_operands(1)
        new_a = self._regs["a"] + instr[0]
        if (new_a == 256):
            self._regs["a"] = 0
            self.set_z()
            self.unset_c()
        elif (new_a > 256):
            self._regs["a"] = new_a % 256
            self.set_c()
            self.unset_z()
        else:
            self._regs["a"] = new_a
            self.unset_z()
            self.unset_c()
            
    def sub_a_r8(self, reg:str) -> None:
        new_a = self._regs["a"] - self._regs[reg]
        if (new_a == 0):
            self._regs["a"] = 0
            self.set_z()
            self.unset_c()
        elif(new_a < 0):
            self._regs["a"] = new_a + 256
            self.set_c()
            self.unset_z()
        else:
            self._regs["a"] = new_a
            self.unset_c()
            self.unset_z()

    def sub_a_mem_hl(self) -> None:
        new_a = self._regs["a"] - self._mem[self.get_16_bit_reg_val("hl")]
        if (new_a == 0):
            self._regs["a"] = 0
            self.set_z()
            self.unset_c()
        elif(new_a < 0):
            self._regs["a"] = new_a + 256
            self.set_c()
            self.unset_z()
        else:
            self._regs["a"] = new_a
            self.unset_c()
            self.unset_z()

    def sub_a_n8(self) -> None:
        instr = self.fetch_operands(1)
        new_a = self._regs["a"] - instr[0]
        if (new_a == 0):
            self._regs["a"] = 0
            self.set_z()
            self.unset_c()
        elif(new_a < 0):
            self._regs["a"] = new_a + 256
            self.set_c()
            self.unset_z()
        else:
            self._regs["a"] = new_a
            self.unset_c()
            self.unset_z()

        
    def push_r16(self, reg:str) -> None:
        self._mem[self._regs["sp"]] -= 2
        self._mem[self._regs["sp"]] = self.regs_[reg[1]]
        self._mem[self._regs["sp"] + 1] = self.regs_[reg[0]]

    def pop_r16(self, reg:str) -> None:
        self._regs[str[1]] = self._mem[self._regs["sp"]]
        self._regs[str[0]] = self._mem[self._regs["sp"] + 1]
        self._regs["sp"] += 2

    def call(self) -> None:
        if (self._verbose):
            print("call")
        instr = self.fetch_operands(2)
        new_address = self.to_little(instr)
        self._regs["sp"] -= 2
        pc_0, pc_1 = self.convert_16_val_to_two_8_bit_vals(self._regs["pc"])
        self._mem[self._regs["sp"]] = pc_1
        self._mem[self._regs["sp"] + 1] = pc_0
        self._regs["pc"] = new_address

    def ret(self) -> None:
        self._regs["pc"] = self.to_little([self._mem[self._regs["sp"]], self._mem[self._regs["sp"] + 1]])
        print(self._regs["pc"])
        self._regs["sp"] += 2


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