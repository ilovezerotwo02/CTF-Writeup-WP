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

# Generate v23
V23_SEED = (0x61565bd7d1b80021 ^ 0x517cc1b727220a95) & 0xFFFFFFFFFFFFFFFF
v10_state = [V23_SEED]
v11 = list(range(256))
for i in range(256, 1, -1):
    v7 = sub_1CBE6(v10_state) % i
    v11[i-1], v11[v7] = v11[v7], v11[i-1]
mapping = v11[:16]
v23 = bytearray([0xFF] * 256)
for i, bval in enumerate(mapping):
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
    start = struct.unpack_from("<Q", qdata, i*16)[0]
    end = struct.unpack_from("<Q", qdata, i*16+8)[0]
    qword_11700.append((start, end))

print(f"Seed: 0x{SEED:016x}")
print(f"v20: {[hex(v) for v in v20]}")
print(f"v23 mapping: {bytes(mapping).hex()}")

def run_step(bc, user_input, v20_loc):
    """Execute a single VM bytecode chunk"""
    pos = 0
    regs = [0] * 8
    acc_lo = 0
    bc_len = len(bc)

    while pos < bc_len:
        if pos >= bc_len:
            return False

        bval = bc[pos]
        op = v23[bval]
        pos += 1

        if op == 0xFF:
            return False

        if op == 0:  # ACC_ROT
            if pos >= bc_len: return False
            pos += 1  # skip register byte
            shift = (pos & 0x1F) + 1
            # No actual v39 in our emulation, skip

        elif op == 1:  # LOAD_CONST: reg = u64
            if pos + 9 > bc_len: return False
            ri = bc[pos]; pos += 1
            val = struct.unpack_from("<Q", bc, pos)[0]; pos += 8
            if ri < 8: regs[ri] = val

        elif op == 2:  # LOAD_BYTE: reg = input[byte]
            if pos + 2 > bc_len: return False
            ri = bc[pos]; pos += 1
            idx = bc[pos]; pos += 1
            if ri < 8 and idx < len(user_input):
                regs[ri] = user_input[idx]

        elif op == 3:  # LOAD_V20: reg = v20[v20_idx]
            if pos + 2 > bc_len: return False
            ri = bc[pos]; pos += 1
            vi = bc[pos]; pos += 1
            if ri < 8 and vi < 4: regs[ri] = v20_loc[vi]

        elif op == 4:  # ADD: reg[a] += reg[b]
            if pos + 2 > bc_len: return False
            ra = bc[pos]; pos += 1
            rb_i = bc[pos]; pos += 1
            if ra < 8 and rb_i < 8:
                regs[ra] = (regs[ra] + regs[rb_i]) & 0xFFFFFFFFFFFFFFFF

        elif op == 5:  # XOR: reg[a] ^= reg[b]
            if pos + 2 > bc_len: return False
            ra = bc[pos]; pos += 1
            rb_i = bc[pos]; pos += 1
            if ra < 8 and rb_i < 8: regs[ra] ^= regs[rb_i]

        elif op == 6:  # MUL: reg[a] *= (reg[b] | 1)
            if pos + 2 > bc_len: return False
            ra = bc[pos]; pos += 1
            rb_i = bc[pos]; pos += 1
            if ra < 8 and rb_i < 8:
                regs[ra] = (regs[ra] * (regs[rb_i] | 1)) & 0xFFFFFFFFFFFFFFFF

        elif op == 7:  # ADD_IMM: reg += u64
            if pos + 9 > bc_len: return False
            ri = bc[pos]; pos += 1
            val = struct.unpack_from("<Q", bc, pos)[0]; pos += 8
            if ri < 8: regs[ri] = (regs[ri] + val) & 0xFFFFFFFFFFFFFFFF

        elif op == 8:  # ROL: reg = ROL(reg, shift)
            if pos + 2 > bc_len: return False
            ri = bc[pos]; pos += 1
            shift = bc[pos]; pos += 1
            if ri < 8: regs[ri] = ROL64(regs[ri], shift)

        elif op == 9:  # STORE_V20: v20[vi] = reg[ri]
            if pos + 2 > bc_len: return False
            vi = bc[pos]; pos += 1
            ri = bc[pos]; pos += 1
            if vi < 4 and ri < 8: v20_loc[vi] = regs[ri]

        elif op == 0xA:  # CMP: if reg[ri] != val: fail
            if pos + 9 > bc_len: return False
            ri = bc[pos]; pos += 1
            val = struct.unpack_from("<Q", bc, pos)[0]; pos += 8
            if ri < 8 and regs[ri] != val: return False

        elif op == 0xB:  # SPECIAL_XOR
            if pos + 2 > bc_len: return False
            ri = bc[pos]; pos += 1
            x = bc[pos]; pos += 1
            if ri < 8:
                shift = x & 0x1F
                acc_lo = ROL64(acc_lo + (regs[ri] ^ (x << (pos & 0x3F))), shift) if False else 0

        elif op == 0xC:  # END: succeed if consumed all bytes exactly
            return pos == bc_len

        elif op == 0xD:  # SUB_IMM: reg -= u64
            if pos + 9 > bc_len: return False
            ri = bc[pos]; pos += 1
            val = struct.unpack_from("<Q", bc, pos)[0]; pos += 8
            if ri < 8: regs[ri] = (regs[ri] - val) & 0xFFFFFFFFFFFFFFFF

        elif op == 0xE:  # ROR: reg = ROR(reg, shift)
            if pos + 2 > bc_len: return False
            ri = bc[pos]; pos += 1
            shift = bc[pos]; pos += 1
            if ri < 8: regs[ri] = ROR64(regs[ri], shift)

        elif op == 0xF:  # COMPLEX
            if pos + 10 > bc_len: return False
            ra = bc[pos]; pos += 1
            rb_i = bc[pos]; pos += 1
            val = struct.unpack_from("<Q", bc, pos)[0]; pos += 8
            if ra < 8 and rb_i < 8:
                a = ROL64(regs[ra], val & 0x3F)
                b = ROR64(regs[rb_i], (val >> 8) & 0x3F)
                # Update acc (simplified)

    return False

# Run all valid VM steps
print(f"\n=== Testing VM execution ===")
user_input = [ord('A')] * 40

for step_idx, b in enumerate(keystream72):
    if b < len(qword_11700):
        start, end = qword_11700[b]
        if end > start and end <= 21336:
            bc = bytes(keystream21336[start:end])
            v20_copy = list(v20)
            result = run_step(bc, user_input, v20_copy)
            status = "PASS" if result else "FAIL"
            if not result:
                # Check WHY it failed
                print(f"\n  step[{step_idx:2d}] idx={b:2d} len={end-start:3d}: {status}")
                # Show first 32 bytes decoded
                for j in range(min(32, len(bc))):
                    op = v23[bc[j]]
                    tag = f"op{op}" if op != 0xFF else "DAT"
                    print(f"    [{j:3d}] 0x{bc[j]:02x} -> {tag}")
                break
            else:
                print(f"  step[{step_idx:2d}] idx={b:2d} len={end-start:3d}: {status}")

print("\nDone!")
