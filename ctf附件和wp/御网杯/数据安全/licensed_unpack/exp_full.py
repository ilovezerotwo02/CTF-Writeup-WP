from __future__ import annotations

import argparse
import struct
import zlib
from pathlib import Path

from Crypto.Cipher import Blowfish


OUTER_PAYLOAD_OFF = 0x25B
OUTER_PAYLOAD_LEN = 0x245
OUTER_XOR_KEY = 0xCE

BF_KEY_LEN = 16
BF_CT_LEN = 48


def unpack_outer(original: Path) -> bytes:
    data = original.read_bytes()
    blob = data[OUTER_PAYLOAD_OFF : OUTER_PAYLOAD_OFF + OUTER_PAYLOAD_LEN]
    if len(blob) != OUTER_PAYLOAD_LEN:
        raise ValueError("外层载荷长度不足，无法按预期范围提取")

    xored = bytes(b ^ OUTER_XOR_KEY for b in blob)
    if xored[:3] != b"\x00\x78\xDA":
        raise ValueError(
            f"外层异或后头部异常，期望 00 78 DA，实际为 {xored[:3].hex(' ')}"
        )

    inner = zlib.decompress(xored[1:])
    if inner[:2] != b"MZ":
        raise ValueError("zlib 解出的内层数据不是 PE 文件")
    return inner


def u16(buf: bytes, off: int) -> int:
    return struct.unpack_from("<H", buf, off)[0]


def u32(buf: bytes, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


def rva_to_raw(buf: bytes, rva: int) -> tuple[int, str]:
    pe = u32(buf, 0x3C)
    number_of_sections = u16(buf, pe + 6)
    size_of_optional_header = u16(buf, pe + 20)
    section_table = pe + 24 + size_of_optional_header

    for i in range(number_of_sections):
        sec = section_table + i * 40
        name = buf[sec : sec + 8].rstrip(b"\x00").decode(errors="replace")
        virtual_size = u32(buf, sec + 8)
        virtual_address = u32(buf, sec + 12)
        raw_size = u32(buf, sec + 16)
        raw_ptr = u32(buf, sec + 20)
        if virtual_address <= rva < virtual_address + max(virtual_size, raw_size):
            return raw_ptr + (rva - virtual_address), name

    raise RuntimeError(f"RVA 0x{rva:X} 不在任何节区中")


def extract_blowfish_material(inner: bytes) -> tuple[bytes, bytes, dict[str, int | str]]:
    pe = u32(inner, 0x3C)
    optional = pe + 24
    data_directories = optional + 0x60

    clr_dir = data_directories + 14 * 8
    clr_rva = u32(inner, clr_dir)
    clr_size = u32(inner, clr_dir + 4)
    clr_raw, clr_sec = rva_to_raw(inner, clr_rva)

    metadata_rva = u32(inner, clr_raw + 8)
    metadata_size = u32(inner, clr_raw + 12)
    metadata_raw, metadata_sec = rva_to_raw(inner, metadata_rva)

    key_off = metadata_raw + metadata_size
    ct_off = key_off + BF_KEY_LEN

    key = inner[key_off : key_off + BF_KEY_LEN]
    ct = inner[ct_off : ct_off + BF_CT_LEN]

    if len(key) != BF_KEY_LEN or len(ct) != BF_CT_LEN:
        raise ValueError("内层 PE 中的 key/ct 长度异常")

    info = {
        "clr_rva": clr_rva,
        "clr_raw": clr_raw,
        "clr_sec": clr_sec,
        "clr_size": clr_size,
        "metadata_rva": metadata_rva,
        "metadata_raw": metadata_raw,
        "metadata_sec": metadata_sec,
        "metadata_size": metadata_size,
        "key_off": key_off,
        "ct_off": ct_off,
    }
    return key, ct, info


def decrypt_flag(key: bytes, ct: bytes) -> str:
    pt = Blowfish.new(key, Blowfish.MODE_ECB).decrypt(ct)
    return pt.rstrip(b"\x00").decode()


def main() -> None:
    parser = argparse.ArgumentParser(description="从原始 licensed.exe 一步恢复 flag")
    parser.add_argument("input", type=Path, help="原始 licensed.exe")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="可选：保存解出的内层 PE",
    )
    args = parser.parse_args()

    inner = unpack_outer(args.input)
    if args.output is not None:
        args.output.write_bytes(inner)

    key, ct, info = extract_blowfish_material(inner)
    flag = decrypt_flag(key, ct)

    print(f"[*] outer payload : off=0x{OUTER_PAYLOAD_OFF:X}, len=0x{OUTER_PAYLOAD_LEN:X}, xor=0x{OUTER_XOR_KEY:02X}")
    print(f"[*] inner size     : {len(inner)} bytes")
    if args.output is not None:
        print(f"[*] inner saved    : {args.output}")

    print(
        f"[*] CLR header     : RVA=0x{info['clr_rva']:X}, raw=0x{info['clr_raw']:X}, "
        f"section={info['clr_sec']}, size=0x{info['clr_size']:X}"
    )
    print(
        f"[*] CLR metadata   : RVA=0x{info['metadata_rva']:X}, raw=0x{info['metadata_raw']:X}, "
        f"section={info['metadata_sec']}, size=0x{info['metadata_size']:X}"
    )
    print(f"[*] key offset     : 0x{info['key_off']:X}")
    print(f"[*] ct offset      : 0x{info['ct_off']:X}")
    print(f"[*] key(hex)       : {key.hex()}")
    print(f"[*] ct(hex)        : {ct.hex()}")
    print(f"[+] flag           : {flag}")


if __name__ == "__main__":
    main()
