#!/usr/bin/env python3
"""
Simulate lld linking of l11nk.o:
  1. Patch R_MIPS_16 → R_MIPS_NONE
  2. Apply all HI16/LO16/R_MIPS_32 relocations to .lm.auth data
  3. Extract image from first 0x1186c bytes
  4. Decode flag via combinatorial ranking
"""

import struct
import math
from collections import Counter
from pathlib import Path

OBJ = Path("l11nk.o")

# ============================================================
# Step 1: Parse ELF
# ============================================================
data = bytearray(OBJ.read_bytes())

assert data[:4] == b"\x7fELF"
assert data[4] == 1   # 32-bit
assert data[5] == 2   # big-endian

e_type, e_machine = struct.unpack_from(">HH", data, 16)
assert e_type == 1     # relocatable
assert e_machine == 8  # MIPS

e_shoff = struct.unpack_from(">I", data, 0x20)[0]
e_shentsize = struct.unpack_from(">H", data, 0x2E)[0]
e_shnum = struct.unpack_from(">H", data, 0x30)[0]
e_shstrndx = struct.unpack_from(">H", data, 0x32)[0]

# Parse section headers
sections = []
for i in range(e_shnum):
    off = e_shoff + i * e_shentsize
    s = struct.unpack_from(">IIIIIIIIII", data, off)
    sections.append(s)

# Read section name string table
shstr = sections[e_shstrndx]
shstrtab = data[shstr[4]:shstr[4] + shstr[5]]

def get_name(off):
    end = shstrtab.find(b"\x00", off)
    if end == -1: end = len(shstrtab)
    return shstrtab[off:end].decode("latin1")

sec_by_name = {}
for s in sections:
    name = get_name(s[0])
    sec_by_name[name] = s

lm_auth = sec_by_name[".lm.auth"]
lm_auth_off = lm_auth[4]   # file offset
lm_auth_size = lm_auth[5]

rel = sec_by_name[".lm.auth.rel"]
rel_off = rel[4]
rel_size = rel[5]
rel_entsize = rel[9]

symtab_s = sec_by_name[".symtab"]
strtab_s = sec_by_name[".strtab"]
strtab_data = data[strtab_s[4]:strtab_s[4] + strtab_s[5]]

def get_str(off):
    end = strtab_data.find(b"\x00", off)
    if end == -1: end = len(strtab_data)
    return strtab_data[off:end].decode("latin1")

