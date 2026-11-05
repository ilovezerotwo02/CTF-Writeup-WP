import struct

def ROL64(v, s):
    s &= 0x3F; v &= 0xFFFFFFFFFFFFFFFF
    return ((v << s) | (v >> (64 - s))) & 0xFFFFFFFFFFFFFFFF

def ROR64(v, s):
    s &= 0x3F; v &= 0xFFFFFFFFFFFFFFFF
    return ((v >> s) | (v << (64 - s))) & 0xFFFFFFFFFFFFFFFF

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

def sub_1CBE6(state):
    state[0] = (state[0] - 0x61C8864680B583EB) & 0xFFFFFFFFFFFFFFFF
    return sub_1DE72(state[0])

V23_SEED = (0x61565bd7d1b80021 ^ 0x517cc1b727220a95) & 0xFFFFFFFFFFFFFFFF
v10_state = [V23_SEED]
v11 = list(range(256))
for i in range(256, 1, -1):
    v7 = sub_1CBE6(v10_state) % i
    v11[i-1], v11[v7] = v11[v7], v11[i-1]
v23 = bytearray([0xFF] * 256)
for i, bval in enumerate(v11[:16]):
    v23[bval] = i

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

byte_C366 = data[0xC366:0xC366+21336]
v5_state = [SEED ^ 0x938288AB9588D79F]
keystream21336 = bytearray()
for i in range(21336):
    r = sub_1CBE6(v5_state)
    v3 = ROL64(r, i)
    keystream21336.append((v3 & 0xFF) ^ byte_C366[i] ^ ((v3 >> 56) & 0xFF))

unk_BFB8 = data[0xBFB8:0xBFB8+1800]
v2_val = ((SEED & 0xFF) << 3 | (SEED & 0xFF) >> 5) & 0xFF
keystream72 = [unk_BFB8[i//25] ^ i ^ v2_val ^ 0x5D for i in range(0, 1800, 25)]

qdata = data[0x11700:0x11700+0x60*16]
qword_11700 = []
for i in range(0x60):
    qword_11700.append((struct.unpack_from("<Q", qdata, i*16)[0], struct.unpack_from("<Q", qdata, i*16+8)[0]))

def run_vm(bc, inp, v20_arr):
    pos = 0
    regs = [0] * 8
    bc_len = len(bc)

    while pos < bc_len:
        bval = bc[pos]
        op = v23[bval]
        if op == 0xFF:
            return False, v20_arr
        pos += 1

        def rb():
            nonlocal pos
            if pos >= bc_len: return -1
            v = bc[pos]; pos += 1; return v

        def r8():
            nonlocal pos
            if pos + 8 > bc_len: return None
            v = struct.unpack_from("<Q", bc, pos)[0]; pos += 8; return v

        if op == 0:
            if rb() < 0: return False, v20_arr
        elif op == 1:
            ri = rb()
            if ri < 0 or ri >= 8: return False, v20_arr
            val = r8()
            if val is None: return False, v20_arr
            regs[ri] = val
        elif op == 2:
            ri = rb()
            if ri < 0 or ri >= 8: return False, v20_arr
            idx = rb()
            if idx < 0 or idx >= len(inp): return False, v20_arr
            regs[ri] = inp[idx]
        elif op == 3:
            ri = rb()
            if ri < 0 or ri >= 8: return False, v20_arr
            vi = rb()
            if vi < 0 or vi >= 4: return False, v20_arr
            regs[ri] = v20_arr[vi]
        elif op == 4:
            ra = rb(); rc = rb()
            if ra < 0 or ra >= 8 or rc < 0 or rc >= 8: return False, v20_arr
            regs[ra] = (regs[ra] + regs[rc]) & 0xFFFFFFFFFFFFFFFF
        elif op == 5:
            ra = rb(); rc = rb()
            if ra < 0 or ra >= 8 or rc < 0 or rc >= 8: return False, v20_arr
            regs[ra] ^= regs[rc]
        elif op == 6:
            ra = rb(); rc = rb()
            if ra < 0 or ra >= 8 or rc < 0 or rc >= 8: return False, v20_arr
            regs[ra] = (regs[ra] * (regs[rc] | 1)) & 0xFFFFFFFFFFFFFFFF
        elif op == 7:
            ri = rb()
            if ri < 0 or ri >= 8: return False, v20_arr
            val = r8()
            if val is None: return False, v20_arr
            regs[ri] = (regs[ri] + val) & 0xFFFFFFFFFFFFFFFF
        elif op == 8:
            ri = rb()
            if ri < 0 or ri >= 8: return False, v20_arr
            s = rb()
            if s < 0: return False, v20_arr
            regs[ri] = ROL64(regs[ri], s)
        elif op == 9:
            vi = rb()
            if vi < 0 or vi >= 4: return False, v20_arr
            ri = rb()
            if ri < 0 or ri >= 8: return False, v20_arr
            v20_arr[vi] = regs[ri]
        elif op == 0xA:
            ri = rb()
            if ri < 0 or ri >= 8: return False, v20_arr
            val = r8()
            if val is None: return False, v20_arr
            if regs[ri] != val:
                return False, v20_arr
        elif op == 0xB:
            if rb() < 0 or rb() < 0: return False, v20_arr
        elif op == 0xC:
            return True, v20_arr
        elif op == 0xD:
            ri = rb()
            if ri < 0 or ri >= 8: return False, v20_arr
            val = r8()
            if val is None: return False, v20_arr
            regs[ri] = (regs[ri] - val) & 0xFFFFFFFFFFFFFFFF
        elif op == 0xE:
            ri = rb()
            if ri < 0 or ri >= 8: return False, v20_arr
            s = rb()
            if s < 0: return False, v20_arr
            regs[ri] = ROR64(regs[ri], s)
        elif op == 0xF:
            if rb() < 0 or rb() < 0: return False, v20_arr
            if r8() is None: return False, v20_arr

    return False, v20_arr

# Test VM
inp = [ord("A")] * 40
v20_cur = list(v20)

for step_idx, b in enumerate(keystream72):
    if b < len(qword_11700):
        start, end = qword_11700[b]
        if end > start and end <= 21336:
            bc = bytes(keystream21336[start:end])
            ok, v20_cur = run_vm(bc, inp, v20_cur)
            if ok:
                print("Step[%2d] idx=%2d PASS" % (step_idx, b))
            else:
                print("Step[%2d] idx=%2d FAIL" % (step_idx, b))
                break

print("Final v20:", [hex(v) for v in v20_cur])
print("Orig v20:", [hex(v) for v in v20])
