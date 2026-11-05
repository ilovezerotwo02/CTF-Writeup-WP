import re
import z3
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

LOG = r'C:/Users/ASUS/Documents/Qoder/2026-10-31/0f67305c/poke1.log'
CTX0 = r'C:/Users/ASUS/Documents/Qoder/2026-10-31/0f67305c/ctx776.bin'
TABLES = r'C:/Users/ASUS/Documents/Qoder/2026-10-31/0f67305c/tables.bin'
EXP = bytes.fromhex('082f54e63c2997605d0679ba143a49d07dcdba76266c79d0')
PA = bytes.fromhex('bda7d397b51b7f23911c7a4ddcd32b1ecc2d8b1e7ba0c07d')
MODE = 'solve'   # or 'check_pa'

ctx0 = open(CTX0, 'rb').read()
tables = open(TABLES, 'rb').read()
md = Cs(CS_ARCH_X86, CS_MODE_64)

BV8 = z3.BitVecSort(8)
BV16 = z3.BitVecSort(16)
BV32 = z3.BitVecSort(32)


def mk_arr(sort, values, width):
    arr = z3.K(sort, z3.BitVecVal(0, width))
    for i, v in enumerate(values):
        arr = z3.Store(arr, z3.BitVecVal(i, width), z3.BitVecVal(v, width))
    return arr


SBOX = None
TAB = z3.K(z3.BitVecSort(16), z3.BitVecVal(0, 8))
for _i, _v in enumerate(tables):
    TAB = z3.Store(TAB, z3.BitVecVal(_i, 16), z3.BitVecVal(_v, 8))
LOGW = mk_arr(BV16, [int.from_bytes(tables[0x500 + 2 * i:0x502 + 2 * i], 'little') for i in range(0x240)], 16)

L = [z3.BitVec('L%d' % i, 8) for i in range(24)]
if MODE == 'check_pa':
    L = [z3.BitVecVal(b, 8) for b in PA]

Mem = [z3.BitVecVal(ctx0[i], 8) for i in range(len(ctx0))]
for i in range(24):
    Mem[0x60 + i] = L[i]

regs = {'eax': z3.BitVecVal(0, 32), 'ecx': z3.BitVecVal(0, 32), 'edx': z3.BitVecVal(0, 32),
        'r8d': z3.BitVecVal(0, 32), 'r9d': z3.BitVecVal(0, 32), 'r10d': z3.BitVecVal(0, 32),
        'r11d': z3.BitVecVal(0, 32)}
ptrs = {'rdi': 0x5a9c20, 'rsi': 0x5aa120, 'r12': 0x5aa360, 'rbp': 0x5aa320}
stack = []


def rd(off, n):
    bs = [Mem[off + i] for i in range(n)]
    v = bs[-1]
    for b in reversed(bs[:-1]):
        v = z3.Concat(v, b)
    return v


def wr(off, n, v):
    for i in range(n):
        Mem[off + i] = z3.Extract(8 * i + 7, 8 * i, v)


def w8imm(name, imm):
    if name in ('al', 'cl', 'dl'):
        w8(name, z3.BitVecVal(imm, 8))
    elif name == 'sil':
        ptrs['rsi'] = (ptrs['rsi'] & ~0xff) | (imm & 0xff)
    else:
        raise Exception('w8imm ' + name)


def r8(name):
    if name == 'al': return z3.Extract(7, 0, regs['eax'])
    if name == 'cl': return z3.Extract(7, 0, regs['ecx'])
    if name == 'dl': return z3.Extract(7, 0, regs['edx'])
    if name == 'sil': return z3.BitVecVal(ptrs['rsi'] & 0xff, 8)
    raise Exception('r8 ' + name)


def w8(name, v):
    if name == 'al':
        regs['eax'] = z3.Concat(z3.Extract(31, 8, regs['eax']), v)
    elif name == 'cl':
        regs['ecx'] = z3.Concat(z3.Extract(31, 8, regs['ecx']), v)
    elif name == 'dl':
        regs['edx'] = z3.Concat(z3.Extract(31, 8, regs['edx']), v)
    else:
        raise Exception('w8 ' + name)


