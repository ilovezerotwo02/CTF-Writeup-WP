import struct
import sys


def analyze(path):
    with open(path, "rb") as f:
        data = f.read()

    # 解析节区表
    e_shoff = struct.unpack_from(">I", data, 0x20)[0]
    e_shentsize = struct.unpack_from(">H", data, 0x2E)[0]
    e_shnum = struct.unpack_from(">H", data, 0x30)[0]

    sections = []
    for idx in range(e_shnum):
        off = e_shoff + idx * e_shentsize
        stype = struct.unpack_from(">I", data, off + 4)[0]
        soff = struct.unpack_from(">I", data, off + 16)[0]
        ssize = struct.unpack_from(">I", data, off + 20)[0]
        sections.append((stype, soff, ssize))

    sym_off, sym_size = sections[5][1], sections[5][2]
    str_off, str_size = sections[6][1], sections[6][2]
    rel_off, rel_size = sections[4][1], sections[4][2]

    # 字符串表
    strtab = data[str_off:str_off + str_size]

    def get_name(off):
        end = off
        while strtab[end] != 0:
            end += 1
        return strtab[off:end].decode("ascii", errors="replace")

    # 符号表，找出 cacheline 符号
    nsyms = sym_size // 16
    cacheline_idx = {}
    for idx in range(nsyms):
        soff = sym_off + idx * 16
        st_name = struct.unpack_from(">I", data, soff)[0]
        name = get_name(st_name) if st_name else ""
        if name.startswith("__lm_cacheline_"):
            cacheline_idx[idx] = int(name.split("_")[-1])

    # 重定位表，提取 R_MIPS_32 目标偏移
    r32_offsets = {}
    for idx in range(0, rel_size, 8):
        roff = struct.unpack_from(">I", data, rel_off + idx)[0]
        rinfo = struct.unpack_from(">I", data, rel_off + idx + 4)[0]
        rtype = rinfo & 0xFF
        sym_idx = rinfo >> 8
        if rtype == 2 and sym_idx in cacheline_idx:
            r32_offsets[roff] = cacheline_idx[sym_idx]

    r32_offsets.pop(0, None)

    print(f"[+] cacheline 符号: {len(cacheline_idx)} 个")
    print(f"[+] R_MIPS_32 目标: {len(r32_offsets)} 个唯一偏移")
    print()
    print(f'    {"#":>3s}  {"偏移":>8s}  {"符号":>22s}')
    print(f'    {"-" * 40}')

    for off, cidx in sorted(r32_offsets.items(), key=lambda item: item[1]):
        sym = f"__lm_cacheline_{cidx:02d}"
        print(f"    {cidx:3d}  0x{off:06x}  {sym:>22s}")

    print()
    return sorted(r32_offsets.items(), key=lambda item: item[1])


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "l11nk.o"
    analyze(path)
