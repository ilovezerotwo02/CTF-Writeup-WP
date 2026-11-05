"""对给定文件偏移/VA 找 rip 相对引用，并反汇编函数体。
用法:
  python xr.py <file_off_hex> [file_off_hex...]     找引用
  python xr.py -d <va_hex> <len>                    反汇编一段
"""
import sys
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_REG_RIP, X86_OP_MEM

EXE = 'duel_arena.exe'
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
buf = open(EXE, 'rb').read()


def o2v(off):
    for s in pe.sections:
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return IB + s.VirtualAddress + (off - s.PointerToRawData)


def v2o(va):
    r = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= r < s.VirtualAddress + s.SizeOfRawData:
            return s.PointerToRawData + (r - s.VirtualAddress)


def disas(va, ln):
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    off = v2o(va)
    for i in md.disasm(buf[off:off + ln], va):
        tgt = ''
        for op in i.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = i.address + i.size + op.mem.disp
                tgt = '   ; -> %#x' % t
                o = v2o(t)
                if o:
                    s = buf[o:o + 40].split(b'\x00')[0]
                    try:
                        tgt += ' "%s"' % s.decode('utf-8')
                    except Exception:
                        pass
        print('%#x  %-24s %s %s%s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str, tgt))


if sys.argv[1] == '-d':
    disas(int(sys.argv[2], 16), int(sys.argv[3], 16))
else:
    targets = {}
    for a in sys.argv[1:]:
        va = int(a, 16)
        targets[va if va > IB else o2v(va)] = a
    text = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
    code = pe.get_data(text.VirtualAddress, text.SizeOfRawData)
    base = IB + text.VirtualAddress
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    for ins in md.disasm(code, base):
        for op in ins.operands:
            if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                t = ins.address + ins.size + op.mem.disp
                if t in targets:
                    print('%#x -> %#x (%s)  %s %s' % (ins.address, t, targets[t], ins.mnemonic, ins.op_str))