def r32(name):
    if name == 'eax' or name == 'rax': return regs['eax']
    if name == 'ecx' or name == 'rcx': return regs['ecx']
    if name == 'edx' or name == 'rdx': return regs['edx']
    if name == 'r8d' or name == 'r8': return regs['r8d']
    if name == 'r9d' or name == 'r9': return regs['r9d']
    if name == 'r10d' or name == 'r10': return regs['r10d']
    if name == 'r11d' or name == 'r11': return regs['r11d']
    if name == 'esi': return z3.BitVecVal(ptrs['rsi'], 32)
    if name == 'edi': return z3.BitVecVal(ptrs['rdi'], 32)
    raise Exception('r32 ' + name)


CUR=[None]
def w32(name, v):
    if z3.is_bv(v) and v.size() != 32:
        raise Exception('w32 width %d for %s at %s' % (v.size(), name, CUR[0]))
    if name in ('eax', 'rax'): regs['eax'] = v
    elif name in ('ecx', 'rcx'): regs['ecx'] = v
    elif name in ('edx', 'rdx'): regs['edx'] = v
    elif name in ('r8d', 'r8'): regs['r8d'] = v
    elif name in ('r9d', 'r9'): regs['r9d'] = v
    elif name in ('r10d', 'r10'): regs['r10d'] = v
    elif name in ('r11d', 'r11'): regs['r11d'] = v
    else: raise Exception('w32 ' + name)


def r16(name):
    if name == 'ax': return z3.Extract(15, 0, regs['eax'])
    if name == 'cx': return z3.Extract(15, 0, regs['ecx'])
    if name == 'dx': return z3.Extract(15, 0, regs['edx'])
    if name == 'r11w': return z3.Extract(15, 0, regs['r11d'])
    raise Exception('r16 ' + name)


def w16(name, v):
    if name == 'ax':
        regs['eax'] = z3.Concat(z3.Extract(31, 16, regs['eax']), v)
    elif name == 'cx':
        regs['ecx'] = z3.Concat(z3.Extract(31, 16, regs['ecx']), v)
    elif name == 'dx':
        regs['edx'] = z3.Concat(z3.Extract(31, 16, regs['edx']), v)
    else:
        raise Exception('w16 ' + name)


def opsize(op):
    if 'byte ptr' in op: return 1
    if 'dword ptr' in op: return 4
    if 'word ptr' in op: return 2
    return 0


