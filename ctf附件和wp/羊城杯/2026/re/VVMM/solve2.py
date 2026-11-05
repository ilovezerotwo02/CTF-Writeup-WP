#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exact VVMM emulator (semantics recovered from native interpreter) + inverse solver."""
import re, struct, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))

M32 = 0xFFFFFFFF

def rol8(x, n):
    n &= 7
    return ((x << n) | (x >> (8 - n))) & 0xFF if n else x & 0xFF

def ror8(x, n):
    n &= 7
    return ((x >> n) | (x << (8 - n))) & 0xFF if n else x & 0xFF

def fmix(idx, seed):
    ecx = (idx * 0x9e3779b9) & M32
    edx = (seed + 0x6d2b79f5) & M32
    edx ^= ecx
    x = edx ^ (edx >> 16)
    x = (x * 0x85ebca6b) & M32
    x ^= x >> 13
    x = (x * 0xc2b2ae35) & M32
    x ^= x >> 16
    return x

def stage(idx, v):
    h = fmix(idx, 0xA5)
    r8 = v ^ h                                  # low byte relevant
    cl = (3 * idx + 1) & 0xFF
    rot = rol8(r8 & 0xFF, cl & 0x1F)
    r8 = (r8 & 0xFFFFFF00) | rot
    edx = (h & 0xFFFFFF00) | ((h & 0xFF) >> 1)  # shr dl,1
    eax = (r8 + 0x31 * idx + 0x42) & M32
    eax ^= edx
    return eax & 0xFF

def stage_inv(idx, y):
    h = fmix(idx, 0xA5)
    edx_low = (h & 0xFF) >> 1
    s = (y ^ edx_low) & 0xFF
    rot = (s - (0x31 * idx + 0x42)) & 0xFF
    cl = (3 * idx + 1) & 0xFF
    r8_low = ror8(rot, cl & 0x1F)
    return r8_low ^ (h & 0xFF)

# ---------------- parse program ----------------
prog = open(r"C:\Users\ASUS\WorkBuddy\yangcheng\vvmm\entry1.bin", "rb").read()
N = len(prog) // 8

def decode(i):
    ins = prog[i*8:(i+1)*8]
    return ins[0], ins[1] & 7, ins[2] & 7, ins[3], struct.unpack("<I", ins[4:8])[0]

# memory init
MEM0 = [((49 * i + 0x17) & 0xFF) ^ 0xA5 for i in range(128)]

def run(candidate):
    mem = MEM0[:]
    regs = [0] * 8
    flag = 0
    pc = 0
    steps = 0
    cand = candidate
    halt = 0
    while pc * 8 + 8 <= len(prog) and steps < 0x4E20:
        op, dst, src, b3, imm = decode(pc)
        steps += 1
        npc = pc + 1
        if op == 0x00 or op == 0x01:            # NOP / MAGIC
            pass
        elif op == 0x10:                        # LEN
            flag = 1 if imm == len(cand) else 0
        elif op == 0x11:                        # LDB
            regs[dst] = cand[imm] if imm < len(cand) else 0
        elif op == 0x12:                        # LDM
            regs[dst] = mem[imm & 0x7F]
        elif op == 0x13:                        # STM
            mem[imm & 0x7F] = regs[dst] & 0xFF
        elif op == 0x20:                        # MOVI
            regs[dst] = imm & M32
        elif op == 0x21:                        # XORI
            regs[dst] ^= imm
        elif op == 0x22:                        # ADDI
            regs[dst] = (regs[dst] + imm) & M32
        elif op == 0x23:                        # MULI
            regs[dst] = (regs[dst] * imm) & M32
        elif op == 0x24:                        # ROLI (low byte only)
            regs[dst] = (regs[dst] & 0xFFFFFF00) | rol8(regs[dst] & 0xFF, imm & 0x1F)
        elif op == 0x25:                        # RORI
            regs[dst] = (regs[dst] & 0xFFFFFF00) | ror8(regs[dst] & 0xFF, imm & 0x1F)
        elif op == 0x26:                        # XORR
            regs[dst] ^= regs[src]
        elif op == 0x27:                        # ADDR
            regs[dst] = (regs[dst] + regs[src]) & M32
        elif op == 0x30:                        # STAGE
            regs[dst] = stage(imm, regs[dst] & 0xFF)
        elif op == 0x40:                        # CMPI8
            flag = 1 if (regs[dst] & 0xFF) == (imm & 0xFF) else 0
        elif op == 0x41:                        # CMPI32
            flag = 1 if regs[dst] == imm else 0
        elif op == 0x50:                        # JNZ: jump when flag==0
            if flag == 0:
                npc = pc + imm + 1
        elif op == 0x51:                        # JMP
            npc = pc + imm + 1
        elif op == 0xF0:
            halt = 0xF0; steps -= 1; break
        elif op == 0xF1:
            halt = 0xF1; steps -= 1; break
        else:
            halt = op; break
        pc = npc
    return mem, regs, flag, steps, pc, halt

