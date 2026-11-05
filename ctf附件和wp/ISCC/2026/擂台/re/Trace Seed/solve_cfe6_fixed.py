import struct, sys
from z3 import *

def ROL64(v, s):
    s &= 0x3F; v &= 0xFFFFFFFFFFFFFFFF
    return ((v << s) | (v >> (64 - s))) & 0xFFFFFFFFFFFFFFFF

def ROL64_z3(v, s):
    s = s & 0x3F; return (v << s) | LShR(v, 64 - s)

def sub_1DE72(a1):
    a1 &= 0xFFFFFFFFFFFFFFFF
    x = (a1 - 0x61C8864680B583EB) & 0xFFFFFFFFFFFFFFFF
    x = (0xBF58476D1CE4E5B9 * x) & 0xFFFFFFFFFFFFFFFF
    x ^= (x >> 30)
    x = (0xBF58476D1CE4E5B9 * x) & 0xFFFFFFFFFFFFFFFF
    x ^= (x >> 27)
    x = (0x94D049BB133111EB * x) & 0xFFFFFFFFFFFFFFFF
    x ^= (x >> 31)
    return x

with open("/mnt/d/桌面/wp/擂台/re/Trace Seed/trace", "rb") as f:
    data = f.read()

unk_C0E8 = struct.unpack_from("<4Q", data, 0xC0E8)
v0 = 0x243F6A8885A308D3; v2 = 13; v3 = 0
for idx in range(4):
    v0 = sub_1DE72(v0 ^ ROL64(v3 ^ unk_C0E8[idx], v2))
    v3 = (v3 - 0x2E4AB5CD2E6D12FD) & 0xFFFFFFFFFFFFFFFF
    v2 += 11
SEED = v0 ^ 0xC0DEC0FFEEBADF00

v20 = [sub_1DE72(SEED ^ c) for c in [0x6A09E667F3BCC909, 0xBB67AE8584CAA73B, 0x3C6EF372FE94F82B, 0xA54FF53A5F1D36F1]]
qword_C088 = struct.unpack_from("<4Q", data, 0xC088)

def ROR64(v, s):
    s &= 0x3F; v &= 0xFFFFFFFFFFFFFFFF
    return ((v >> s) | (v << (64 - s))) & 0xFFFFFFFFFFFFFFFF

T_C = 0x83C43F18D6EB1975
C0 = 0x3141592653589793
REM_c = [(17 + i * 13) & 0x3F for i in range(40)]

# Fix: C088 uses (i+1) & 3 due to post-increment
C088_idx = lambda i: qword_C088[(i + 1) & 3]

# First verify with known values
def cfe6_fixed(inp):
    v = C0
    for i in range(40):
        term = ROL64(C088_idx(i), i) + i*256 + inp[i]
        v9 = ROL64(0xD6E8FEB86659FD93 * (v ^ term), REM_c[i])
        v = v9 ^ (v9 >> 29)
    return v

# Test with the E5B5 solution
known = [73,83,67,67,123,75,41,61,67,110,106,39,55,118,64,101,42,108,100,45,92,54,40,89,53,126,64,102,59,74,112,90,39,60,110,53,117,123,45,125]
print("Fixed CFE6 of known E5B5 sol:", hex(cfe6_fixed(known)))
print("Target:", hex(T_C))

# Now run Z3 with FIXED CFE6 constraint
print("\nSolving CFE6 with FIXED qword_C088 indexing...")
s = Solver()
s.set("timeout", 120000)
inp = [BitVec("b%d" % i, 32) for i in range(40)]
for i in range(40):
    s.add(inp[i] >= 32, inp[i] <= 126)
s.add(inp[0] == 73, inp[1] == 83, inp[2] == 67, inp[3] == 67)
s.add(inp[4] == 123, inp[39] == 125)

vc = BitVecVal(C0, 64)
for i in range(40):
    term = ROL64_z3(BitVecVal(qword_C088[(i+1) & 3], 64), i) + BitVecVal(i * 256, 64) + ZeroExt(32, inp[i])
    v9 = ROL64_z3(BitVecVal(0xD6E8FEB86659FD93, 64) * (vc ^ term), REM_c[i])
    vc = v9 ^ LShR(v9, 29)
s.add(vc == BitVecVal(T_C, 64))

print("Solving...")
if s.check() == sat:
    m = s.model()
    flag = bytes([m.eval(inp[i]).as_long() for i in range(40)])
    print("FIXED CFE6 sol:", repr(flag))
    print("String:", flag.decode())
else:
    print("UNSAT")
