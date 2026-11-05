#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recover ALL entries of the VMC2 container (multi-entry encrypted bytecode)."""
import pefile, struct, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))

PATH = r"C:\Users\ASUS\WorkBuddy\yangcheng\vvmm\VVMM.exe"
pe = pefile.PE(PATH)
data = pe.get_memory_mapped_image()
cont = data[0x6f60:]           # container base
total = struct.unpack("<Q", data[0xbda0:0xbda8])[0] if len(data) > 0xbda8 else None
print(f"container size field @0x14000bda0 = {total}")

def fmix32(h):
    h ^= h >> 16; h = (h * 0x7feb352d) & 0xFFFFFFFF
    h ^= h >> 15; h = (h * 0x846ca68b) & 0xFFFFFFFF
    h ^= h >> 16
    return h

def vmhash(buf):
    h = None
    # r8 initialized to (key^seed) ^ 0x811c9dc5; we pass it in
    return None

version = cont[4]
print(f"version (entries) = {version}")
off = 8
for e in range(version):
    seed = struct.unpack("<I", cont[off:off+4])[0]
    key = cont[off+4]
    size = struct.unpack("<H", cont[off+6:off+8])[0]
    chk = struct.unpack("<I", cont[off+8:off+12])[0]
    enc = cont[off+12: off+12+size]
    print(f"\nentry {e}: off={off:#x} seed={seed:#010x} key={key:#04x} size={size} checksum={chk:#010x}")
    h0 = ((key ^ seed) ^ 0x811c9dc5) & 0xFFFFFFFF
    esi = (key + (seed >> 11)) & 0xFFFFFFFF
    out = bytearray()
    r11 = 0
    for i in range(size):
        c = r11 & 0xFFFFFFFF
        r11 = (r11 + 0x45d9f3b) & 0xFFFFFFFF
        c ^= (key ^ seed) & 0xFFFFFFFF
        c ^= 0x9e3779b9
        m = fmix32(c)
        shift = (i & 3) * 8
        k = (m >> shift) & 0xFF
        v = enc[i] ^ (esi & 0xFF) ^ k
        out.append(v)
        esi = (esi - 0x59) & 0xFFFFFFFF
    # checksum: modified FNV
    h = h0
    for b in out:
        h ^= b
        h = (h * 0x1000193) & 0xFFFFFFFF
        h ^= h >> 13
    ok = (size ^ h) == chk
    print(f"  checksum computed={size ^ h:#010x} match={ok}")
    print(f"  first bytes: {out[:16].hex(' ')}")
    if ok:
        open(f"entry{e}.bin", "wb").write(out)
        print(f"  -> saved entry{e}.bin")
    off += size + 12
    if off >= len(cont):
        break
