from pathlib import Path

import analyze_l11nk as core


R_MIPS_32 = 2
WRITEUP_FLAG = "ISCC{n9Q4vX7k2P0mLd8R5tYz}"


def gather_unique_r32_slots(symbols, relocs):
    slots = {}
    zero_hits = {}

    for rel in relocs:
        if rel["type"] != R_MIPS_32:
            continue
        name = symbols[rel["sym_idx"]]["name"]
        if not name.startswith("__lm_cacheline_"):
            continue
        if rel["offset"] == 0:
            zero_hits.setdefault(name, 0)
            zero_hits[name] += 1
            continue
        slots[name] = rel["offset"]

    ordered = sorted(slots.items(), key=lambda item: item[1])
    return ordered, zero_hits


def simulate_writeup_flag(elf_path, flag):
    section_data, symbols, relocs = core.load_elf(elf_path)
    overrides = {
        f"__lm_cacheline_{idx:02d}": ord(ch)
        for idx, ch in enumerate(flag)
    }
    data = core.apply_relocations(section_data, symbols, relocs, overrides)
    ordered, zero_hits = gather_unique_r32_slots(symbols, relocs)

    rows = []
    for idx, (name, off) in enumerate(ordered):
        word = core.read_u32_be(data, off)
        rows.append(
            {
                "index": idx,
                "symbol": name,
                "offset": off,
                "char": flag[idx],
                "word": word,
                "bytes": data[off : off + 4].hex(),
            }
        )

    return ordered, zero_hits, rows


def main():
    elf_path = Path(r"D:\00DownLoadings\l11nk.o")
    ordered, zero_hits, rows = simulate_writeup_flag(elf_path, WRITEUP_FLAG)

    print("[*] Unique non-zero R_MIPS_32 slots:")
    for idx, (name, off) in enumerate(ordered):
        print(f"    {idx:02d} {name} -> 0x{off:04x}")

    print()
    print("[*] Offset 0 repeated R_MIPS_32 hits per cacheline symbol:")
    for name in sorted(zero_hits):
        print(f"    {name}: {zero_hits[name]}")

    print()
    print("[*] Replaying the writeup with its published flag:")
    for row in rows:
        print(
            f"    {row['index']:02d} {row['symbol']} @ 0x{row['offset']:04x} "
            f"char={row['char']!r} word=0x{row['word']:08x} bytes={row['bytes']}"
        )

    print()
    print("[*] Note:")
    print("    The writeup's cacheline-order mapping is reproducible.")
    print("    Its 'read data[off + 3] directly as ASCII' claim does not match the file.")
    print("    These slots are still transformed by many other relocations at the same offsets.")


if __name__ == "__main__":
    main()
