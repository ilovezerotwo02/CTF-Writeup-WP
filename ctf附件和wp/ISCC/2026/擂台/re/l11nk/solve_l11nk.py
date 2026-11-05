#!/usr/bin/env python3
import re
import struct
import sys
from pathlib import Path


ENCRYPTED = bytes([
    19, 56, 63, 206, 229, 193, 249, 128, 214, 133, 92, 34, 77,
    5, 24, 105, 7, 55, 232, 165, 252, 138, 164, 184, 136, 126,
])

FLAG_RE = re.compile(r"ISCC\{[ -~]{20}\}")


def cstr(blob: bytes, off: int) -> str:
    end = blob.find(b"\x00", off)
    if end == -1:
        end = len(blob)
    return blob[off:end].decode("latin1")


def parse_elf32_be(path: Path):
    data = path.read_bytes()
    if len(data) < 52 or data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")
    if data[4] != 1:
        raise ValueError("not ELF32")
    if data[5] != 2:
        raise ValueError("not big-endian ELF")

    unpack16 = lambda off: struct.unpack_from(">H", data, off)[0]
    unpack32 = lambda off: struct.unpack_from(">I", data, off)[0]

    e_type = unpack16(16)
    e_machine = unpack16(18)
    e_shoff = unpack32(32)
    e_shentsize = unpack16(46)
    e_shnum = unpack16(48)
    e_shstrndx = unpack16(50)

    if e_type != 1:
        raise ValueError("not a relocatable object")
    if e_machine != 8:
        raise ValueError("not MIPS")

    section_headers = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh = struct.unpack_from(">IIIIIIIIII", data, off)
        section_headers.append({
            "name_off": sh[0],
            "type": sh[1],
            "offset": sh[4],
            "size": sh[5],
            "link": sh[6],
            "entsize": sh[9],
        })

    shstr = section_headers[e_shstrndx]
    shstrtab = data[shstr["offset"]:shstr["offset"] + shstr["size"]]
    for sh in section_headers:
        sh["name"] = cstr(shstrtab, sh["name_off"])

    sections = {sh["name"]: sh for sh in section_headers}
    for required in (".lm.auth", ".lm.auth.rel", ".symtab", ".strtab"):
        if required not in sections:
            raise ValueError(f"missing section: {required}")

    rel = sections[".lm.auth.rel"]
    rel_count = rel["size"] // rel["entsize"]
    if rel_count < 100000:
        raise ValueError("relocation table is smaller than expected")

    symtab = sections[".symtab"]
    strtab = sections[".strtab"]
    names = data[strtab["offset"]:strtab["offset"] + strtab["size"]]
    symbols = []
    for off in range(symtab["offset"], symtab["offset"] + symtab["size"], symtab["entsize"]):
        st_name = unpack32(off)
        symbols.append(cstr(names, st_name))

    cacheline_names = [f"__lm_cacheline_{i:02d}" for i in range(26)]
    missing = [name for name in cacheline_names if name not in symbols]
    if missing:
        raise ValueError("missing input symbols: " + ", ".join(missing))

    return rel_count


def decrypt_flag() -> str:
    flag = bytes(
        c ^ ((0x5A + 17 * i) & 0xFF)
        for i, c in enumerate(ENCRYPTED)
    ).decode("latin1")
    if not FLAG_RE.fullmatch(flag):
        raise ValueError("decrypted text does not match flag format")
    return flag


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("l11nk.o")
    rel_count = parse_elf32_be(target)
    flag = decrypt_flag()
    print(f"[+] target: {target}")
    print(f"[+] .lm.auth.rel relocations: {rel_count}")
    print(f"[+] flag: {flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
