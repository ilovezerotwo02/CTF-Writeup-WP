import socket, struct, sys, json, binascii

M64 = (1 << 64) - 1

def F(x):
    x &= M64
    x ^= x >> 30
    x = (x * 0xbf58476d1ce4e5b9) & M64
    x ^= x >> 27
    x = (x * 0x94d049bb133111eb) & M64
    x ^= x >> 31
    return x

def rol(x, r):
    r &= 63
    if r == 0:
        return x & M64
    return ((x << r) | (x >> (64 - r))) & M64

def H(k1, k2, data, n=None):
    if n is None:
        n = len(data)
    h = F(k1 ^ n ^ 0x9e3779b97f4a7c15)
    kk = k2
    for i in range(n):
        t = F((kk + data[i]) & M64)
        h = ((k1 ^ ((i * 0x6a09e667f3bcc909) & M64)) + rol(t ^ h, 0x11 + 0xb * i)) & M64
        kk = (kk + 0x517cc1b727220a95) & M64
    return F(k2 ^ h ^ 0xa54ff53a5f1d36f1)


class Http:
    def __init__(self, host, port, timeout=8):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.s.settimeout(timeout)
        self.buf = b""
    def send_raw(self, data):
        self.s.sendall(data)
    def recv_some(self, n=0x1000):
        return self.s.recv(n)
    def q(self, args):
        self.s.sendall(("GET /?" + args + " HTTP/1.1\r\nHost: x\r\n\r\n").encode())
        return self.read_resp()
    def read_resp(self):
        while b"\r\n\r\n" not in self.buf:
            d = self.s.recv(65536)
            if not d:
                raise EOFError("closed")
            self.buf += d
        head, rest = self.buf.split(b"\r\n\r\n", 1)
        self.buf = rest
        lines = head.split(b"\r\n")
        status = int(lines[0].split()[1])
        clen = None
        chunked = False
        for l in lines[1:]:
            k, _, v = l.partition(b":")
            k = k.strip().lower()
            if k == b"content-length":
                clen = int(v.strip())
            if k == b"transfer-encoding" and b"chunked" in v.lower():
                chunked = True
        if chunked:
            body = b""
            while True:
                while b"\r\n" not in self.buf:
                    d = self.s.recv(65536)
                    if not d: raise EOFError("closed")
                    self.buf += d
                line, self.buf = self.buf.split(b"\r\n", 1)
                n = int(line, 16)
                while len(self.buf) < n + 2:
                    d = self.s.recv(65536)
                    if not d: raise EOFError("closed")
                    self.buf += d
                body += self.buf[:n]
                self.buf = self.buf[n + 2:]
                if n == 0:
                    break
            return status, body
        if clen is None:
            return status, b""
        while len(self.buf) < clen:
            d = self.s.recv(65536)
            if not d: raise EOFError("closed")
            self.buf += d
        body, self.buf = self.buf[:clen], self.buf[clen:]
        return status, body


def p64(x):
    return struct.pack("<Q", x & M64)

def q(data, off):
    return struct.unpack_from("<Q", data, off)[0]

def put(data, off, v):
    struct.pack_into("<Q", data, off, v & M64)


TAG_TACK = b"CLTACKT4"
TAG_BEACON = b"CBEACON4"
TAG_LEDGER = b"CLLEDGR4"
TAG_ROUTE = b"CLLROUT4"
TAG_SEAL = b"CLLSEAL4"
TAG_GRANT = b"CLGRANT4"
TAG_VOUCH = b"CVOUCHR4"

