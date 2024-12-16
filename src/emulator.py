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

        self._isa[0x00] = self.nop

        self._isa[0xC3] = self.jump
        self._isa[0xC2] = self.jp_nz_n16
        self._isa[0xCA] = self.jp_z_n16
        self._isa[0xD2] = self.jp_nc_n16
        self._isa[0xDA] = self.jp_c_n16

        self._isa[0X20] = self.jr_nz

        self._isa[0x01] = lambda: self.ld_r16_n16("bc")
        self._isa[0x11] = lambda: self.ld_r16_n16("de")
        self._isa[0x21] = lambda: self.ld_r16_n16("hl")

        self._isa[0x02] = lambda: self.ld_mem_r16_r8("bc", "a")
        self._isa[0x0A] = lambda: self.ld_r8_mem_r16("a", "bc")
        self._isa[0x12] = lambda: self.ld_mem_r16_r8("de", "a")
        self._isa[0x1A] = lambda: self.ld_r8_mem_r16("a", "de")
        self._isa[0x22] = self.ld_mem_hli_a
        self._isa[0x2A] = self.ld_a_mem_hli

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

        self._isa[0X36] = self.ld_mem_hl_n8
 
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
        
        self._isa[0X04] = lambda: self.inc_r8("b")
        self._isa[0X0C] = lambda: self.inc_r8("c")
        self._isa[0X14] = lambda: self.inc_r8("d")
        self._isa[0X1C] = lambda: self.inc_r8("e")
        self._isa[0X24] = lambda: self.inc_r8("h")
        self._isa[0X2C] = lambda: self.inc_r8("l")
        self._isa[0x3C] = lambda: self.inc_r8("a")

        self._isa[0X05] = lambda: self.dec_8_bit("b")
        self._isa[0X0D] = lambda: self.dec_8_bit("c")
        self._isa[0X15] = lambda: self.dec_8_bit("d")
        self._isa[0X1D] = lambda: self.dec_8_bit("e")
        self._isa[0X25] = lambda: self.dec_8_bit("h")
        self._isa[0X2D] = lambda: self.dec_8_bit("l")
        self._isa[0X3D] = lambda: self.dec_8_bit("a")

        self._isa[0X03] = lambda: self.inc_r16("bc")
        self._isa[0X13] = lambda: self.inc_r16("de")
        self._isa[0X23] = lambda: self.inc_r16("hl")
        
        self._isa[0X0B] = lambda: self.dec_r16("bc")
        self._isa[0X1B] = lambda: self.dec_r16("de") 
        self._isa[0X2B] = lambda: self.dec_r16("hl") 
        
        self._isa[0X09] = lambda: self.add_hl_r16("hl", "bc")
        self._isa[0X19] = lambda: self.add_hl_r16("hl", "de")
        self._isa[0X29] = lambda: self.add_hl_r16("hl", "hl")

        self._isa[0XFE] = self.cp_n8
        self._isa[0XB8] = lambda: self.cp_r8("b")
        self._isa[0XB9] = lambda: self.cp_r8("c")
        self._isa[0XBA] = lambda: self.cp_r8("d")
        self._isa[0XBB] = lambda: self.cp_r8("e")
        self._isa[0XBC] = lambda: self.cp_r8("h")
        self._isa[0XBD] = lambda: self.cp_r8("l")
        self._isa[0XBE] = self.cp_mem_hl
        self._isa[0XBF] = lambda: self.cp_r8("a")

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
        self._isa[0XD6] = self.sub_a_n8

        self._isa[0XC5] = lambda: self.push_r16("bc")
        self._isa[0XD5] = lambda: self.push_r16("de")
        self._isa[0XE5] = lambda: self.push_r16("hl")
        self._isa[0xF5] = lambda: self.push_r16("af")

        self._isa[0XC1] = lambda: self.pop_r16("bc")
        self._isa[0XD1] = lambda: self.pop_r16("de")
        self._isa[0XE1] = lambda: self.pop_r16("hl")
        self._isa[0XF1] = lambda: self.pop_r16("af")
        
        self._isa[0XCD] = self.call
        self._isa[0XC9] = self.ret

        self._isa[0XA7] = lambda: self.logic_and("a")
        self._isa[0XA0] = lambda: self.logic_and("b")
        self._isa[0XA1] = lambda: self.logic_and("c")
        self._isa[0XA2] = lambda: self.logic_and("d")
        self._isa[0XA3] = lambda: self.logic_and("e")
        self._isa[0XA4] = lambda: self.logic_and("h")
        self._isa[0XA5] = lambda: self.logic_and("l")
        self._isa[0XA6] = self.logic_and_mem

        self._isa[0XAF] = lambda: self.logic_xor("a")
        self._isa[0XA8] = lambda: self.logic_xor("b")
        self._isa[0XA9] = lambda: self.logic_xor("c")
        self._isa[0XAA] = lambda: self.logic_xor("d")
        self._isa[0XAB] = lambda: self.logic_xor("e")
        self._isa[0XAC] = lambda: self.logic_xor("h")
        self._isa[0XAD] = lambda: self.logic_xor("l")
        self._isa[0XAE] = self.logic_xor_mem

        self._isa[0XB7] = lambda: self.logic_or("a")
        self._isa[0XB0] = lambda: self.logic_or("b")
        self._isa[0XB1] = lambda: self.logic_or("c")
        self._isa[0XB2] = lambda: self.logic_or("d")
        self._isa[0XB3] = lambda: self.logic_or("e")
        self._isa[0XB4] = lambda: self.logic_or("h")
        self._isa[0XB5] = lambda: self.logic_or("l")
        self._isa[0XB6] = self.logic_or_mem
        
        self._isa[0XCB40] = lambda: self.bit(0, "b")
        self._isa[0XCB41] = lambda: self.bit(0, "c")
        self._isa[0XCB42] = lambda: self.bit(0, "d")
        self._isa[0XCB43] = lambda: self.bit(0, "e")
        self._isa[0XCB44] = lambda: self.bit(0, "h")
        self._isa[0XCB45] = lambda: self.bit(0, "l")
        self._isa[0XCB46] = lambda: self.bit_mem(0)
        self._isa[0XCB47] = lambda: self.bit(0, "a")

        self._isa[0XCB48] = lambda: self.bit(1, "b")
        self._isa[0XCB49] = lambda: self.bit(1, "c")
        self._isa[0XCB4A] = lambda: self.bit(1, "d")
        self._isa[0XCB4B] = lambda: self.bit(1, "e")
        self._isa[0XCB4C] = lambda: self.bit(1, "h")
        self._isa[0XCB4D] = lambda: self.bit(1, "l")
        self._isa[0XCB4E] = lambda: self.bit_mem(1)
        self._isa[0XCB4F] = lambda: self.bit(1, "a")

        self._isa[0XCB50] = lambda: self.bit(2, "b")
        self._isa[0XCB51] = lambda: self.bit(2, "c")
        self._isa[0XCB52] = lambda: self.bit(2, "d")
        self._isa[0XCB53] = lambda: self.bit(2, "e")
        self._isa[0XCB54] = lambda: self.bit(2, "h")
        self._isa[0XCB55] = lambda: self.bit(2, "l")
        self._isa[0XCB56] = lambda: self.bit_mem(2)
        self._isa[0XCB57] = lambda: self.bit(2, "a")

        self._isa[0XCB58] = lambda: self.bit(3, "b")
        self._isa[0XCB59] = lambda: self.bit(3, "c")
        self._isa[0XCB5A] = lambda: self.bit(3, "d")
        self._isa[0XCB5B] = lambda: self.bit(3, "e")
        self._isa[0XCB5C] = lambda: self.bit(3, "h")
        self._isa[0XCB5D] = lambda: self.bit(3, "l")
        self._isa[0XCB5E] = lambda: self.bit_mem(3)
        self._isa[0XCB5F] = lambda: self.bit(3, "a")

        self._isa[0XCB60] = lambda: self.bit(4, "b")
        self._isa[0XCB61] = lambda: self.bit(4, "c")
        self._isa[0XCB62] = lambda: self.bit(4, "d")
        self._isa[0XCB63] = lambda: self.bit(4, "e")
        self._isa[0XCB64] = lambda: self.bit(4, "h")
        self._isa[0XCB65] = lambda: self.bit(4, "l")
        self._isa[0XCB66] = lambda: self.bit_mem(4)
        self._isa[0XCB67] = lambda: self.bit(4, "a")

        self._isa[0XCB68] = lambda: self.bit(5, "b")
        self._isa[0XCB69] = lambda: self.bit(5, "c")
        self._isa[0XCB6A] = lambda: self.bit(5, "d")
        self._isa[0XCB6B] = lambda: self.bit(5, "e")
        self._isa[0XCB6C] = lambda: self.bit(5, "h")
        self._isa[0XCB6D] = lambda: self.bit(5, "l")
        self._isa[0XCB6E] = lambda: self.bit_mem(5)
        self._isa[0XCB6F] = lambda: self.bit(5, "a")

        self._isa[0XCB70] = lambda: self.bit(6, "b")
        self._isa[0XCB71] = lambda: self.bit(6, "c")
        self._isa[0XCB72] = lambda: self.bit(6, "d")
        self._isa[0XCB73] = lambda: self.bit(6, "e")
        self._isa[0XCB74] = lambda: self.bit(6, "h")
        self._isa[0XCB75] = lambda: self.bit(6, "l")
        self._isa[0XCB76] = lambda: self.bit_mem(6)
        self._isa[0XCB77] = lambda: self.bit(6, "a")

        self._isa[0XCB78] = lambda: self.bit(7, "b")
        self._isa[0XCB79] = lambda: self.bit(7, "c")
        self._isa[0XCB7A] = lambda: self.bit(7, "d")
        self._isa[0XCB7B] = lambda: self.bit(7, "e")
        self._isa[0XCB7C] = lambda: self.bit(7, "h")
        self._isa[0XCB7D] = lambda: self.bit(7, "l")
        self._isa[0XCB7E] = lambda: self.bit_mem(7)
        self._isa[0XCB7F] = lambda: self.bit(7, "a")

        self._isa[0XCBC0] = lambda: self.set(0, "b")
        self._isa[0XCBC1] = lambda: self.set(0, "c")
        self._isa[0XCBC2] = lambda: self.set(0, "d")
        self._isa[0XCBC3] = lambda: self.set(0, "e")
        self._isa[0XCBC4] = lambda: self.set(0, "h")
        self._isa[0XCBC5] = lambda: self.set(0, "l")
        self._isa[0XCBC6] = lambda: self.set_mem(0)
        self._isa[0XCBC7] = lambda: self.set(0, "a")

        self._isa[0XCBC8] = lambda: self.set(1, "b")
        self._isa[0XCBC9] = lambda: self.set(1, "c")
        self._isa[0XCBCA] = lambda: self.set(1, "d")
        self._isa[0XCBCB] = lambda: self.set(1, "e")
        self._isa[0XCBCC] = lambda: self.set(1, "h")
        self._isa[0XCBCD] = lambda: self.set(1, "l")
        self._isa[0XCBCE] = lambda: self.set_mem(1)
        self._isa[0XCBCF] = lambda: self.set(1, "a")

        self._isa[0XCBD0] = lambda: self.set(2, "b")
        self._isa[0XCBD1] = lambda: self.set(2, "c")
        self._isa[0XCBD2] = lambda: self.set(2, "d")
        self._isa[0XCBD3] = lambda: self.set(2, "e")
        self._isa[0XCBD4] = lambda: self.set(2, "h")
        self._isa[0XCBD5] = lambda: self.set(2, "l")
        self._isa[0XCBD6] = lambda: self.set_mem(2)
        self._isa[0XCBD7] = lambda: self.set(2, "a")

        self._isa[0XCBD8] = lambda: self.set(3, "b")
        self._isa[0XCBD9] = lambda: self.set(3, "c")
        self._isa[0XCBDA] = lambda: self.set(3, "d")
        self._isa[0XCBDB] = lambda: self.set(3, "e")
        self._isa[0XCBDC] = lambda: self.set(3, "h")
        self._isa[0XCBDD] = lambda: self.set(3, "l")
        self._isa[0XCBDE] = lambda: self.set_mem(3)
        self._isa[0XCBDF] = lambda: self.set(3, "a")

        self._isa[0XCBE0] = lambda: self.set(4, "b")
        self._isa[0XCBE1] = lambda: self.set(4, "c")
        self._isa[0XCBE2] = lambda: self.set(4, "d")
        self._isa[0XCBE3] = lambda: self.set(4, "e")
        self._isa[0XCBE4] = lambda: self.set(4, "h")
        self._isa[0XCBE5] = lambda: self.set(4, "l")
        self._isa[0XCBE6] = lambda: self.set_mem(4)
        self._isa[0XCBE7] = lambda: self.set(4, "a")

        self._isa[0XCBE8] = lambda: self.set(5, "b")
        self._isa[0XCBE9] = lambda: self.set(5, "c")
        self._isa[0XCBEA] = lambda: self.set(5, "d")
        self._isa[0XCBEB] = lambda: self.set(5, "e")
        self._isa[0XCBEC] = lambda: self.set(5, "h")
        self._isa[0XCBED] = lambda: self.set(5, "l")
        self._isa[0XCBEE] = lambda: self.set_mem(5)
        self._isa[0XCBEF] = lambda: self.set(5, "a")

        self._isa[0XCBF0] = lambda: self.set(6, "b")
        self._isa[0XCBF1] = lambda: self.set(6, "c")
        self._isa[0XCBF2] = lambda: self.set(6, "d")
        self._isa[0XCBF3] = lambda: self.set(6, "e")
        self._isa[0XCBF4] = lambda: self.set(6, "h")
        self._isa[0XCBF5] = lambda: self.set(6, "l")
        self._isa[0XCBF6] = lambda: self.set_mem(6)
        self._isa[0XCBF7] = lambda: self.set(6, "a")

        self._isa[0XCBF8] = lambda: self.set(7, "b")
        self._isa[0XCBF9] = lambda: self.set(7, "c")
        self._isa[0XCBFA] = lambda: self.set(7, "d")
        self._isa[0XCBFB] = lambda: self.set(7, "e")
        self._isa[0XCBFC] = lambda: self.set(7, "h")
        self._isa[0XCBFD] = lambda: self.set(7, "l")
        self._isa[0XCBFE] = lambda: self.set_mem(7)
        self._isa[0XCBFF] = lambda: self.set(7, "a")

        self._isa[0XCB38] = lambda: self.srl("b")
        self._isa[0XCB39] = lambda: self.srl("c")
        self._isa[0XCB3A] = lambda: self.srl("d")
        self._isa[0XCB3B] = lambda: self.srl("e")
        self._isa[0XCB3C] = lambda: self.srl("h")
        self._isa[0XCB3D] = lambda: self.srl("l")
        self._isa[0XCB3E] = self.srl_mem
        self._isa[0XCB3F] = lambda: self.srl("a")

        self._isa[0XF8] = self.ld_hl_sp
        self._isa[0XF9] = self.ld_sp_hl
        self._isa[0X08] = self.ld_mem_n16_sp
        self._isa[0X31] = self.ld_sp_n16
        self._isa[0X33] = self.inc_sp
        self._isa[0X39] = self.add_hl_sp
        self._isa[0X3B] = self.dec_sp

        self._isa[0X88] = lambda: self.adc_a_r8('b')
        self._isa[0X89] = lambda: self.adc_a_r8('c')
        self._isa[0X8A] = lambda: self.adc_a_r8('d')
        self._isa[0X8B] = lambda: self.adc_a_r8('e')
        self._isa[0X8C] = lambda: self.adc_a_r8('h')
        self._isa[0X8D] = lambda: self.adc_a_r8('l')
        self._isa[0X8E] = self.adc_a_mem_hl
        self._isa[0X8F] = lambda: self.adc_a_r8('a')

        self._isa[0XC4] = self.call_nz
        self._isa[0XCC] = self.call_z
        self._isa[0XD4] = self.call_nc
        self._isa[0XDC] = self.call_c

        self._isa[0XE6] = self.logic_and_n8
        self._isa[0XEE] = self.logic_xor_n8
        self._isa[0XF6] = self.logic_or_n8

        self._isa[0XCB30] = lambda: self.swap("b")
        self._isa[0XCB31] = lambda: self.swap("c")
        self._isa[0XCB32] = lambda: self.swap("d")
        self._isa[0XCB33] = lambda: self.swap("e")
        self._isa[0XCB34] = lambda: self.swap("h")
        self._isa[0XCB35] = lambda: self.swap("l")
        self._isa[0XCB36] = self.swap_mem_hl
        self._isa[0XCB37] = lambda: self.swap("a")

        self._isa[0X18] = self.jr
        self._isa[0X20] = self.jr_nz
        self._isa[0X28] = self.jr_z
        self._isa[0X30] = self.jr_nc
        self._isa[0X38] = self.jr_c

        self._isa[0X2F] = self.cpl
            
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
    
    def nop(self) -> None:
        if self._verbose:
            print("nop")
    
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
    
    #Takes the name of a 16 bit reg and returns it's value by combining the two 8 bit regs it is compossed of
    def get_16_bit_reg_val(self, reg:str) -> int:
        return self._regs[reg[0]] << 8 | self._regs[reg[1]]
    
    #Takes a 16 bit integer, and returns it's value as two 8 bit integers
    def convert_16_val_to_two_8_bit_vals(self, val: int) -> tuple[int, int]:
        val_0 = val >> 8
        val_1 = val & 0XFF
        return val_0, val_1
    
    #Takes an unsigned integer and returns it's value as a signed integers encoded with two's compliment
    def convert_unsigned_to_signed(self, val: int) -> int:
        if (val < 128):
            return val
        else:
            return val - 256

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

    def jr(self) -> None:
        if (self._verbose):
            print("jr")
        instr = self.fetch_operands(1)
        offset = self.convert_unsigned_to_signed(instr[0])
        self._regs["pc"] = offset + self._regs["pc"]

    def jr_nz(self) -> None:
        if (self._verbose):
            print("jr nz")
        instr = self.fetch_operands(1)
        if (self.z_is_set()):
            return
        offset = self.convert_unsigned_to_signed(instr[0])
        self._regs["pc"] = offset + self._regs["pc"]
    
    def jr_z(self) -> None:
        if (self._verbose):
            print("jr z")
        instr = self.fetch_operands(1)
        if (not self.z_is_set()):
            return
        offset = self.convert_unsigned_to_signed(instr[0])
        self._regs["pc"] = offset + self._regs["pc"]

    def jr_nc(self) -> None:
        if (self._verbose):
            print("jr nc")
        instr = self.fetch_operands(1)
        if (self.c_is_set()):
            return
        offset = self.convert_unsigned_to_signed(instr[0])
        self._regs["pc"] = offset + self._regs["pc"]

    def jr_c(self) -> None:
        if (self._verbose):
            print("jr c")
        instr = self.fetch_operands(1)
        if (not self.c_is_set()):
            return
        offset = self.convert_unsigned_to_signed(instr[0])
        self._regs["pc"] = offset + self._regs["pc"]

    def ld_r8_n8(self, reg: str) -> None:
        val = self.fetch_operands(1)
        if self._verbose:
            print(f"ld {reg}, n8")
        self._regs[reg] = val[0]

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
            print(f"ld {reg_1}, {reg_2}")
        self._regs[reg_1] = self._regs[reg_2]

    def ld_r8_mem_r16(self, reg_8: str, reg_16: str) -> None:
        if self._verbose:
            print(f"ld {reg_8}, [{reg_16}]")
        addr = self.get_16_bit_reg_val(reg_16)
        self._regs[reg_8] = self._mem[addr]
        
    def ld_mem_r16_r8(self, reg_16: str, reg_8: str) -> None:
        if self._verbose:
            print(f"ld [{reg_16}], {reg_8}")
        addr = self.get_16_bit_reg_val(reg_16)
        self._mem[addr] = self._regs[reg_8]
    
    def ld_mem_hl_n8(self) -> None:
        if self._verbose:
            print("ld [hl], n8")
        val = self.fetch_operands(1)
        addr = self.get_16_bit_reg_val("hl")
        self._mem[addr] = val[0]

    def ld_hl_sp(self) -> None:
        if (self._verbose):
            print("ld hl, sp")
        reg_h, reg_l = self.convert_16_val_to_two_8_bit_vals(self._regs["sp"])
        self._regs["h"] = reg_h
        self._regs["l"] = reg_l

    def ld_sp_hl(self) -> None:
        if (self._verbose):
            print("ld sp, hl")
        self._regs["sp"] = self.get_16_bit_reg_val("hl")

    def ld_mem_n16_sp(self) -> None:
        if (self._verbose):
            print("ld [n16], sp")
        instr = self.fetch_operands(2)
        self._mem[self.to_little(instr)] = self._regs["sp"]
        
    def ld_sp_n16(self) -> None:
        if self._verbose:
            print("ld sp, n16")
        val = self.fetch_operands(2)
        self._regs["sp"] = self.to_little(val)

    def inc_sp(self):
        if self._verbose:
            print("inc sp")
        self._regs["sp"] += 1

    def dec_sp(self):
        if self._verbose:
            print("dec sp")
        self._regs["sp"] -= 1
    
    def add_hl_sp(self):
        if self._verbose:
            print(f"add hl, ")
        val_1 = self.get_16_bit_reg_val("hl")
        val_2 = self.get_16_bit_reg_val("sp")
        val = val_1 + val_2
        if (val > 0XFFFF):
            self.set_c()
            val %= 0x10000
        else:
            self.unset_c()
        self._regs["h"], self._regs["l"] = self.convert_16_val_to_two_8_bit_vals(val)

    def ld_mem_hli_a(self) -> None:
        if self._verbose:
            print(f"ld [hli], a")
        addr = self.get_16_bit_reg_val("hl")
        self._mem[addr] = self._regs["a"]
        addr += 1
        self.inc_r16("hl")

    def ld_a_mem_hli(self):
        if self._verbose:
            print(f"ld a, [hli]")
        addr = self.get_16_bit_reg_val("hl")
        self._regs["a"] = self._mem[addr]
        addr += 1
        self.inc_r16("hl")


    def ld_r16_n16(self, reg: str):
        if self._verbose:
            print(f"ld [{reg}], n16")
        val = self.fetch_operands(2)
        val_1, val_0 = val
        reg_0 = reg[0]
        reg_1 = reg[1]
        self._regs[reg_0] = val_0
        self._regs[reg_1] = val_1

    def inc_r8(self, reg: str) -> None:
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
            
    def inc_r16(self, reg_16: str) -> None:
        if self._verbose:
            print(f"inc {reg_16}")
        val = self.get_16_bit_reg_val(reg_16) 
        val += 1
        val %= 0x10000
        val_0, val_1 = self.convert_16_val_to_two_8_bit_vals(val)
        reg_0 = reg_16[0]
        reg_1 = reg_16[1]
        self._regs[reg_0] = val_0
        self._regs[reg_1] = val_1
        
    def dec_r16(self, reg_16: str) -> None:
        if self._verbose:
            print(f"dec {reg_16}")
        val = self.get_16_bit_reg_val(reg_16)
        val -= 1
        val %= 0X10000
        val_0, val_1 = self.convert_16_val_to_two_8_bit_vals(val)
        reg_0 = reg_16[0]
        reg_1 = reg_16[1]
        self._regs[reg_0] = val_0
        self._regs[reg_1] = val_1

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

    def cp_r8(self, reg: str) -> None:
        if self._verbose:
            print(f"cp {reg}")
        if self._regs["a"] == self._regs[reg]:
            self.set_z()
            self.unset_c()
        elif self._regs["a"] > self._regs[reg]:
            self.unset_z()
            self.unset_c()
        else:
            self.unset_z()
            self.set_c()

    def cp_mem_hl(self) -> None:
        if (self._verbose):
            print("cp [hl]")
        addr = self.get_16_bit_reg_val("hl")
        if self._regs["a"] == self._mem[addr]:
            self.set_z()
            self.unset_c()
        elif self._regs["a"] > self._mem[addr]:
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
        else:
            self.fetch_operands(2)

    def jp_z_n16(self) -> None:
        if (self._verbose):
            print("jp z, n16")
        if (self.z_is_set()):
            self.jump()
        else:
            self.fetch_operands(2)

    def jp_c_n16(self) -> None:
        if (self._verbose):
            print("jp c, n16")
        if (self.c_is_set()):
            self.jump()
        else:
            self.fetch_operands(2)

    def jp_nc_n16(self) -> None:
        if (self._verbose):
            print("jp nc, n16")
        if (not self.c_is_set()):
            self.jump()
        else:
            self.fetch_operands(2)

    def add_a_r8(self, reg: str) -> None:
        if (self._verbose):
            print(f"add a, {reg}")
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
            print("add a, [hl]")
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
            print(f"add a, n8")
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

    def adc_a_r8(self, reg: str) -> None:
        if (self._verbose):
            print(f"adc a, {reg}")
        val = self._regs[reg]
        new_a = self._regs["a"] + val + self.c_is_set()
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

    def adc_a_mem_hl(self) -> None:
        if (self._verbose):
            print("add a, [hl]")
        addr = self.gget_16_bit_reg_val("hl")
        new_a = self._regs["a"] + self._mem[addr] + self.c_is_set()
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
        if (self._verbose):
            print(f"sub a, {reg}")
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
        if (self._verbose):
            print(f"sub a, [hl]")
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
        if (self._verbose):
            print(f"sub a, n8")
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

    def add_hl_r16(self, reg_1: str, reg_2: str) -> None:
        if self._verbose:
            print(f"add {reg_1}, {reg_2}")
        val_1 = self.get_16_bit_reg_val(reg_1)
        val_2 = self.get_16_bit_reg_val(reg_2)
        val = val_1 + val_2
        if (val > 0XFFFF):
            self.set_c()
            val %= 0x10000
        else:
            self.unset_c()
        self._regs[reg_1[0]], self._regs[reg_1[1]] = self.convert_16_val_to_two_8_bit_vals(val)
    
    def push_r16(self, reg:str) -> None:
        if (self._verbose):
            print(f"push {reg}")
        self._regs["sp"] -= 2
        self._mem[self._regs["sp"]] = self._regs[reg[1]]
        self._mem[self._regs["sp"] + 1] = self._regs[reg[0]]

    def pop_r16(self, reg:str) -> None:
        if (self._verbose):
            print(f"pop {reg}")        
        self._regs[reg[1]] = self._mem[self._regs["sp"]]
        self._regs[reg[0]] = self._mem[self._regs["sp"] + 1]
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

    def call_z(self) -> None:
        if (self._verbose):
            print("call z")
        if (not self.z_is_set()):
            return
        self.call()

    def call_nz(self) -> None:
        if (self._verbose):
            print("call nz")
        if (self.z_is_set()):
            return
        self.call()

    def call_c(self) -> None:
        if (self._verbose):
            print("call c")
        if (not self.c_is_set()):
            return
        self.call()

    def call_nc(self) -> None:
        if (self._verbose):
            print("call nc")
        if (self.c_is_set()):
            return
        self.call()

    def ret(self) -> None:
        if (self._verbose):
            print("ret")
        self._regs["pc"] = self.to_little([self._mem[self._regs["sp"]], self._mem[self._regs["sp"] + 1]])
        self._regs["sp"] += 2

    def logic_and(self, reg: str) -> None:
        if (self._verbose):
            print(f"and a, {reg}")
        self._regs["a"] = self._regs["a"] & self._regs[reg]
        self.unset_c()
        if (self._regs["a"] == 0):
            self.set_z()
        else:
            self.unset_z()

    def logic_and_n8(self) -> None:
        if (self._verbose):
            print("and n8")
        instr = self.fetch_operands(1)
        self._regs["a"] = self._regs["a"] & instr[0]
        self.unset_c()
        if (self._regs["a"] == 0):
            self.set_z()
        else:
            self.unset_z()
        
    def logic_and_mem(self) -> None:
        if (self._verbose):
            print("and a, [hl]")
        self._regs["a"] = self._regs["a"] & self._mem[self.get_16_bit_reg_val("hl")]
        self.unset_c()
        if (self._regs["a"] == 0):
            self.set_z()
        else:
            self.unset_z()

    def logic_or(self, reg: str) -> None:
        if (self._verbose):
            print(f"or a, {reg}")
        self._regs["a"] = self._regs["a"] | self._regs[reg]
        self.unset_c()
        if (self._regs["a"] == 0):
            self.set_z()
        else:
            self.unset_z()

    def logic_or_mem(self) -> None:
        if (self._verbose):
            print("or a, [hl]")
        self._regs["a"] = self._regs["a"] | self._mem[self.get_16_bit_reg_val("hl")]
        self.unset_c()
        if (self._regs["a"] == 0):
            self.set_z()
        else:
            self.unset_z()

    def logic_or_n8(self) -> None:
        if (self._verbose):
            print("or n8")
        instr = self.fetch_operands(1)
        self._regs["a"] = self._regs["a"] | instr[0]
        self.unset_c()
        if (self._regs["a"] == 0):
            self.set_z()
        else:
            self.unset_z()

    def logic_xor(self, reg: str) -> None:
        if (self._verbose):
            print(f"xor a, {reg}")
        self._regs["a"] = self._regs["a"] ^ self._regs[reg]
        self.unset_c()
        if (self._regs["a"] == 0):
            self.set_z()
        else:
            self.unset_z()

    def logic_xor_mem(self) -> None:
        if (self._verbose):
            print("xor a, [hl]")
        self._regs["a"] = self._regs["a"] ^ self._mem[self.get_16_bit_reg_val("hl")]
        self.unset_c()
        if (self._regs["a"] == 0):
            self.set_z()
        else:
            self.unset_z()

    def logic_xor_n8(self) -> None:
        if (self._verbose):
            print("xor n8")
        instr = self.fetch_operands(1)
        self._regs["a"] = self._regs["a"] ^ instr[0]
        self.unset_c()
        if (self._regs["a"] == 0):
            self.set_z()
        else:
            self.unset_z()

    def bit(self, position: int, reg: str) -> None:
        if (self._verbose):
            print(f"bit {position}, {reg}")
        value = self._regs[reg] >> position
        if (value % 2 == 0):
            self.set_z()
        else:
            self.unset_z()

    def bit_mem(self, position: int) -> None:
        if (self._verbose):
            print(f"bit {position}, [hl]")
        value = self._mem[self.get_16_bit_reg_val("hl")] >> position
        if (value % 2 == 0):
            self.set_z()
        else:
            self.unset_z()
            
    def set(self, position: int, reg: str) -> None:
        if (self._verbose):
            print(f"set {position}, {reg}")
        value = 1 << position
        self._regs[reg] = self._regs[reg] | value
        if (self._regs[reg] == 0):
            self.set_z()
        else:
            self.unset_z()

    def set_mem(self, position: int) -> None:
        if (self._verbose):
            print(f"set {position}, [hl]")
        value = 1 << position
        address = self.get_16_bit_reg_val("hl")
        self.mem[address] = self._mem[address] | value
        if (self._mem[address] == 0):
            self.set_z()
        else:
            self.unset_z()

    def srl(self, reg: str) -> None:
        if(self._verbose):
            print(f"srl {reg}")
        if (self._regs[reg] == 1):
            self.set_c()
        else:
            self.unset_c()
        self._regs[reg] = self._regs[reg] >> 1
        if (self._regs[reg] == 0):
            self.set_z()
        else:
            self.unset_z()

    def srl_mem(self) -> None:
        if(self._verbose):
            print(f"srl [hl]")
        address = self.get_16_bit_reg_val("hl")
        if (self._mem[address] == 1):
            self.set_c()
        else:
            self.unset_c()
        self._mem[address] = self._mem[address] >> 1
        if (self._mem[address] == 0):
            self.set_z()
        else:
            self.unset_z()

    def swap(self, reg: str) -> None:
        if (self._verbose):
            print(f"swap {reg}")
        val = self._regs[reg]
        most_sig = val >> 4
        least_sig = val << 4 % 256
        self._regs[reg] = most_sig | least_sig

    def swap_mem_hl(self) -> None:
        if (self._verbose):
            print("swap [hl]")
        addr = self.get_16_bit_reg_val("hl")
        val = self._mem[addr]
        most_sig = val >> 4
        least_sig = val << 4 % 256
        self._mem[addr] = most_sig | least_sig

    def reti(self) -> None:
        if (self._verbose):
            print("reti")
        self.enable_interrupts()
        self.ret()

    def cpl(self) -> None:
        if (self._verbose):
            print("cpl")
        self._regs["a"] = self._regs["a"] ^ 0B11111111


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