# Build symbol table
symbols = []
for i in range(symtab_s[5] // symtab_s[9]):
    off = symtab_s[4] + i * 16
    st_name, st_value, st_size = struct.unpack_from(">III", data, off)
    st_info, st_other, st_shndx = data[off+12], data[off+13], struct.unpack_from(">H", data, off+14)[0]
    name = get_str(st_name) if st_name else ""
    symbols.append({
        "idx": i, "name": name, "value": st_value,
        "size": st_size, "shndx": st_shndx,
        "bind": st_info >> 4
    })

# Symbol lookup
def find_sym(idx):
    for s in symbols:
        if s["idx"] == idx: return s
    return None

# ============================================================
# Step 2: Patch R_MIPS_16 → R_MIPS_NONE
# ============================================================
patched_count = 0
for i in range(rel_size // rel_entsize):
    pos = rel_off + i * rel_entsize
    r_info = struct.unpack_from(">I", data, pos + 4)[0]
    r_type = r_info & 0xff
    if r_type == 1:  # R_MIPS_16
        data[pos + 4:pos + 8] = struct.pack(">I", r_info & ~0xff)
        patched_count += 1

print(f"patched R_MIPS_16: {patched_count}")

# ============================================================
# Step 3: Apply relocations to .lm.auth data
# ============================================================
lm_data = bytearray(data[lm_auth_off:lm_auth_off + lm_auth_size])

R_MIPS_32 = 2
R_MIPS_HI16 = 5
R_MIPS_LO16 = 6

hi16_count = 0
lo16_count = 0
r32_count = 0

for i in range(rel_size // rel_entsize):
    pos = rel_off + i * rel_entsize
    r_offset, r_info = struct.unpack_from(">II", data, pos)
    r_type = r_info & 0xff
    sym_idx = r_info >> 8

    sym = find_sym(sym_idx)
    if not sym:
        continue
    sym_val = sym["value"]

    if r_type == R_MIPS_32:
        # Write symbol value (32-bit) at target offset
        struct.pack_into(">I", lm_data, r_offset, sym_val)
        r32_count += 1

    elif r_type == R_MIPS_HI16:
        # Read current value, extract upper 16 bits as addend
        cur = struct.unpack_from(">I", lm_data, r_offset)[0]
        addend_hi = (cur >> 16) & 0xFFFF
        result = ((addend_hi << 16) + sym_val + 0x8000) >> 16
        cur = (cur & 0xFFFF) | ((result & 0xFFFF) << 16)
        struct.pack_into(">I", lm_data, r_offset, cur)
        hi16_count += 1

    elif r_type == R_MIPS_LO16:
        cur = struct.unpack_from(">I", lm_data, r_offset)[0]
        addend_lo = cur & 0xFFFF
        result = (addend_lo + sym_val) & 0xFFFF
        cur = (cur & 0xFFFF0000) | result
        struct.pack_into(">I", lm_data, r_offset, cur)
        lo16_count += 1

print(f"applied HI16: {hi16_count} LO16: {lo16_count} R_MIPS_32: {r32_count}")

# ============================================================
# Step 4: Extract image from linked data
# ============================================================
# The wp says linked[:0x1186c] forms the image
# 0x1186c = 71788 = 262 * 274
raw = lm_data[:0x1186c]
W, H = 262, 274

if len(raw) != W * H:
    print(f"WARNING: raw len = {len(raw)}, expected {W*H}")
    # Try to pad or truncate
    raw = raw[:W*H] if len(raw) >= W*H else raw + b"\x00" * (W*H - len(raw))

# Pad to exact size
if len(raw) < W * H:
    raw = raw + b"\x00" * (W * H - len(raw))
raw = bytes(raw)

# Verify some stats
vals = set(raw)
print(f"linked data bytes: unique={len(vals)} range=[{min(vals)}, {max(vals)}]")

# ============================================================
# Step 5: Column mode background removal
# ============================================================
col_mode = []
for c in range(W):
    cnt = Counter(raw[r * W + c] for r in range(H))
    col_mode.append(cnt.most_common(1)[0][0])

def mark(pos):
    return raw[pos] != col_mode[pos % W]

marks = sum(1 for i in range(len(raw)) if mark(i))
print(f"non-background pixels: {marks}/{len(raw)} ({marks/len(raw)*100:.1f}%)")

# ============================================================
# Step 6: Track detection with unary probes
# ============================================================
probes = [0, 1] + list(range(3, 33, 2))

def get_value(pos):
    return sum(1 for o in probes if mark(pos + o)) - 2

# Try the wp's claimed positions
print()
print("=== Track decoding ===")
s1 = [get_value(4709 + i * 280) for i in range(76)]
s2 = [get_value(26693 + i * 282) for i in range(75)]

print("track1 =", "".join(format(x, "x") if x >= 0 else "?" for x in s1))
print("track2 =", "".join(format(x, "x") if x >= 0 else "?" for x in s2))

# Check terminator
if s1[-1] != 15 or s2[-1] != 15:
    print(f"WARNING: terminator check failed: s1[-1]={s1[-1]} s2[-1]={s2[-1]}")
    # Try to adjust by scanning for proper positions
else:
    print("Terminator check: OK")

a = [x for x in s1[:-1] if x >= 0]
b = [x for x in s2[:-1] if x >= 0]

print(f"sum track1 (no term) = {sum(a)}")
print(f"sum track2 (no term) = {sum(b)}")

# ============================================================
# Step 7: Run-length → bits → combinatorial rank
# ============================================================
bits = []
for i in range(max(len(a), len(b))):
    if i < len(b):
        bits += [0] * b[i]
    if i < len(a):
        bits += [1] * a[i]

print(f"bits len={len(bits)} sum={sum(bits)}")

if len(bits) == 127 and sum(bits) == 63:
    ones = [i for i, v in enumerate(bits) if v]
    rank = 0
    for i, p in enumerate(ones):
        rank += math.comb(p, i + 1)
    flag_body = rank.to_bytes(16, "big").hex()
    print(f"\nFLAG: ISCC{{{flag_body}}}")
else:
    print("Bit constraints not met, cannot decode flag.")
    print("Trying to search for correct track parameters...")
