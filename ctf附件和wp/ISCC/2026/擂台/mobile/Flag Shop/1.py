import glob
import struct
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UcError, UC_ARCH_ARM64, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC, UC_PROT_ALL, UC_HOOK_CODE
from unicorn.arm64_const import *

import os
so_path = os.path.join(os.path.dirname(__file__), 'resources', 'lib', 'arm64-v8a', 'libflagshop.so')
if not os.path.exists(so_path):
    so_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'lib', 'arm64-v8a', 'libflagshop.so')
if not os.path.exists(so_path):
    so_path = glob.glob('**/resources/lib/arm64-v8a/libflagshop.so', recursive=True)[0]
path = os.path.abspath(so_path)
PAGE = 0x1000

def align_down(x):
    return x & ~(PAGE - 1)

def align_up(x):
    return (x + PAGE - 1) & ~(PAGE - 1)

def read_cstr(mu, addr, limit=0x1000):
    out = bytearray()
    for i in range(limit):
        b = mu.mem_read(addr + i, 1)[0]
        if b == 0:
            break
        out.append(b)
    return out.decode('utf-8', 'replace')

def write_cstr(mu, addr, s):
    mu.mem_write(addr, s.encode() + b'\x00')

with open(path, 'rb') as f:
    elf = ELFFile(f)
    mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)

    for seg in elf.iter_segments():
        if seg['p_type'] != 'PT_LOAD':
            continue
        vaddr = seg['p_vaddr']
        memsz = seg['p_memsz']
        filesz = seg['p_filesz']
        start = align_down(vaddr)
        end = align_up(vaddr + memsz)
        perms = 0
        flags = seg['p_flags']
        if flags & 4:
            perms |= UC_PROT_READ
        if flags & 2:
            perms |= UC_PROT_WRITE
        if flags & 1:
            perms |= UC_PROT_EXEC
        mu.mem_map(start, end - start, perms)
        mu.mem_write(vaddr, seg.data())
        if memsz > filesz:
            mu.mem_write(vaddr + filesz, b'\x00' * (memsz - filesz))

    for secname in ('.rela.dyn', '.rela.plt'):
        sec = elf.get_section_by_name(secname)
        if not sec:
            continue
        symtab = elf.get_section(sec['sh_link']) if sec['sh_link'] else None
        for rel in sec.iter_relocations():
            rtype = rel['r_info_type']
            off = rel['r_offset']
            addend = rel['r_addend'] if rel.is_RELA() else 0
            if rtype == 1027:
                mu.mem_write(off, struct.pack('<q', addend))

    stack = 0x2000000
    mu.mem_map(stack, 0x200000, UC_PROT_ALL)
    sp = stack + 0x1f0000
    mu.reg_write(UC_ARM64_REG_SP, sp)
    mu.reg_write(UC_ARM64_REG_X29, sp)

    env = 0x3000000
    vtbl = 0x3001000
    mu.mem_map(0x3000000, 0x30000, UC_PROT_ALL)
    mu.mem_write(env, struct.pack('<Q', vtbl))

    stub_base = 0x3100000
    mu.mem_map(stub_base, 0x10000, UC_PROT_ALL)
    ret_stub = b'\xc0\x03\x5f\xd6'
    stub_for = {}
    stub_i = 0
    plt = elf.get_section_by_name('.rela.plt')
    if plt:
        symtab = elf.get_section(plt['sh_link'])
        for rel in plt.iter_relocations():
            sym = symtab.get_symbol(rel['r_info_sym']).name if rel['r_info_sym'] else ''
            if sym not in stub_for:
                stub_for[sym] = stub_base + stub_i * 0x100
                mu.mem_write(stub_for[sym], ret_stub)
                stub_i += 1
            mu.mem_write(rel['r_offset'], struct.pack('<Q', stub_for[sym]))

    newstring_stub = 0x3200000
    mu.mem_map(newstring_stub, 0x1000, UC_PROT_ALL)
    mu.mem_write(newstring_stub, ret_stub)
    mu.mem_write(vtbl + 0x538, struct.pack('<Q', newstring_stub))

    data = 0x3300000
    mu.mem_map(data, 0x40000, UC_PROT_ALL)

    def cstr(addr, s):
        write_cstr(mu, addr, s)
        return addr

    item = cstr(data + 0x000, 'fakeflag1')
    flag = cstr(data + 0x100, 'ISCC{fakeflagfake}')
    user = cstr(data + 0x200, 'admin')
    pw = cstr(data + 0x300, 'FlagShopAdmin2026')

    heap = 0x3400000
    mu.mem_map(heap, 0x40000, UC_PROT_ALL)
    heap_next = [heap]

    def alloc(size, align=0x10):
        cur = (heap_next[0] + align - 1) & ~(align - 1)
        heap_next[0] = cur + size
        return cur

    def write_std_string(addr, s):
        b = s.encode()
        mu.mem_write(addr, b'\x00' * 0x20)
        if len(b) <= 22:
            mu.mem_write(addr, bytes([len(b) << 1]) + b + b'\x00' * (23 - len(b)))
            return
        ptr = alloc(len(b) + 1)
        mu.mem_write(ptr, b + b'\x00')
        mu.mem_write(addr, struct.pack('<Q', 1))
        mu.mem_write(addr + 8, struct.pack('<Q', len(b)))
        mu.mem_write(addr + 16, struct.pack('<Q', ptr))

    ret_strings = []
    trace = []

    def decode_std_string(addr):
        b0 = mu.mem_read(addr, 1)[0]
        if (b0 & 1) == 0:
            n = b0 >> 1
            raw = bytes(mu.mem_read(addr + 1, n))
            return raw.decode('utf-8', 'replace')
        n = struct.unpack('<Q', bytes(mu.mem_read(addr + 8, 8)))[0]
        p = struct.unpack('<Q', bytes(mu.mem_read(addr + 16, 8)))[0]
        raw = bytes(mu.mem_read(p, min(n, 0x200)))
        return raw.decode('utf-8', 'replace')

    def emulate_symbol(sym):
        x0 = mu.reg_read(UC_ARM64_REG_X0)
        x1 = mu.reg_read(UC_ARM64_REG_X1)
        x2 = mu.reg_read(UC_ARM64_REG_X2)
        lr = mu.reg_read(UC_ARM64_REG_LR)
        if sym == 'strlen':
            trace.append(('call', sym, hex(lr), hex(x0), read_cstr(mu, x0)[:120]))
            mu.reg_write(UC_ARM64_REG_X0, len(read_cstr(mu, x0).encode()))
        elif sym == 'strcmp':
            a = read_cstr(mu, x0)
            b = read_cstr(mu, x1)
            trace.append(('call', sym, hex(lr), a[:80], b[:80]))
            mu.reg_write(UC_ARM64_REG_X0, (a > b) - (a < b))
        elif sym == 'strncmp':
            a = read_cstr(mu, x0)[:x2]
            b = read_cstr(mu, x1)[:x2]
            trace.append(('call', sym, hex(lr), a[:80], b[:80], x2))
            mu.reg_write(UC_ARM64_REG_X0, (a > b) - (a < b))
        elif sym == 'memcmp':
            a = bytes(mu.mem_read(x0, x2))
            b = bytes(mu.mem_read(x1, x2))
            trace.append(('call', sym, hex(lr), x2, a[:64].hex(), b[:64].hex()))
            mu.reg_write(UC_ARM64_REG_X0, (a > b) - (a < b))
        elif sym in ('memcpy', '__memcpy_chk', 'memmove'):
            trace.append(('call', sym, hex(lr), hex(x0), hex(x1), x2))
            mu.mem_write(x0, bytes(mu.mem_read(x1, x2)))
            mu.reg_write(UC_ARM64_REG_X0, x0)
        elif sym == 'memset':
            mu.mem_write(x0, bytes([x1 & 0xff]) * x2)
            mu.reg_write(UC_ARM64_REG_X0, x0)
        elif sym == 'malloc':
            mu.reg_write(UC_ARM64_REG_X0, alloc(max(x0, 1)))
        elif sym == 'realloc':
            p = alloc(max(x1, 1))
            if x0:
                mu.mem_write(p, bytes(mu.mem_read(x0, x1)))
            mu.reg_write(UC_ARM64_REG_X0, p)
        elif sym == 'free':
            mu.reg_write(UC_ARM64_REG_X0, 0)
        elif sym == '__system_property_get':
            prop = read_cstr(mu, x0)
            val = '1' if 'frida' in prop.lower() else ''
            write_cstr(mu, x1, val)
            mu.reg_write(UC_ARM64_REG_X0, len(val))
        elif sym == 'strstr':
            hay = read_cstr(mu, x0)
            nee = read_cstr(mu, x1)
            idx = hay.find(nee)
            mu.reg_write(UC_ARM64_REG_X0, 0 if idx < 0 else x0 + idx)
        elif sym == 'getpid':
            mu.reg_write(UC_ARM64_REG_X0, 1234)
        elif sym == 'syscall':
            mu.reg_write(UC_ARM64_REG_X0, 0)
        elif sym in ('abort', '__stack_chk_fail'):
            raise RuntimeError(sym)
        else:
            mu.reg_write(UC_ARM64_REG_X0, 0)

    def hook_code(mu, addr, size, user_data):
        if addr == 0x5007c:
            src = mu.reg_read(UC_ARM64_REG_X1)
            target = mu.reg_read(UC_ARM64_REG_X8)
            s = read_cstr(mu, src)
            write_std_string(target, s)
            trace.append(('copy', hex(target), s, bytes(mu.mem_read(target, 24)).hex()))
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return
        if addr == newstring_stub:
            s = read_cstr(mu, mu.reg_read(UC_ARM64_REG_X1))
            ret_strings.append(s)
            trace.append(('retstr', hex(mu.reg_read(UC_ARM64_REG_LR)), s[:120]))
            mu.reg_write(UC_ARM64_REG_X0, mu.reg_read(UC_ARM64_REG_X1))
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return
        if addr in (0x52280, 0x522b4, 0x522c8, 0x522f4, 0x52384, 0x523b8, 0x523cc, 0x523f8, 0x52464, 0x52498, 0x524ac, 0x524d8, 0x53024, 0x53058, 0x5306c, 0x53098, 0x53154, 0x53188, 0x5319c, 0x531c8, 0x5377c, 0x537a8, 0x537bc):
            base = mu.reg_read(UC_ARM64_REG_X8)
            target = struct.unpack('<Q', bytes(mu.mem_read(base, 8)))[0] if base else 0
            trace.append(('indirect', hex(addr), hex(base), hex(target)))
        for sym, stub in stub_for.items():
            if addr == stub:
                trace.append(('ext', sym))
                emulate_symbol(sym)
                mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
                return
        if addr == 0x6e1ac:
            trace.append(('skip', hex(addr)))
            mu.reg_write(UC_ARM64_REG_PC, mu.reg_read(UC_ARM64_REG_LR))
            return

    mu.hook_add(UC_HOOK_CODE, hook_code)
    mu.reg_write(UC_ARM64_REG_X0, env)
    mu.reg_write(UC_ARM64_REG_X1, 0x1234)
    mu.reg_write(UC_ARM64_REG_X2, item)
    mu.reg_write(UC_ARM64_REG_X3, flag)
    mu.reg_write(UC_ARM64_REG_X4, user)
    mu.reg_write(UC_ARM64_REG_X5, pw)

    try:
        mu.emu_start(0x517a8, 0x56000, count=10000000)
        print('EMU_OK')
    except Exception as e:
        print('EMUERR', type(e).__name__, e)
        print('PC', hex(mu.reg_read(UC_ARM64_REG_PC)))
        print('LR', hex(mu.reg_read(UC_ARM64_REG_LR)))

    print('RETCOUNT', len(ret_strings))
    for i, s in enumerate(ret_strings[:20]):
        print('RET', i, repr(s[:200]))
    print('TRACECOUNT', len(trace))
    for t in trace:
        print('TRACE', t)