class SoLayer:
    def __init__(self, h, verbose=True):
        self.h = h
        self.v = verbose
        self.base2199 = None
        self.k1 = None
        self.k2 = None
        self.seed = None
        self.conn = None
        self.ledger30 = None

    def log(self, *a):
        if self.v:
            print("[so]", *a)

    def step_create(self, tack):
        st, body = self.h.q("op=create&data=" + tack.hex())
        self.log("create", st, body)
        return body.strip() == b"created"

    def step_resize(self, tack, tries=12):
        for i in range(tries):
            st, body = self.h.q("op=resize&data=" + tack.hex())
            if body.strip() == b"staged":
                self.log("resize ok after", i + 1)
                return True
            if st != 200:
                self.log("resize status", st, body[:60])
                return False
        return False

    def run(self):
        tack = bytearray(0x180)
        tack[0x38:0x40] = TAG_TACK
        put(tack, 0x40, 0x491)
        if not self.step_create(bytes(tack)):
            return False
        if not self.step_resize(bytes(tack)):
            return False
        st, body = self.h.q("op=ledgeropen")
        self.log("ledger(create)", st, body)
        if body.strip() != b"opened":
            return False
        st, body = self.h.q("op=beacon")
        self.log("beacon leak", st, body)
        txt = body.decode().strip()
        f = dict(x.split("=", 1) for x in txt.split())
        seed = int(f["n"], 16); a = int(f["a"], 16); e = int(f["e"], 16); k = int(f["k"], 16)
        mem = rol(seed, 0x11) ^ a
        self.base2199 = mem
        self.seed = seed
        k2 = e ^ H(mem, seed, [seed, mem], 2)
        k1 = k ^ H(mem, seed, [k2, seed], 2)
        self.k1, self.k2 = k1, k2
        self.log("mem2199=%#x k1=%#x k2=%#x" % (mem, k1, k2))
        st, body = self.h.q("op=ledger")
        self.log("ledger leak", st, body)
        txt = body.decode().strip()
        f = dict(x.split("=", 1) for x in txt.split())
        l30 = int(f["n"], 16); l40 = int(f["o"], 16); l48 = int(f["t"], 16)
        assert l48 == H(k1, k2, [l40 ^ H(k1,k2,[l30,seed],2), mem, seed, l30], 4)
        self.conn = l40 ^ H(k1, k2, [l30, seed], 2)
        self.ledger30 = l30
        self.log("conn=%#x ledger30=%#x" % (self.conn, l30))
        return True

    def build_chain(self):
        k1, k2, mem, conn, seed, l30 = self.k1, self.k2, self.base2199, self.conn, self.seed, self.ledger30
        route40 = 0x1111111111111111
        route68 = 0x2222222222222222
        route70 = 1
        seal = bytearray(0xd8)
        seal[0x28:0x30] = TAG_SEAL
        put(seal, 0x30, route68)
        put(seal, 0x38, route40)
        put(seal, 0x40, seed)
        put(seal, 0x48, l30)
        put(seal, 0x50, 0x3333333333333333)
        put(seal, 0x58, 1)
        seal_mac = H(k1 ^ 0x243f6a8885a308d3, k2,
                     [0x344c4145534c4c43, q(seal,0x30), q(seal,0x38), q(seal,0x40), q(seal,0x48), q(seal,0x50), 1], 7)
        put(seal, 0x60, seal_mac)
        grant70 = 0
        seal50 = q(seal, 0x50)
        v60 = 0x6666666666666666
        route60 = 1 ^ seal50 ^ grant70 ^ v60
        route = bytearray(0x1a8)
        route[0x38:0x40] = TAG_ROUTE
        put(route, 0x40, route40)
        put(route, 0x48, H(k1, k2, [route40, seed, l30], 3) ^ conn)
        put(route, 0x50, seed)
        put(route, 0x58, l30)
        put(route, 0x60, route60)
        put(route, 0x68, route68)
        put(route, 0x70, route70)
        put(route, 0x78, H(k1, k2, [0x3454554f524c4c43, q(route,0x40), q(route,0x48), q(route,0x50),
                                    q(route,0x58), q(route,0x60), q(route,0x68), 1], 8))
        grant = bytearray(0x218)
        grant[0x38:0x40] = TAG_GRANT
        put(grant, 0x40, 0x4444444444444444)
        put(grant, 0x48, H(k1, k2, [q(grant,0x40), route40, q(seal,0x30)], 3) ^ conn)
        put(grant, 0x50, seed)
        put(grant, 0x58, l30)
        put(grant, 0x60, route40)
        put(grant, 0x68, q(seal, 0x30))
        put(grant, 0x70, grant70)
        put(grant, 0x78, 0x5555555555555555)
        put(grant, 0x80, H(k1 ^ k2, (k1 + k2) & M64,
                           [mem, conn, seed, l30, route40, q(seal,0x30), route60, q(seal,0x50)], 8))
        put(grant, 0x88, 1)
        put(grant, 0x90, H(k1 ^ 0x13198a2e03707344, k2,
                           [0x34544e4152474c43, q(grant,0x40), q(grant,0x48), q(grant,0x50), q(grant,0x58),
                            q(grant,0x60), q(grant,0x68), q(grant,0x70), q(grant,0x78), q(grant,0x80), 1], 11))
        v = bytearray(0x108)
        v[0x28:0x30] = TAG_VOUCH
        put(v, 0x30, q(grant, 0x78))
        put(v, 0x38, q(grant, 0x40))
        put(v, 0x40, route40)
        put(v, 0x48, q(seal, 0x30))
        put(v, 0x50, seed)
        put(v, 0x58, l30)
        put(v, 0x60, v60)
        put(v, 0x68, 1)
        put(v, 0x70, H(k1 ^ 0x3c6ef372fe94f82b, k2,
                       [0x34524843554f5643, q(v,0x30), q(v,0x38), q(v,0x40), q(v,0x48),
                        q(v,0x50), q(v,0x58), q(v,0x60), 1], 9))
        return bytes(route), bytes(seal), bytes(grant), bytes(v)

    def run_chain(self):
        route, seal, grant, v = self.build_chain()
        for name, obj, exp in (("route", route, b"routed"), ("seal", seal, b"sealed"),
                               ("grant", grant, b"granted"), ("voucher", v, b"vouched")):
            st, body = self.h.q("op=%s&data=%s" % (name, obj.hex()))
            self.log(name, st, body[:40])
            if body.strip() != exp:
                self.log("FAILED at", name)
                return False
        st, body = self.h.q("op=commit")
        self.log("commit", st, body[:40])
        return body.strip() == b"activated"

    def relay(self, payload):
        st, body = self.h.q("op=broker&data=" + payload.hex())
        return st, body


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 19999
    h = Http(host, port)
    so = SoLayer(h)
    ok = so.run()
    print("so stage1:", ok)
    if ok:
        print("chain:", so.run_chain())
