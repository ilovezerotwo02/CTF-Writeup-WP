#!/usr/bin/env python3
import math
import struct
from collections import Counter
from pathlib import Path


WIDTH = 262
HEIGHT = 274
PLANE_SIZE = WIDTH * HEIGHT
PROBES = [0, 1] + list(range(3, 33, 2))


def read_c_string(blob, offset):
    end = blob.find(b"\x00", offset)
    if end == -1:
        end = len(blob)
    return blob[offset:end].decode("latin1")


def parse_layout(blob):
    header = struct.unpack(">HHIIIIIHHHHHH", blob[16:52])
    shoff = header[5]
    shentsize = header[10]
    shnum = header[11]
    shstrndx = header[12]

    sections = []
    for idx in range(shnum):
        off = shoff + idx * shentsize
        sections.append(struct.unpack(">IIIIIIIIII", blob[off:off + shentsize]))

    shstr = sections[shstrndx]
    shstrtab = blob[shstr[4]:shstr[4] + shstr[5]]

    def sec_name(pos):
        return read_c_string(shstrtab, pos)

    named_sections = {sec_name(sec[0]): sec for sec in sections}
    strtab = named_sections[".strtab"]
    strtab_data = blob[strtab[4]:strtab[4] + strtab[5]]

    symbols = []
    symtab = named_sections[".symtab"]
    for idx in range(symtab[5] // symtab[9]):
        off = symtab[4] + idx * symtab[9]
        st_name, st_value, st_size = struct.unpack_from(">III", blob, off)
        st_info = blob[off + 12]
        st_shndx = struct.unpack_from(">H", blob, off + 14)[0]
        symbols.append(
            {
                "name": read_c_string(strtab_data, st_name) if st_name else "",
                "value": st_value,
                "size": st_size,
                "bind": st_info >> 4,
                "shndx": st_shndx,
            }
        )

    return named_sections, symbols


def rebuild_plane(obj_path):
    blob = bytearray(Path(obj_path).read_bytes())
    if blob[:4] != b"\x7fELF" or blob[4] != 1 or blob[5] != 2:
        raise ValueError("target is not a 32-bit big-endian ELF")

    sections, symbols = parse_layout(blob)
    auth = sections[".lm.auth"]
    rel = sections[".lm.auth.rel"]

    plane = bytearray(blob[auth[4]:auth[4] + auth[5]])

    rel_off = rel[4]
    rel_size = rel[5]
    rel_entsize = rel[9]

    for idx in range(rel_size // rel_entsize):
        item_off = rel_off + idx * rel_entsize
        dst, info = struct.unpack_from(">II", blob, item_off)
        r_type = info & 0xFF
        sym_idx = info >> 8
        sym_value = symbols[sym_idx]["value"]

        if r_type == 2:  # R_MIPS_32
            struct.pack_into(">I", plane, dst, sym_value)
            continue

        if r_type == 5:  # R_MIPS_HI16
            cur = struct.unpack_from(">I", plane, dst)[0]
            hi_addend = (cur >> 16) & 0xFFFF
            hi_result = (((hi_addend << 16) + sym_value + 0x8000) >> 16) & 0xFFFF
            struct.pack_into(">I", plane, dst, (cur & 0xFFFF) | (hi_result << 16))
            continue

        if r_type == 6:  # R_MIPS_LO16
            cur = struct.unpack_from(">I", plane, dst)[0]
            lo_addend = cur & 0xFFFF
            lo_result = (lo_addend + sym_value) & 0xFFFF
            struct.pack_into(">I", plane, dst, (cur & 0xFFFF0000) | lo_result)

    return bytes(plane[:PLANE_SIZE])


def column_background(raw_plane):
    background = []
    for col in range(WIDTH):
        values = Counter(raw_plane[row * WIDTH + col] for row in range(HEIGHT))
        background.append(values.most_common(1)[0][0])
    return background


def sample_track(raw_plane, background, start, step, count):
    def is_marked(pos):
        return raw_plane[pos] != background[pos % WIDTH]

    digits = []
    for idx in range(count):
        pos = start + idx * step
        active = 0
        for delta in PROBES:
            spot = pos + delta
            if 0 <= spot < len(raw_plane) and is_marked(spot):
                active += 1
        digits.append(active - 2)
    return digits


def colex_rank(bits):
    rank = 0
    ones = [idx for idx, bit in enumerate(bits) if bit]
    for idx, pos in enumerate(ones, start=1):
        rank += math.comb(pos, idx)
    return rank


def recover_flag(obj_path="l11nk.o"):
    raw_plane = rebuild_plane(obj_path)
    background = column_background(raw_plane)

    upper = sample_track(raw_plane, background, start=4707, step=280, count=76)
    lower = sample_track(raw_plane, background, start=26691, step=282, count=75)

    left_runs = upper[:-1]
    right_runs = lower[:-1]

    bits = []
    for idx in range(max(len(left_runs), len(right_runs))):
        if idx < len(right_runs):
            bits.extend([0] * right_runs[idx])
        if idx < len(left_runs):
            bits.extend([1] * left_runs[idx])

    if len(bits) != 127 or sum(bits) != 63:
        raise ValueError("decoded path does not satisfy expected shape")

    body = colex_rank(bits).to_bytes(16, "big").hex()
    return {
        "flag": f"ISCC{{{body}}}",
        "track_upper": "".join(format(x, "x") for x in upper),
        "track_lower": "".join(format(x, "x") for x in lower),
        "sum_upper": sum(left_runs),
        "sum_lower": sum(right_runs),
    }


def main():
    result = recover_flag()
    print("upper =", result["track_upper"])
    print("lower =", result["track_lower"])
    print("sum_upper =", result["sum_upper"])
    print("sum_lower =", result["sum_lower"])
    print(result["flag"])


if __name__ == "__main__":
    main()