def step(ins):
    mn, op = ins.mnemonic, ins.op_str
    parts = [x.strip() for x in op.split(',')] if op else []
    if mn == 'movzx':
        dst, src = parts
        if '[r12 +' in src:
            off = int(re.search(r'0x([0-9a-f]+)', src).group(1), 16)
            sz = opsize(src)
            v = rd(off, sz)
        elif '[rdi + rax]' in src:
            v = z3.Select(TAB, z3.Extract(15, 0, regs['eax']))
        elif '[rdi + rcx' in src:
            v = z3.Select(TAB, z3.Extract(15, 0, regs['ecx'] + z3.BitVecVal(0x300, 32)))
        elif '[rdi + rdx' in src:
            v = z3.Select(TAB, z3.Extract(15, 0, regs['edx'] + z3.BitVecVal(0x300, 32)))
        elif '[rsi + rax*2]' in src:
            delta = ((ptrs['rsi'] - 0x5aa120) // 2) & 0xffff
            v = z3.Select(LOGW, z3.Extract(15, 0, regs['eax'] + z3.BitVecVal(delta, 32)))
        else:
            raise Exception('movzx src ' + src)
        w32(dst, z3.ZeroExt(32 - 8 * opsize(src) if opsize(src) else 24, v))
        return
    if mn == 'mov':
        dst, src = parts
        if 'ptr' in dst:
            off = int(re.search(r'0x([0-9a-f]+)', dst).group(1), 16)
            sz = opsize(dst)
            if 'ptr' in src:
                o2 = int(re.search(r'0x([0-9a-f]+)', src).group(1), 16)
                v = rd(o2, opsize(src))
            elif src.startswith('0x') or src == '0':
                v = z3.BitVecVal(int(src, 16) if src.startswith('0x') else 0, 8 * sz)
            elif src in ('al', 'cl', 'dl', 'sil'):
                v = r8(src)
            elif src in ('ax', 'cx', 'dx', 'r11w'):
                v = r16(src)
            else:
                v = r32(src)
            wr(off, sz, v)
        else:
            if 'ptr' in src:
                off = int(re.search(r'0x([0-9a-f]+)', src).group(1), 16)
                v = rd(off, opsize(src))
                w32(dst, v)
            elif src.startswith('0x') or src == '0':
                imm = int(src, 16) if src.startswith('0x') else 0
                if dst in ('al', 'cl', 'dl', 'sil'): w8imm(dst, imm)
                elif dst in ('ax', 'cx', 'dx'): w16(dst, z3.BitVecVal(imm, 16))
                elif dst in ('edi', 'esi'): ptrs['rdi' if dst == 'edi' else 'rsi'] = imm
                else: w32(dst, z3.BitVecVal(imm, 32))
            else:
                if src == 'sil':
                    w8('sil', z3.BitVecVal(ptrs['rsi'] & 0xff, 8))
                elif src in ('ax', 'cx', 'dx', 'r11w'):
                    v = r16(src); w16(dst, v)
                else:
                    v = r32(src)
                    if dst in ('al', 'cl', 'dl', 'sil'):
                        w8(dst, z3.Extract(7, 0, v))
                    elif dst in ('ax', 'cx', 'dx'):
                        w16(dst, z3.Extract(15, 0, v))
                    else:
                        w32(dst, v)
        return
    if mn == 'xor':
        dst, src = parts
        if 'ptr' in dst:
            raise Exception('xor mem dst')
        dv = r8(dst) if dst in ('al', 'cl', 'dl') else r32(dst)
        if 'ptr' in src:
            off = int(re.search(r'0x([0-9a-f]+)', src).group(1), 16)
            sv = rd(off, opsize(src))
        elif re.fullmatch(r'0x[0-9a-f]+|[0-9]+', src):
            sv = z3.BitVecVal(int(src, 0), 8 if dst in ('al', 'cl', 'dl') else 32)
        else:
            sv = r8(src) if src in ('al', 'cl', 'dl') else r32(src)
        if dst in ('al', 'cl', 'dl'):
            w8(dst, dv ^ sv)
        else:
            w32(dst, dv ^ sv)
        return
    if mn == 'add':
        dst, src = parts
        imm = int(src, 0) if re.fullmatch(r'0x[0-9a-f]+|[0-9]+', src) else None
        if dst == 'sil':
            ptrs['rsi'] = (ptrs['rsi'] + imm) & 0xffffffffffffffff
            return
        if dst in ('ax', 'cx', 'dx'):
            w16(dst, r16(dst) + z3.BitVecVal(imm, 16))
            return
        v = r32(dst)
        if imm is not None:
            w32(dst, v + z3.BitVecVal(imm, 32))
        else:
            w32(dst, v + r32(src))
        return
    if mn in ('and', 'or'):
        dst, src = parts
        if 'ptr' in dst:
            off = int(re.search(r'0x([0-9a-f]+)', dst).group(1), 16)
            sz = opsize(dst)
            v = rd(off, sz)
            if 'ptr' in src:
                s = rd(int(re.search(r'0x([0-9a-f]+)', src).group(1), 16), sz)
            elif src.startswith('0x'):
                s = z3.BitVecVal(int(src, 16), 8 * sz)
            elif src in ('al', 'cl', 'dl'):
                s = r8(src)
            else:
                s = z3.Extract(8 * sz - 1, 0, r32(src))
            wr(off, sz, v & s if mn == 'and' else v | s)
        else:
            if dst in ('ax', 'cx', 'dx'):
                s = z3.BitVecVal(int(src, 16), 16)
                w16(dst, r16(dst) & s if mn == 'and' else r16(dst) | s)
                return
            if src.startswith('0x'):
                s = z3.BitVecVal(int(src, 16), 32)
            else:
                s = r32(src)
            w32(dst, r32(dst) & s if mn == 'and' else r32(dst) | s)
        return
    if mn in ('shr', 'shl', 'rol', 'ror', 'sar'):
        dst = parts[0]
        cnt = int(parts[1], 16) if parts[1].startswith('0x') else int(parts[1])
        v = r32(dst)
        if mn == 'shr': r = z3.LShR(v, cnt)
        elif mn == 'shl': r = v << cnt
        elif mn == 'sar': r = v >> cnt
        elif mn == 'rol': r = z3.RotateLeft(v, cnt)
        else: r = z3.RotateRight(v, cnt)
        w32(dst, r)
        return
    if mn in ('push', 'pop'):
        r = parts[0]
        if mn == 'push':
            if r in ('rdi', 'rsi'):
                stack.append(z3.BitVecVal(ptrs[r], 32))
            else:
                stack.append(r32(r))
        else:
            v = stack.pop()
            if r in ('rdi', 'rsi'):
                if z3.is_bv_value(v):
                    ptrs[r] = v.as_long()
            else:
                w32(r, v)
        return
    if mn in ('nop', 'syscall', 'endbr64'):
        return
    raise Exception('unhandled %s %s' % (mn, op))


max_trap = 2600
last_ea = None
for line in open(LOG, errors='ignore'):
    m = re.match(r'EXEC trap=(\d+) rip=([0-9a-f]+) ctx4=([0-9a-f]+) ea=([0-9a-f]+) b=([0-9a-f]+)', line)
    if not m:
        continue
    trap = int(m.group(1)); ea = int(m.group(4), 16); by = bytes.fromhex(m.group(5))
    if trap < 776 or trap > max_trap:
        continue
    if trap == 2464:
        wr(0xa, 2, z3.BitVecVal(0x5feb, 16))
    if not (0x409700 <= ea <= 0x40d700):
        last_ea = None
        continue
    if ea == last_ea:
        continue
    last_ea = ea
    ins = list(md.disasm(by[:15], ea))
    if not ins:
        continue
    try:
        CUR[0] = '%d %x %s %s' % (trap, ea, ins[0].mnemonic, ins[0].op_str)
        step(ins[0])
    except Exception as e:
        print('FAIL trap=%d ea=%x %s %s : %s' % (trap, ea, ins[0].mnemonic, ins[0].op_str, e))
        raise

mac = [Mem[0xa8 + i] for i in range(24)]
AMAC = bytes.fromhex('dae875752c94642b0255e82b826faeb27e8a59430926b3b0')
if MODE == 'check_pa':
    def simp(v):
        v = z3.simplify(v)
        return v.as_long() if z3.is_bv_value(v) else ('EXPR:' + str(v)[:60])
    print('sym 90:', [simp(Mem[0x90+i]) for i in range(24)])
    print('A   90:', list(bytes.fromhex('c564b28e4c7655239b9928e19d3a968ed4436434115ec9e2')))
    print('sym a8:', [simp(Mem[0xa8+i]) for i in range(24)])
    print('A   a8:', list(bytes.fromhex('1f8cc7fb60e2310899ccc0ca1f55383caac93d7718787a52')))
    print('sym mac:', [simp(mac[i]) for i in range(24)])
    print('A   mac:', list(bytes.fromhex('dae875752c94642b0255e82b826faeb27e8a59430926b3b0')))
    s = z3.Solver()
    for i in range(24):
        s.add(mac[i] == AMAC[i])
    print('PA self-check (vs A MAC):', s.check())
else:
    print('mac sample expr:', str(mac[0])[:80])
    s = z3.Solver()
    s.set('timeout', 540000)
    for i in range(24):
        s.add(mac[i] == EXP[i])
    print('solving...')
    r = s.check()
    print(r)
    if r == z3.sat:
        m = s.model()
        lic = bytes([m.eval(L[i]).as_long() for i in range(24)])
        print('LICENSE24', lic.hex())
        print('ASCII', lic)
