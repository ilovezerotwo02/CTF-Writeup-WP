# 七夕（qixi_gift）— PWN 1000pt

- 赛方：HTUCTF 2026
- 地址：`103.163.47.230:32846`
- Flag：`HTUCTF{I_love_you_0d6e93eb3d29}`
- 附件：`qixi_gift`

## 题目

> 男生收到女生留下的七夕互动贺卡。请你用 GDB 查找线索、打开礼物盒，最后读到女生留下的话。

## 附件分析

ELF64 PIE，Debian GCC 16.2 编译，参数 `-g -O0`，**符号表和 DWARF 全都在**，函数/全局变量名可以直接在 GDB 里引用。

```
$ readelf -h qixi_gift | grep Type
  Type:                              DYN (Shared object file)
$ readelf -sW qixi_gift | grep FUNC | grep -v UND
random_u64  random_u32  read_line  first_checkpoint  place_checkpoint
ribbon_checkpoint  gift_checkpoint  stage_one  stage_two  stage_three
stage_four  main
```

`main` 流程：

```
setvbuf(stdout, NULL, _IONBF, 0) × 3
puts 4 段说明文字
code = random_u32()
stage_one()  -> 失败 exit
stage_two()  -> 失败 exit
stage_three(code)
stage_four()
```

## 四关分析

四个 `*_checkpoint` 函数**函数体是空的**（只有 `push rbp; nop; pop rbp; ret`），纯粹是留给 GDB 下断点的位置——这就是题目唯一的设计意图。

### 第 1 关：卡片编号

```asm
stage_one:
    call random_u64          ; 随机 8 字节
    mov  qword [rbp-0x18], rax
    mov  r12, rax            ; ← 答案留在这里
    puts "[第 1 关：卡片编号] 编号放在 r12 寄存器中。"
    call first_checkpoint    ; ← 断点
    printf "输入编号（十六进制）：\n> "
    read_line(buf, 0x80)
    strtoull(buf, &end, 16)
    ... errno / endptr / 全字符串 检查 ...
    cmp  rax, qword [rbp-0x20]   ; 与 r12 里的随机值比较
```

答案每次运行都变（`getrandom(2)`），所以必须：

```gdb
break first_checkpoint
commands
  silent
  printf "[stage1] r12 = 0x%lx\n", $r12
  continue
end
```

`continue` 后把 `0x…` 原样填进去（程序用的 base 16）。

### 第 2 关：礼物地点

```asm
stage_two:
    puts "[第 2 关：礼物地点] 地点藏在 gift_place 字符串中。"
    call place_checkpoint
    printf "输入地点：\n> "
    read_line(buf, 0x80)
    strcmp(buf, gift_place)
```

`gift_place` 是 `.rodata 0x2010` 的全局常量串：

```
银桦大道第三棵树下
```

GDB 里直接 `x/s &gift_place` 就能读出来，也可以静态 dump。

### 第 3 关：丝带密码

```asm
stage_three:
    mov  dword [rbp-0xa4], edi    ; ← main 传来的 random_u32() 返回值
    puts "[第 3 关：丝带密码] 丝带编号每次运行都会改变。"
    mov  edi, [rbp-0xa4]
    call ribbon_checkpoint        ; ← 断点，$edi 就是答案
    printf "输入编号（可用十进制或 0x 开头的十六进制）：\n> "
    strtoul(buf, &end, 0)         ; base 0，自动识别 0x 前缀
    cmp  rax, 原值
```

```gdb
break ribbon_checkpoint
commands
  silent
  printf "[stage3] edi = %u (0x%x)\n", $edi, $edi
  continue
end
```

### 第 4 关：礼物盒

```asm
stage_four:
    puts "[第 4 关：礼物盒] 盒子还锁着。把 gift_box_open 改成 1，就能打开礼物。"
    call gift_checkpoint          ; ← 断点
    mov  eax, dword ptr [rip+...] # gift_box_open
    cmp  eax, 1
```

`gift_box_open` 是 `.bss 0x40ac` 的全局变量，符号表里就有，GDB 直接：

```gdb
break gift_checkpoint
commands
  silent
  set var gift_box_open = 1
  continue
end
```

## 一键脚本

`qixi_gdb.cmd`（把上面四个断点全自动化）：

```bash
gdb -q -x qixi_gdb.cmd ./qixi_gift
```

程序会依次打印 r12 的编号、gift_place 的字符串、edi 的密码，然后自动开盒，最后输出：

```
盒子打开了。里面有一张女生留下的卡片：
七夕快乐，我喜欢你。愿意和我在一起吗？
把这句话告诉礼物投递员，收下她为你准备的礼物。
```

## 远程

远程 `103.163.47.230:32846` **不是这个二进制**，而是一个「七夕礼物投递员」，只问一句话：

```
七夕礼物投递员：请告诉我卡片上的那句话。
>
```

把卡片上的话原样发过去即可：

```python
import socket
s = socket.create_connection(("103.163.47.230", 32846))
s.sendall("七夕快乐，我喜欢你。愿意和我在一起吗？".encode() + b"\n")
print(s.recv(4096).decode())
# 投递成功：他说的就是这句话。
# HTUCTF{I_love_you_0d6e93eb3d29}
```

对应脚本 `qixi_solve.py`。

## 总结

- 随机量全部来自 `getrandom(2)`，每次运行都变，远程二进制本身不可解，**只能本地 GDB 读运行时状态**。
- 二进制带 `-g -O0`，符号名/全局变量名可直接在 GDB 里用，定位答案几乎零成本。
- 第 4 关是纯粹的「改内存」教学点：`set var gift_box_open = 1`。
