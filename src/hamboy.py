import sys
import argparse
import emulator

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HamBoy emulator.')
    parser.add_argument('-v', help='enable verbose output', action="store_true")

    parser.add_argument('rom_file', default="game.gb", help='rom file')
    args = parser.parse_args()
    verbose = args.v
    file_name = args.rom_file
    rom = emulator.read_rom(file_name, verbose)
    if verbose:
        emulator.print_rom(rom)

    hamboy = emulator.Emulator(rom, verbose)
    hamboy.run()