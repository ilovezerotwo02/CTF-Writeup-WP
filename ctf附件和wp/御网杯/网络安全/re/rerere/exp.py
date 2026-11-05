import struct
from pathlib import Path


BASE = 0x140000000
BINARY = Path(__file__).with_name("rerere.exe")


def u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def rva_to_file_offset(data, rva):
    pe_offset = u32(data, 0x3C)
    section_count = u16(data, pe_offset + 6)
    optional_header_size = u16(data, pe_offset + 20)
    section_table = pe_offset + 24 + optional_header_size

    for i in range(section_count):
        entry = section_table + i * 40
        virtual_size = u32(data, entry + 8)
        virtual_address = u32(data, entry + 12)
        raw_size = u32(data, entry + 16)
        raw_address = u32(data, entry + 20)
        size = max(virtual_size, raw_size)

        if virtual_address <= rva < virtual_address + size:
            return raw_address + (rva - virtual_address)

    raise ValueError(f"RVA not found: 0x{rva:x}")


def read_va(data, va, size):
    return data[rva_to_file_offset(data, va - BASE):][:size]


def main():
    data = BINARY.read_bytes()

    target = read_va(data, 0x140004020, 38)
    key = read_va(data, 0x140004048, 8)
    table = read_va(data, 0x140004060, 256)

    inverse_table = [0] * 256
    for index, value in enumerate(table):
        inverse_table[value] = index

    flag = bytearray()
    for i, value in enumerate(target):
        flag.append(inverse_table[value] ^ key[i % len(key)])

    print(flag.decode())


if __name__ == "__main__":
    main()
