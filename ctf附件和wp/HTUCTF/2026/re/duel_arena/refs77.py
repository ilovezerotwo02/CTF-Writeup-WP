import pefile
from capstone import *

pe = pefile.PE('duel_arena.exe')
base = pe.OPTIONAL_HEADER.ImageBase
text = None
for s in pe.sections:
    if s.Name.startswith(b'.text'):
        text = s.get_data()
        tva = s.VirtualAddress
print('text size', len(text), hex(tva))

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True
targets = {0xeb3f8: 'invalid_action', 0xeb56e: 'hint_true_kiss', 0xeb81d: 'defeat_king', 0xeb900: 'got_token'}
refs = {}
for ins in md.disasm(text, base + tva):
    if ins.mnemonic in ('lea', 'mov') and 'rip' in ins.op_str:
        try:
            for op in ins.operands:
                if op.type == 3 and op.mem.base == 41:
                    tgt = ins.address + ins.size + op.mem.disp - base
                    if tgt in targets:
                        refs.setdefault(tgt, []).append(ins.address - base)
        except Exception:
            pass
for k, v in targets.items():
    print(v, hex(k), [hex(x) for x in refs.get(k, [])])
