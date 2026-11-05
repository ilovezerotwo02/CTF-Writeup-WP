#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CTFmobile Auto-solver (modified - automatic APK detection)
将 apk 放在脚本同目录下，双击运行或 python solve.py 即可。
也可手动指定：python solve.py yourfile.apk
"""

import sys
import os
import zipfile
import hashlib
import itertools
import re
from pathlib import Path
from collections import defaultdict

# ========== 常量定义 ==========
ASCII_MIN = 0x20
ASCII_MAX = 0x7E
PRINTABLE = bytes(range(ASCII_MIN, ASCII_MAX + 1))
MOD24 = 1 << 24
FNV_PRIME = 0x193
FNV_INV = pow(FNV_PRIME, -1, MOD24)
FNV_INIT = 0x1C9DC5
BASE64 = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

P4_TARGET = b"gGH52dkV"
DEFAULT_PIN_HEX = "a950927d04e7936e1ebdb7ee03f59f7a17adf1a3d962475e0c772b7899c4ff2d"
P1_HASH = "5475D82A7B1E7BAD1C0D50487C52AD17D8C7E5F1FF68E361ACC725CD301A5215"
P1_HEX = "43542E3D3660"   # CT.=6`


def err(msg: str):
    print(f"[-] {msg}")
    sys.exit(1)


def is_ascii6(data: bytes) -> bool:
    return len(data) == 6 and all(ASCII_MIN <= b <= ASCII_MAX for b in data)


def fnv24(data: bytes) -> int:
    h = FNV_INIT
    for b in data:
        h = ((h ^ b) * FNV_PRIME) & 0xFFFFFF
    return h


def xor_all(data: bytes) -> int:
    acc = 0
    for b in data:
        acc ^= b
    return acc & 0xFF


def rol24(v: int, n: int) -> int:
    n %= 24
    v &= 0xFFFFFF
    return ((v << n) | (v >> (24 - n))) & 0xFFFFFF


def ror24(v: int, n: int) -> int:
    n %= 24
    v &= 0xFFFFFF
    return ((v >> n) | (v << (24 - n))) & 0xFFFFFF


def int2hex6(v: int) -> str:
    return f"{v & 0xFFFFFF:06X}"


def atbash_hex6(s: str) -> str:
    res = []
    for c in s.upper():
        if '0' <= c <= '9':
            res.append(chr(ord('9') - ord(c) + ord('0')))
        elif 'A' <= c <= 'F':
            res.append(chr(ord('F') - ord(c) + ord('A')))
        else:
            raise ValueError(f"bad hex: {c}")
    return ''.join(res)


def p2_fold_target(p1: bytes) -> int:
    u1 = fnv24(p1)
    c = int(atbash_hex6(int2hex6(u1)), 16)
    b = ror24(c, 8)
    a = int(atbash_hex6(int2hex6(b)), 16)
    return (a ^ 0xAAAAAA) & 0xFFFFFF


def build_prefix_table() -> dict[tuple[int, int], list[bytes]]:
    tbl = defaultdict(list)
    for trip in itertools.product(PRINTABLE, repeat=3):
        pre = bytes(trip)
        tbl[(fnv24(pre), xor_all(pre))].append(pre)
    return tbl


def find_ascii6(fold: int, xor: int, prefixes: dict) -> list[bytes]:
    res = []
    for d3, d4, d5 in itertools.product(PRINTABLE, repeat=3):
        suff = bytes((d3, d4, d5))
        f = fold
        f = ((f * FNV_INV) & 0xFFFFFF) ^ d5
        f = ((f * FNV_INV) & 0xFFFFFF) ^ d4
        f = ((f * FNV_INV) & 0xFFFFFF) ^ d3
        px = xor ^ d3 ^ d4 ^ d5
        for pre in prefixes.get((f, px), []):
            res.append(pre + suff)
    return res


def derive_p4(p1: bytes, p2: bytes, p3: bytes, target: bytes) -> bytes | None:
    seed = (fnv24(p1) ^ rol24(fnv24(p2), 3) ^ rol24(fnv24(p3), 7)) & 0xFFFFFF
    shift = seed & 0x3F
    custom_b64 = bytes((BASE64[(i + shift) % 64]) for i in range(64))
    rev = {c: i for i, c in enumerate(custom_b64)}

    indices = []
    for i, ch in enumerate(target):
        if ch not in rev:
            return None
        indices.append((rev[ch] ^ ((seed >> ((i * 7) % 24)) & 0x3F)) & 0x3F)

    raw = bytearray()
    for blk in range(2):
        off = blk * 4
        val = (indices[off] << 18) | (indices[off+1] << 12) | (indices[off+2] << 6) | indices[off+3]
        raw.append((val >> 16) & 0xFF)
        raw.append((val >> 8) & 0xFF)
        raw.append(val & 0xFF)
    p4 = bytes(raw)
    return p4 if is_ascii6(p4) else None


def rc4_crypt(data: bytes, key: bytes) -> bytes:
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray()
    for b in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)


def load_apk(path: Path) -> tuple[bytes, bytes, list[bytes], bytes]:
    with zipfile.ZipFile(path, 'r') as zf:
        data = zf.read("assets/data.bin")
        flag = zf.read("assets/flag.enc")
        dex = b"".join(zf.read(n) for n in zf.namelist() if re.fullmatch(r'classes\d*\.dex', n))
        sos = [zf.read(n) for n in zf.namelist() if n.endswith("libscm_native.so")]
    if not sos:
        err("No libscm_native.so found in APK")
    return data, flag, sos, dex


def get_data_targets(dat: bytes, p1: bytes) -> dict[int, list[tuple[int, int]]]:
    want_hi = xor_all(p1)
    targets = defaultdict(list)
    for off in range(len(dat) - 2):
        raw = int.from_bytes(dat[off:off+3], 'little')
        dec = (raw ^ 0xDEADBE) & 0xFFFFFF
        if (dec >> 16) == want_hi:
            p2_xor = (dec >> 8) & 0xFF
            targets[p2_xor].append(((off ^ 0xAAAAAA) & 0xFFFFFF, dec & 0xFF))
    return targets


def solve(apk_path: Path):
    print(f"[*] Solving {apk_path.name} ...")
    data_bin, flag_enc, so_blobs, dex_blob = load_apk(apk_path)

    # 从 dex 中验证 p1 哈希（可选）
    # dex_hash = next((h.decode() for h in re.findall(rb'[0-9A-F]{64}', dex_blob) if h == P1_HASH.encode()), None)
    # if not dex_hash:
    #     err("p1 hash not found in dex")

    p1 = bytes.fromhex(P1_HEX)
    if hashlib.sha256(hashlib.sha256(p1).digest()).hexdigest().upper() != P1_HASH:
        err("p1 hash mismatch")

    # 获取 native 中的 PIN 哈希
    default_pin = bytes.fromhex(DEFAULT_PIN_HEX)
    pins = set()
    for blob in so_blobs:
        if default_pin in blob:
            pins.add(default_pin)
    if not pins:
        for blob in so_blobs:
            for i in range(len(blob) - 31):
                pins.add(blob[i:i+32])

    prefixes = build_prefix_table()
    p2_fold = p2_fold_target(p1)
    targets_by_xor = get_data_targets(data_bin, p1)

    p2_cache = {}
    p3_cache = {}
    checked = 0
    for p2_xor, data_targets in targets_by_xor.items():
        if p2_xor not in p2_cache:
            p2_cache[p2_xor] = find_ascii6(p2_fold, p2_xor, prefixes)
        for p2 in p2_cache[p2_xor]:
            for p3_fold, p3_xor in data_targets:
                ck = (p3_fold, p3_xor)
                if ck not in p3_cache:
                    p3_cache[ck] = find_ascii6(p3_fold, p3_xor, prefixes)
                for p3 in p3_cache[ck]:
                    p4 = derive_p4(p1, p2, p3, P4_TARGET)
                    if not p4:
                        continue
                    key = p1 + p2 + p3 + p4
                    checked += 1
                    if hashlib.sha256(key).digest() not in pins:
                        continue
                    flag = rc4_crypt(flag_enc, key).decode('utf-8')
                    print(f"p1 = {p1.decode('ascii')}")
                    print(f"p2 = {p2.decode('ascii')}")
                    print(f"p3 = {p3.decode('ascii')}")
                    print(f"p4 = {p4.decode('ascii')}")
                    print(f"key = {key.decode('ascii')}")
                    print(f"flag = {flag}")
                    print(f"checked = {checked}")
                    return
    print(f"[-] No valid key found (checked {checked})")


def find_apk() -> Path:
    # 优先使用命令行参数
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        if p.exists():
            return p
        err(f"指定的 APK 不存在: {p}")

    # 默认在当前脚本所在目录下查找
    script_dir = Path(__file__).resolve().parent

    # 尝试默认文件名
    default = script_dir / "attachment-7.apk"
    if default.exists():
        return default

    # 自动扫描所有 .apk 文件
    apks = list(script_dir.glob("*.apk"))
    if not apks:
        # 再尝试当前工作目录
        apks = list(Path.cwd().glob("*.apk"))
    if not apks:
        err("未找到任何 APK 文件，请将 APK 放在脚本同目录或命令行指定。")
    if len(apks) > 1:
        print(f"[*] 发现多个 APK: {[a.name for a in apks]}，默认使用第一个: {apks[0].name}")
    return apks[0]


if __name__ == "__main__":
    apk_path = find_apk()
    solve(apk_path)