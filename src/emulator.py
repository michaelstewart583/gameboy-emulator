import typing

class Emulator:
    def __init__(self, mem: list[int], verbose: bool = False) -> None:
        self._mem = mem
        self.init_regs()
        self.init_isa()
        self._interrupts_enabled = True
        self._verbose = verbose

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
        new_address = instr[1] << 8 | instr[0]
        if self._verbose:
            print("{0:04X}".format(new_address))
        self._regs["pc"] = new_address

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
    rom = read_rom("main.gb", verbose)
    if verbose:
        print_rom(rom)

    emulator = Emulator(rom, verbose)
    emulator.run()