# ---------------- verify against binary oracle ----------------
test = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ01234"
mem, regs, flag, steps, pc, halt = run(test)
print(f"emulator: steps={steps} pc={pc*8:#x} acc={regs[0]:#04x} zero={flag} halt={halt:#04x}")
print(f"binary  : steps=2370 pc=0x4ce8 acc=0xe9  zero=0 halt=0xf1")
ok = (steps == 2370 and pc*8 == 0x4ce8 and (regs[0] & 0xFF) == 0xE9)
print("MATCH:", ok)
if not ok:
    sys.exit(1)

# ---------------- invert ----------------
# 1) final targets
targets = []
pending = None
for i in range(N):
    op, dst, src, b3, imm = decode(i)
    if op == 0x12:  # LDM
        pending = imm
    elif op == 0x40:  # CMPI8
        targets.append((pending, imm)); pending = None
targets.sort()
assert [t[0] for t in targets] == list(range(31)), "unexpected check order"
T = [t[1] for t in targets]
print("targets:", [hex(x) for x in T])

# 2) collect mixing blocks in execution order
blocks = []
for i in range(N):
    op, dst, src, b3, imm = decode(i)
    if op == 0x12:  # LDM
        if not blocks or "stm" in blocks[-1]:
            blocks.append({"ldm": [imm]})
        else:
            blocks[-1]["ldm"].append(imm)
    elif op == 0x13:  # STM
        if blocks and "ldm" in blocks[-1] and "stm" not in blocks[-1]:
            blocks[-1]["stm"] = imm
    elif op == 0x24 and blocks and "ldm" in blocks[-1] and "k" not in blocks[-1] and "stm" not in blocks[-1]:
        blocks[-1]["k"] = imm
    elif op == 0x22 and blocks and "k" in blocks[-1] and "d" not in blocks[-1] and "stm" not in blocks[-1] and blocks[-1].get("stage_set"):
        blocks[-1]["d"] = imm
    elif op == 0x30 and blocks and "ldm" in blocks[-1] and "s" not in blocks[-1] and "stm" not in blocks[-1]:
        blocks[-1]["s"] = imm; blocks[-1]["stage_set"] = True
blocks = [b for b in blocks if "k" in b and "d" in b and "s" in b and "stm" in b]
print(f"mixing blocks: {len(blocks)}")
assert len(blocks) == 217
R = [blocks[r*31:(r+1)*31] for r in range(7)]

# sanity: block shape i, i1, i2
for r in range(7):
    for j, b in enumerate(R[r]):
        assert b["ldm"] == [j, (j+1) % 31, (j+7) % 31], (r, j, b)
        assert b["stm"] == j

# 3) undo mixing rounds (reverse)
mem = [0] * 128
for i in range(31):
    mem[i] = T[i]
for r in range(6, -1, -1):
    for j in range(30, -1, -1):
        b = R[r][j]
        i, i1, i2 = j, (j + 1) % 31, (j + 7) % 31
        y = (mem[i] - b["d"]) & 0xFF
        pre = stage_inv(b["s"], y)
        x = ror8(pre, b["k"] & 0x1F)
        old = ((x ^ mem[i2]) - mem[i1]) & 0xFF
        mem[i] = old

# 4) undo phase 1 (per-byte transform: v=(c^a)+b -> rol8 k -> stage(i))
phase1 = []
for i in range(N):
    op, dst, src, b3, imm = decode(i)
    if op == 0x11:  # LDB
        phase1.append({"i": imm})
    elif op == 0x21 and phase1 and "a" not in phase1[-1]:
        phase1[-1]["a"] = imm
    elif op == 0x22 and phase1 and "b" not in phase1[-1]:
        phase1[-1]["b"] = imm
    elif op == 0x24 and phase1 and "c" not in phase1[-1]:
        phase1[-1]["c"] = imm
assert len(phase1) == 31 and all(set(p) >= {"i","a","b","c"} for p in phase1)

flag_bytes = bytearray()
for p in phase1:
    i = p["i"]
    pre = stage_inv(i, mem[i])          # = rol8((c^a)+b, k)
    v = ror8(pre, p["c"] & 0x1F)
    ch = ((v - p["b"]) & 0xFF) ^ p["a"]
    flag_bytes.append(ch)

flag = bytes(flag_bytes)
print("\nrecovered flag:", flag)

# 5) verify by re-running emulator
mem2, regs2, flagz, steps2, pc2, halt2 = run(flag)
print(f"emulator re-run: halt={halt2:#04x} steps={steps2} -> {'ACCEPT' if halt2==0xF0 else 'REJECT'}")
