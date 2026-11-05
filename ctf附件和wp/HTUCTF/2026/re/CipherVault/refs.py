from capstone import *
from capstone.x86 import *

img = open('image.bin', 'rb').read()
base = int(open('image_base.txt').read(), 16)
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

targets = {}
for ins in md.disasm(img[0x1000:0xa000], base + 0x1000):
    if ins.mnemonic == 'lea' and 'rip' in ins.op_str:
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                tgt = ins.address + ins.size + op.mem.disp
                rva = tgt - base
                if 0x6000 <= rva <= 0xa000:
                    targets.setdefault(rva, []).append(ins.address - base)
for rva in sorted(targets):
    s = img[rva:rva+70].split(b'\0')[0].decode(errors='replace')
    print(hex(rva), '|', s[:70], '| refs:', [hex(a) for a in targets[rva]])
