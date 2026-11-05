from pwn import *
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
import sys

context.log_level = 'error'
e = ELF('pwn/uaf', checksec=False)
md = Cs(CS_ARCH_X86, CS_MODE_64)


def d(addr, maxn=0x400, title=None):
    if title:
        print('=' * 20, title, hex(addr))
    code = e.read(addr, maxn)
    n = 0
    for i in md.disasm(code, addr):
        print('  %x: %-9s %s' % (i.address, i.mnemonic, i.op_str))
        n += 1
        if i.mnemonic == 'ret' or i.mnemonic == 'hlt':
            break
        if n > 200:
            break
    print()


def strings():
    seen = []
    for sec in ('.rodata', '.data'):
        base = e.get_section_by_name(sec).header.sh_addr
        data = e.read(base, e.get_section_by_name(sec).header.sh_size)
        for m in re.finditer(rb'[\x20-\x7e\xe4-\xef][\x20-\x7e\x80-\xef\xb0-\xbf]{3,}', data):
            s = m.group().decode('utf-8', 'replace')
            seen.append((base + m.start(), s))
    for a, s in seen:
        print('  %#x  %s' % (a, s))


if __name__ == '__main__':
    if sys.argv[1] == 'str':
        strings()
    else:
        for a in sys.argv[1:]:
            d(int(a, 16))
