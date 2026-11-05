#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conway's trap 动态求解脚本
用法：python3 solve_conway_dynamic.py "Conway's Trap.exe"
"""
import re
import sys
from pathlib import Path


def rol8(x: int, n: int = 1) -> int:
    x &= 0xff
    return ((x << n) | (x >> (8 - n))) & 0xff


def ror8(x: int, n: int = 1) -> int:
    x &= 0xff
    return ((x >> n) | (x << (8 - n))) & 0xff


def forward_round(state: bytes) -> bytes:
    """对应程序中的 0x401990 变换。"""
    s = list(state)
    for i in range(0, 16, 2):
        a = s[i]
        b = s[i + 1]
        t = (a + b) & 0xff
        s[i] = t
        s[i + 1] = rol8(t ^ b, 1)
    return bytes(s[1:] + s[:1])  # 整体左移 1 字节


def inverse_round(state: bytes) -> bytes:
    """逆向 0x401990 变换。"""
    # 先逆整体左移 1 字节
    z = bytearray(16)
    z[0] = state[15]
    z[1:] = state[:15]

    out = bytearray(16)
    for i in range(0, 16, 2):
        t0 = z[i]
        t1 = z[i + 1]
        b = t0 ^ ror8(t1, 1)
        a = (t0 - b) & 0xff
        out[i] = a
        out[i + 1] = b
    return bytes(out)


def extract_seed_target(data: bytes) -> bytes:
    """提取程序中用于 seed 校验的 32 位十六进制目标串。"""
    # 程序中 seed 目标是一个独立的 32 字节 hex 字符串，以 \x00 结束。
    cands = []
    for m in re.finditer(rb"(?<![0-9A-Fa-f])([0-9A-Fa-f]{32})\x00", data):
        cands.append(m.group(1).decode())

    if not cands:
        raise RuntimeError("没有找到 32 字节 seed 目标 hex 字符串")

    # 一般只有一个独立的 32 字节 hex 串；若有多个，优先选择能正常解析的第一个。
    for s in cands:
        try:
            raw = bytes.fromhex(s)
            if len(raw) == 16:
                return raw
        except ValueError:
            pass
    raise RuntimeError("找到的 seed 目标无法按 hex 解析")


def extract_flag_check_bytes(data: bytes) -> bytes:
    """提取隐藏校验函数 0x401d00 中的 23 字节密文常量，并 XOR 0xcc 还原校验表。"""
    pat = re.compile(
        rb"\xc7\x45\xe4(.{4})"
        rb"\xc7\x45\xe8(.{4})"
        rb"\xc7\x45\xec(.{4})"
        rb"\xc7\x45\xf0(.{4})"
        rb"\xc7\x45\xf4(.{4})"
        rb"\x66\xc7\x45\xf8(.{2})"
        rb"\xc6\x45\xfa(.)",
        re.S,
    )
    m = pat.search(data)
    if not m:
        raise RuntimeError("没有找到隐藏 flag 校验常量")

    enc = b"".join(m.groups())
    return bytes(x ^ 0xCC for x in enc)


def solve_seed(seed_target: bytes, rounds: int = 5) -> bytes:
    seed = seed_target
    for _ in range(rounds):
        seed = inverse_round(seed)

    # 校验一下逆推结果确实能回到目标。
    test = seed
    for _ in range(rounds):
        test = forward_round(test)
    if test != seed_target:
        raise RuntimeError("seed 逆推校验失败")
    return seed


def solve_flag_inner(seed: bytes, check_bytes: bytes) -> str:
    """
    还原大括号中的 flag 内容。
    隐藏校验关系：
        rol8(((seed[i&0xf] ^ ch) + i*L) & 0xff, 3) ^ 0xaa == check[i]
    其中 L=0x17，也就是 check_bytes 长度。
    """
    L = len(check_bytes)
    out = bytearray()
    for i, chk in enumerate(check_bytes):
        t = (ror8(chk ^ 0xAA, 3) - ((i * L) & 0xFF)) & 0xFF
        out.append(seed[i & 0x0F] ^ t)
    return out.decode("ascii")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"用法: {Path(sys.argv[0]).name} <Conway's Trap.exe>")
        sys.exit(1)

    data = Path(sys.argv[1]).read_bytes()
    seed_target = extract_seed_target(data)
    check_bytes = extract_flag_check_bytes(data)

    seed = solve_seed(seed_target, rounds=5)
    flag_inner = solve_flag_inner(seed, check_bytes)
    flag = f"ISCC{{{flag_inner}}}"

    print("seed_target:", seed_target.hex())
    print("seed       :", seed.hex())
    print("flag       :", flag)


if __name__ == "__main__":
    main()
