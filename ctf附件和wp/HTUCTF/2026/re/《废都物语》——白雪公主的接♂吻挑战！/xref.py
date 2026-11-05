"""在 .text 里找引用了指定字符串（按文件偏移给）的指令 —— rip 相对寻址。"""
import sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_REG_RIP

pe = pefile.PE('duel_arena.exe')
IB = pe.OPTIONAL_HEADER.ImageBase
SECT = [(s.VirtualAddress, s.PointerToRawData, s.SizeOfRawData, s.Name.rstrip(b'\x00').decode(errors='replace')) for s in pe.sections]


def off2va(off):
    for va, raw, size, _ in SECT:
        if raw and raw <= off < raw + size:
            return IB + va + (off - raw)
    return None


def va2off(va):
    rva = va - IB
    for va0, raw, size, _ in SECT:
        if va0 <= rva < va0 + size:
            return raw + (rva - va0)
    return None


text = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
code = pe.get_data(text.VirtualAddress, text.SizeOfRawData)
base = IB + text.VirtualAddress
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

targets = [off2va(int(a, 16)) for a in sys.argv[1:]]
print('targets', [hex(t) for t in targets if t])
tset = set(t for t in targets if t)
hits = {t: [] for t in tset}
for ins in md.disasm(code, base):
    for op in ins.operands:
        if op.type == 3 and op.mem.base == X86_REG_RIP:      # X86_OP_MEM = 3
            tgt = ins.address + ins.size + op.mem.disp
            if tgt in tset:
                hits[tgt].append((ins.address, ins.mnemonic, ins.op_str))
for t in sorted(tset):
    print('==', hex(t), 'off', hex(va2off(t) or 0), 'refs', len(hits[t]))
    for a, m, o in hits[t][:10]:
        print('   %#x  %s %s' % (a, m, o))
