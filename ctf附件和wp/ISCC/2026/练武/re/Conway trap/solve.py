#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conway's Trap 逆向求解脚本
用法: python3 solve.py "Conway's Trap.exe"
"""
import re
import sys
from pathlib import Path


def rotl(x, n=1):
    """8-bit rotate left"""
    x &= 0xFF
    return ((x << n) | (x >> (8 - n))) & 0xFF


def rotr(x, n=1):
    """8-bit rotate right"""
    x &= 0xFF
    return ((x >> n) | (x << (8 - n))) & 0xFF


def forward(state):
    """16-byte state forward transformation (sub_401990):
    pair: a' = (a+b)&FF, b' = rotl((a+b)^b,1), then rotate whole state left by 1 byte"""
    buf = list(state)
    for i in range(0, 16, 2):
        x, y = buf[i], buf[i + 1]
        s = (x + y) & 0xFF
        buf[i] = s
        buf[i + 1] = rotl(s ^ y)
    return bytes(buf[1:] + buf[:1])


def backward(state):
    """Reverse of forward transformation"""
    tmp = bytearray(16)
    tmp[0] = state[15]
    tmp[1:] = state[:15]
    out = bytearray(16)
    for i in range(0, 16, 2):
        a, b = tmp[i], tmp[i + 1]
        y = a ^ rotr(b)
        x = (a - y) & 0xFF
        out[i], out[i + 1] = x, y
    return bytes(out)


def locate_seed(raw):
    """Extract the 32-char hex string = seed target after 5 rounds"""
    for m in re.finditer(rb"(?<![0-9A-Fa-f])([0-9A-Fa-f]{32})\x00", raw):
        d = bytes.fromhex(m.group(1).decode())
        if len(d) == 16:
            return d
    raise RuntimeError("seed target not found")


def locate_checktable(raw):
    """Extract hidden constants XOR'ed with 0xCC from sub_401D00"""
    pat = re.compile(
        rb"\xc7\x45\xe4(.{4})"
        rb"\xc7\x45\xe8(.{4})"
        rb"\xc7\x45\xec(.{4})"
        rb"\xc7\x45\xf0(.{4})"
        rb"\xc7\x45\xf4(.{4})"
        rb"\x66\xc7\x45\xf8(.{2})"
        rb"\xc6\x45\xfa(.)",
        re.S)
    m = pat.search(raw)
    if not m:
        raise RuntimeError("check table not found")
    packed = b"".join(m.groups())
    return bytes(b ^ 0xCC for b in packed)


def recover(seed_bytes, table):
    """Decode the flag body using seed and check table"""
    n = len(table)
    result = []
    for idx, val in enumerate(table):
        t = rotr(val ^ 0xAA, 3)
        t = (t - (idx * n)) & 0xFF
        result.append(seed_bytes[idx & 0x0F] ^ t)
    return bytes(result).decode("ascii")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {Path(sys.argv[0]).name} <exe_file>")
        sys.exit(1)

    blob = Path(sys.argv[1]).read_bytes()

    # Step 1: get seed target
    target = locate_seed(blob)
    print(f"[+] Seed target: {target.hex()}")

    # Step 2: reverse 5 rounds
    seed = target
    for _ in range(5):
        seed = backward(seed)
    print(f"[+] Original seed: {seed.hex()}")

    # verify
    v = seed
    for _ in range(5):
        v = forward(v)
    assert v == target, "round-trip check failed"

    # Step 3: extract hidden check table
    ct = locate_checktable(blob)
    print(f"[+] Check table: {ct.hex()} ({len(ct)} bytes)")

    # Step 4: decode flag
    flag_body = recover(seed, ct)
    print(f"[+] Flag body: {flag_body}")
    print(f"[+] ISCC{{{flag_body}}}")
