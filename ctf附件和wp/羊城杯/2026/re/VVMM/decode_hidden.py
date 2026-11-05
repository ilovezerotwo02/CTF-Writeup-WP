#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Map VM opcodes via entry1 + official disasm, then disassemble hidden entry0."""
import re, struct, os
HERE = os.path.dirname(os.path.abspath(__file__))

# parse official disasm: pc, mnemonic, r1, r2, b3, imm
off_dis = {}
for ln in open(r"C:\Users\ASUS\WorkBuddy\yangcheng\vvmm\disasm.txt", encoding="utf-8", errors="replace"):
    m = re.match(r"^([0-9a-f]+)\s+([A-Z0-9]+)\s+r(\d+) r(\d+) (\S+)\s+imm=0x([0-9a-f]+)", ln)
    if m:
        off_dis[int(m.group(1), 16)] = (m.group(2), int(m.group(3)), int(m.group(4)), m.group(5), int(m.group(6), 16))

e1 = open(r"C:\Users\ASUS\WorkBuddy\yangcheng\vvmm\entry1.bin", "rb").read()
opmap = {}
for pc in range(0, len(e1), 8):
    ins = e1[pc:pc+8]
    op = ins[0]
    r1, r2 = ins[1] & 7, ins[2] & 7
    b3 = ins[3]
    imm = struct.unpack("<I", ins[4:8])[0]
    if pc in off_dis:
        name, dr1, dr2, db3, dimm = off_dis[pc]
        if name in opmap and opmap[name] != op:
            print(f"CONFLICT at {pc:#x}: {name} was {opmap[name]} now {op}")
        opmap[name] = op
        assert (r1, r2) == (dr1, dr2) and imm == dimm, f"mismatch at {pc:#x}: {(r1,r2,imm)} vs {(dr1,dr2,dimm)}"
print("opcode map:", {v: k for k, v in sorted(opmap.items(), key=lambda x: x[1])})

names = {v: k for k, v in opmap.items()}
e0 = open(r"C:\Users\ASUS\WorkBuddy\yangcheng\vvmm\entry0.bin", "rb").read()
print(f"\n=== hidden entry0: {len(e0)} bytes, {len(e0)//8} instructions ===")
for pc in range(0, len(e0), 8):
    ins = e0[pc:pc+8]
    op = ins[0]
    r1, r2, b3 = ins[1] & 7, ins[2] & 7, ins[3]
    imm = struct.unpack("<I", ins[4:8])[0]
    name = names.get(op, f"OP_{op:#04x}")
    extra = ""
    if name in ("LDB", "LDM", "STM") and b3:
        extra = f"  index={b3}"
    if name in ("JMP", "JZ", "JNZ"):
        extra = f"  target={imm:#06x}"
    print(f"{pc:04x}  {name:<6} r{r1} r{r2} {b3:02x}  imm={imm:#010x}{extra}")
