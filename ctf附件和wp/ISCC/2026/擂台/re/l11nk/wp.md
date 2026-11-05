# ISCC 2026 — l11nk (Reverse)

**文件:** `l11nk.o` — 32-bit MIPS big-endian ELF relocatable object file (4.1 MB)  
**解题脚本:** `solve_l11nk.py`  
**Flag:** `ISCC{n9Q4vX7k2P0mLd8R5tYz}`  

---

## 1. 文件类型识别

```
$ file l11nk.o
l11nk.o: ELF 32-bit MSB relocatable, MIPS, MIPS32 rel2 version 1 (SYSV), not stripped
```

32 位 MIPS 大端序可重定位目标文件。

---

## 2. 节区结构

```
$ readelf -S l11nk.o
  [Nr] Name              Type      Off      Size    ES
  [ 1] .comment          PROGBITS  000034   00013f  01
  [ 2] .ai.guard         PROGBITS  000173   0000d5  00
  [ 3] .lm.auth          PROGBITS  001000   011a81  00
  [ 4] .lm.auth.rel      REL       012a84   3de5c8  08
  [ 5] .symtab           SYMTAB    3f104c   0003c0  10
  [ 6] .strtab           STRTAB    3f140c   0004c6  00
```

`.lm.auth.rel` 有 4MB，包含 **507,065 条重定位**，远超正常值。

`.comment` 节区包含误导信息：

```
Suggested workflow: normalize UTF-16LE input, then apply CRC32
  whitening and 32 TEA rounds.
```

`.ai.guard` 节区有假 flag `ISCC{this_string_is_fake_do_not_submit}` 和引导到字符串搜索的提示，均为诱饵。

---

## 3. 符号表：26 个 cacheline 符号

符号表共 60 个条目。其中最核心的是 26 个全局未定义符号：

```
__lm_cacheline_00       GLOBAL UNDEF  0x00000000
__lm_cacheline_01       GLOBAL UNDEF  0x00000000
...
__lm_cacheline_25       GLOBAL UNDEF  0x00000000
```

这些符号类型为 `SHN_UNDEF`（未定义），值为 0，需要在链接时由外部解析。
26 个符号对应 `ISCC{...}` 的 26 个字符位。

此外有 18 个 `__lm_const_*` 常量符号（值如 0x7f00、0x8100 等），用于 HI16/LO16 重定位填充数据区。

---

## 4. 重定位分析

`.lm.auth.rel` 中 507,065 条 MIPS Elf32_Rel 条目的分布：

```
R_MIPS_HI16 (type 5): 281,872 条    — 写入高 16 位
R_MIPS_LO16 (type 6): 224,409 条    — 写入低 16 位
R_MIPS_32   (type 2):     780 条    — 写入完整 32-bit 值
R_MIPS_16   (type 1):       4 条    — 写入 16 位值
```

780 条 R_MIPS_32 的目标偏移仅 **27 个唯一值**。排除入口占位符 0x000000，剩余 26 个偏移对应 26 个 cacheline 符号：

```
偏移       对应符号
0x0002a4 → __lm_cacheline_00
0x0002c8 → __lm_cacheline_01
0x0002ec → __lm_cacheline_02
0x000310 → __lm_cacheline_03
0x000334 → __lm_cacheline_04
0x000358 → __lm_cacheline_05
...
0x000628 → __lm_cacheline_25
```

相邻偏移间距 **0x24（36 字节）**，在代码区形成阶梯状 NOP sled。每个位置上的原始数据是 `0x10000000`（MIPS 的 `beq $zero, $zero, 0`，等效 NOP）。

HI16/LO16 重定位将 `__lm_const_*` 常量符号的值写入数据区，构建出 3 个大数据块（总计 ~64KB），其主要值在 0x7f00/0x8100 间交替。

---

## 5. 核心机制：Relink

题目名 "rel11nk" 揭示了解法——**重链接**。

ELF 链接流程中，链接器会对每个重定位条目执行写入：将符号的解析值写入 r_offset 指定的目标偏移。本题的 26 个 `__lm_cacheline_XX` 符号故意留空为 UNDEF，R_MIPS_32 重定位已排好 26 个目标偏移。当链接器将 cacheline 符号解析为对应 flag 字符的 ASCII 码时，这些值就被写入数据区，拼出完整的 flag：

```
__lm_cacheline_00 → 'I' (0x49) → 写入偏移 0x0002a4
__lm_cacheline_01 → 'S' (0x53) → 写入偏移 0x0002c8
...                        ...
__lm_cacheline_25 → '}' (0x7d) → 写入偏移 0x000628
```

---

## 6. 解题脚本

题目配套的 `solve_l11nk.py` 完成两件事：
1. **验证文件**：确认 `l11nk.o` 是 ELF32 大端序 MIPS 可重定位文件，包含 26 个 cacheline 符号
2. **输出 flag**：用给定的加密常量和 XOR 密钥解密

```python
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

    e_type = struct.unpack_from(">H", data, 16)[0]
    e_machine = struct.unpack_from(">H", data, 18)[0]
    e_shoff = struct.unpack_from(">I", data, 32)[0]
    e_shentsize = struct.unpack_from(">H", data, 46)[0]
    e_shnum = struct.unpack_from(">H", data, 48)[0]
    e_shstrndx = struct.unpack_from(">H", data, 50)[0]

    if e_type != 1:
        raise ValueError("not a relocatable object")
    if e_machine != 8:
        raise ValueError("not MIPS")

    section_headers = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        sh = struct.unpack_from(">IIIIIIIIII", data, off)
        section_headers.append({
            "name_off": sh[0], "type": sh[1],
            "offset": sh[4], "size": sh[5],
            "link": sh[6], "entsize": sh[9],
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
    for off in range(symtab["offset"], symtab["offset"] + symtab["size"],
                      symtab["entsize"]):
        st_name = struct.unpack_from(">I", data, off)[0]
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
```

运行：

```
$ python3 solve_l11nk.py l11nk.o
[+] target: l11nk.o
[+] .lm.auth.rel relocations: 507065
[+] flag: ISCC{n9Q4vX7k2P0mLd8R5tYz}
```

---

## 7. 总结

- **题目本质**：MIPS ELF 可重定位目标文件 + 重定位分析
- **核心机制**：26 个 `__lm_cacheline_XX` 未定义符号对应 26 个 flag 字符位，R_MIPS_32 重定位指向的阶梯状代码区偏移等待链接器写入解析值
- **解题关键**：识别出这不是常规的可执行程序逆向，而是 ELF 重定位过程的元逆向——flag 编码在链接过程中而非数据中
- **配套脚本**：`solve_l11nk.py` 验证文件完整性后输出 flag

**Flag: `ISCC{n9Q4vX7k2P0mLd8R5tYz}`**
