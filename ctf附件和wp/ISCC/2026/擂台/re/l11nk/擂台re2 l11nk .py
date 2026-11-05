#!/usr/bin/env python3
import struct
import subprocess
import shutil
import math
from collections import Counter

OBJ = "l11nk.o"
PATCHED = "l11nk_patched.o"
BIN = "l11nk_linked.bin"

data = bytearray(open(OBJ, "rb").read())

# ELF32 big-endian
assert data[:4] == b"\x7fELF"
assert data[4] == 1
assert data[5] == 2

hdr = struct.unpack(">HHIIIIIHHHHHH", data[16:52])
shoff = hdr[5]
shentsize = hdr[10]
shnum = hdr[11]
shstrndx = hdr[12]

sections = []
for i in range(shnum):
    off = shoff + i * shentsize
    sections.append(struct.unpack(">IIIIIIIIII", data[off:off + shentsize]))

shstr = sections[shstrndx]
shstr_data = data[shstr[4]:shstr[4] + shstr[5]]

def get_name(pos):
    end = shstr_data.find(b"\x00", pos)
    return shstr_data[pos:end].decode()

sec_by_name = {get_name(s[0]): s for s in sections}

rel = sec_by_name[".lm.auth.rel"]
rel_off = rel[4]
rel_size = rel[5]
rel_entsize = rel[9]

patched = 0

for i in range(rel_size // rel_entsize):
    pos = rel_off + i * rel_entsize
    r_offset, r_info = struct.unpack(">II", data[pos:pos + 8])
    r_type = r_info & 0xff

    # R_MIPS_16 = 1，题目故意放的坏 relocation
    if r_type == 1:
        data[pos + 4:pos + 8] = struct.pack(">I", r_info & ~0xff)
        patched += 1

open(PATCHED, "wb").write(data)

print("patched R_MIPS_16:", patched)

ld = shutil.which("ld.lld") or "/usr/local/swift/usr/bin/ld.lld"

defs = []
for i in range(26):
    defs.append(f"--defsym=__lm_cacheline_{i:02d}=0")

subprocess.check_call([
    ld,
    "-m", "elf32btsmip",
    "-Ttext=0x0",
    "--oformat=binary",
    *defs,
    "-o", BIN,
    PATCHED
])

linked = open(BIN, "rb").read()

# __lm_notice_blob = 0x1186c = 262 * 274
raw = linked[:0x1186c]

W = 262
H = 274

assert len(raw) == W * H

# 每一列取众数作为背景
col_mode = []
for c in range(W):
    cnt = Counter(raw[r * W + c] for r in range(H))
    col_mode.append(cnt.most_common(1)[0][0])

def mark(pos):
    return raw[pos] != col_mode[pos % W]

# unary 编码探针
probes = [0, 1] + list(range(3, 33, 2))

def get_value(pos):
    # 前两个点是同步位，所以减 2
    return sum(1 for o in probes if mark(pos + o)) - 2

# 两条轨迹
s1 = [get_value(4709 + i * 280) for i in range(76)]
s2 = [get_value(26693 + i * 282) for i in range(75)]

print("track1 =", "".join(format(x, "x") for x in s1))
print("track2 =", "".join(format(x, "x") for x in s2))

# 结尾 f 是终止符
assert s1[-1] == 15
assert s2[-1] == 15

a = s1[:-1]
b = s2[:-1]

print("sum track1 =", sum(a))
print("sum track2 =", sum(b))

# 两条轨迹分别表示 x / y 方向 run length
# 共 127 步，其中 63 个 1，64 个 0
bits = []

for i in range(max(len(a), len(b))):
    if i < len(b):
        bits += [0] * b[i]
    if i < len(a):
        bits += [1] * a[i]

assert len(bits) == 127
assert sum(bits) == 63

# 用组合数排名恢复 16 字节数据
ones = [i for i, v in enumerate(bits) if v]

rank = 0
for i, p in enumerate(ones):
    rank += math.comb(p, i + 1)

flag_body = rank.to_bytes(16, "big").hex()

print(f"ISCC{{{flag_body}}}")