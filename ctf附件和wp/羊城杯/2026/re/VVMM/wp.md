# 羊城杯 2026 —— VVMM Writeup

> **题目**：一层难后一重关，恢复 VM，找到藏在其中最美丽的姑娘。
> **赛事**：羊城杯 2026（DASCTF 平台）　**类别 / 难度**：REVERSE / MEDIUM（动态 200 分）
> **附件**：`VVMM.zip` → `VVMM.exe`（x64 PE，47.6 KB，MSVC，无壳）
> **Flag**：`flag{J1nxI_i5_4_6eautiful_g1rl}`

---

## 0x00 摘要

一句话概括：**这是一个自带调试 CLI 的自研字节码虚拟机（"VMVault"，容器格式 VMC2）。先逆出容器解密算法恢复全部 2 个入口（其中一个 magic 是 `0x0BADF00D` 的隐藏入口，被解码器故意跳过），再从 native 解释器的机器码里逐 handler 还原 5 个反直觉语义（内存 keystream 初始化、低 8 位旋转、字节截断存取、STAGE 隐藏变换、JNZ 反向跳转），最后论证整个校验流水线是字节级双射，从 31 个目标常数按块逆序精确求逆，一发命中。**

全程不需要爆破、不需要 Z3、不需要 hook——因为出题人把每一步都写成了可逆的字节运算，这是道"数学上必须唯一解"的题。坑全在语义层面：任何一个语义猜错，答案就是一串乱码。

---

## 0x01 侦察：自带调试器的 VM

解压得到 `VVMM.exe`，`strings` 一把就有完整的用法说明：

```
usage:
  %s                         launch the VM console
  %s --check <candidate>     verify one candidate
  %s --run <candidate>       execute the VM with a report
  %s --disasm [count]        disassemble decoded bytecode
  %s --layout                print VM image information
  %s --bof                   enter the BOF laboratory mode
```

`--layout` 直接交代了 VM 的底细：

```
vm container  : VMC2 / multi-entry encrypted bytecode
vm blob bytes : 20016
entries       : 2          ← 多入口，"藏在其中"的东西就在这
program bytes : 19696
instructions  : 2462
registers     : 8 x u32
memory        : 128 bytes
rounds        : 7 global rounds
```

`--disasm` 甚至能把解码后的字节码直接打出来（2462 条全给）。开局一眼：

```
0000  MAGIC  r0 r0 00  imm=0xc0def00d
0008  LEN    r0 r0 00  imm=0x0000001f      ← 长度必须 31
0010  JNZ    r0 r0 00  imm=0x0000099a  target=0x4ce8   ← 不对就跳 FAIL
0018  LDB    r0 r0 00  index=0
0020  XORI   r0 r0 00  imm=0x000000fb
0028  ADDI   r0 r0 00  imm=0x0000006a
0030  ROLI   r0 r0 00  imm=0x00000004
0038  STAGE  r0 r0 00  imm=0x00000000
0040  STM    r0 r0 00  index=0
...
```

尾部是 31 组 `LDM idx / CMPI8 target / JNZ FAIL`，逐字节比对最终内存。

`--run` 的报告行是本题最重要的 oracle：

```
[vm] steps=%zu pc=0x%zx acc=0x%02x zero=%u halt=0x%02x
```

`steps` 告诉你第一个失败的检查点在第几条指令，`acc` 直接吐出该位置算出来的字节值——后面全靠它校准模拟器。

---

## 0x02 恢复 VM：VMC2 容器与双入口

### 容器格式

容器在 `.rdata:0x140006f60`，解码器 `0x140002940`。逆向出的格式：

```
+0x00  u32  'VMC2'
+0x04  u8   version = 2        ← 同时是 entry 数量，循环 version 次
+0x08  连续排布的 entry：
         +0x00  u32 seed
         +0x04  u8  key
         +0x06  u16 size            （≤ 0x8000）
         +0x08  u32 checksum
         +0x0C  size 字节密文
下一个 entry 紧随其后
```

### 解密算法

```c
r9  = key ^ seed;
esi = key + (seed >> 11);            // keystream 状态，每字节 esi -= 0x59
h0  = r9 ^ 0x811c9dc5;               // checksum 初值

for i in 0..size-1:
    c = i * 0x45d9f3b;               // 32 位累加
    c = c ^ r9 ^ 0x9e3779b9;
    m = fmix32(c);                   // murmur3 finalizer（16/15/16 移位版）
    k = (m >> ((i & 3) * 8)) & 0xFF;
    out[i] = enc[i] ^ (esi & 0xFF) ^ k;
    esi -= 0x59;

// checksum：改版 FNV-1a
h = h0;
for b in out: { h ^= b; h *= 0x1000193; h ^= h >> 13; }
校验: (size ^ h) == checksum
     且 out[0] == 1
     且 u32(out[4:8]) == 0xc0def00d     ← 隐藏入口的伏笔！
```

### 两个入口

| entry | 偏移 | seed | key | size | checksum | 解码后 magic |
|---|---|---|---|---|---|---|
| 0 | 0x8 | `0x13572468` | 0x93 | 288 | `0xeeebf3c6` ✓ | **`0x0BADF00D`** |
| 1 | 0x134 | `0xb16b00b5` | 0xc7 | 19696 | `0x86b3869b` ✓ | `0xc0def00d` |

解码器的 magic 白名单只认 `0xc0def00d`，entry0 解出来对不上就**静默跳到下一个 entry**——所以二进制自己永远不执行 entry0。它就是"藏在其中"的部分：288 字节 = 36 条指令，实际内容是 **17 个伪装成指令的数据值**：

```
0000  MAGIC  imm=0x0badf00d
0008  MOVI   r0  imm=0xdead0000      XORI  r0  imm=0xa5a5a5a5
0018  MOVI   r1  imm=0xdeae2345      XORI  r1  imm=0xb4b4b4b4
...                                        （MOVI = 0xdead0000 + i*0x12345）
0108  MOVI   r0  imm=0xdebf3450      XORI  r0  imm=0xb4b4b4b5
0118  FAIL
```

纯彩蛋/标识数据，不参与校验。"恢复 VM"这一关的产物就是 `entry0.bin` + `entry1.bin` 两个完整的明文程序。

---

## 0x03 解释器语义还原（本题全部坑点）

先排个雷：`0x140002db0` 那个带 0x8058 栈帧的大函数**不是解释器**，只是 `--disasm` 的打印器（里面全是 `'%04zx  %-6s r%u r%u %02x  imm=0x%08x'` 和助记符字符串）。真正的解释器在 **`0x140003480`**，自己的跳转表在 `0x140006580`（0x52 项），运行上限 `steps < 0x4e20`。

逐 handler 读机器码，5 个语义和"直觉写法"都不一样：

### 坑 1：内存不是全零，是 keystream

解释器开头一段 SSE2 向量循环把 128 字节内存整体初始化：

```nasm
paddb xmm0, xmm12  ×7   ; i → 2i → 3i → 6i → 12i → 24i → 48i → 49i
paddb xmm0, xmm4       ; + 0x17
pxor   xmm0, xmm3      ; ^ 0xa5
```

即 **`mem[i] = ((0x31*i + 0x17) & 0xFF) ^ 0xA5`**。

mixing 轮里 `LDM index=(i+7)%31` 对 i≥24 会回卷读到 `mem[0..6]`，而对 i≤23 读到 `mem[i+7]` 最大到 37——**mem[31..37] 永远是这份 keystream，从没被写过**。不还原这条，第 4 轮之后就全错。

### 坑 2：ROLI/RORI 只转低 8 位

```nasm
; ROLI 0x24 @ 0x14000395e
mov  r12d, [rbp + rdx*4 - 0x40]
mov  eax, r12d
rol  al, cl                 ; ← 只转 al！
jmp  0x14000377f
; 0x14000377f: 高 24 位原样拼回去: regs[dst] = (old & 0xFFFFFF00) | rol8(low, cl)
```

x86 的 `rol r8, cl` 计数取 `cl & 0x1F`，8 位旋转模 8。程序里 imm ∈ 1..8，无碍。

### 坑 3：STM 截断 / LDM 零扩展

```nasm
; STM 0x13 @ 0x14000389b
and  ecx, 0x7f
mov  eax, [rbp + rdx*4 - 0x40]
mov  byte ptr [rbp + rcx - 0x20], al      ; 只存低字节
; LDM 0x12 @ 0x1400038b2
movzx eax, byte ptr [rbp + rcx - 0x20]    ; 读字节零扩展
```

与 `--layout` 的 "memory: 128 bytes" 呼应——内存是**字节数组**，寄存器才是 u32。

### 坑 4：STAGE 不是空操作，是一个 murmur 变换

```nasm
; STAGE 0x30 @ 0x1400038e5
movzx edx, byte ptr [rbp + r12*4 - 0x40]   ; 取 regs[dst] 低字节
call  0x140002d10                          ; stage(imm, value)
movzx eax, al
mov  [rbp + r12*4 - 0x40], eax             ; 返回值整个替换寄存器
```

`0x140002d10` + 内联的 fmix（`0x140002ce0`）逆出来是：

```python
h = fmix32(idx * 0x9e3779b9 ^ (0xa5 + 0x6d2b79f5))   # murmur finalizer, 13 移位版
def stage(idx, v):        # v 是字节, idx 是指令里的 imm（stage 槽位号）
    h  = fmix(idx, 0xA5)
    r8 = v ^ h                                   # 32 位 xor，v 只影响低字节
    cl = (3*idx + 1) & 0xFF
    r8 = (r8 & 0xFFFFFF00) | rol8(r8 & 0xFF, cl & 0x1F)
    edx = (h & 0xFFFFFF00) | ((h & 0xFF) >> 1)   # shr dl, 1
    eax = (r8 + 0x31*idx + 0x42) & 0xFFFFFFFF
    return (eax ^ edx) & 0xFF
```

每个 stage 槽位号（0x00..0x1e、0x40..0x118）对应一个独立的双射 S-box。**STAGE 只吃低字节、返回后高位清零**——phase-1 里 ADDI 进位产生的 bit8 就是在这里被丢掉的。

### 坑 5：JNZ 是"flag==0 才跳"

```nasm
; 0x140003830
cmp  byte ptr [rbp + 0x60], 0     ; 零标志
jne  next                          ; flag!=0 → 顺序执行
movsxd rcx, ecx
lea  rax, [r9 + rcx*8 + 8]         ; target = pc + imm*8 + 8
mov  r9, rax
```

CMPI8 是 `sete`（相等置 1），所以 JNZ 语义 = **不相等才跳**，target 按"指令条数"编码。与开头 `LEN; JNZ target=0x4ce8` 的行为吻合（长度错时 `steps=3 pc=0x4ce8` 实测验证）。

### 其余 handler（无坑，一一对号）

| opcode | 助记符 | 语义 |
|---|---|---|
| 0x00 / 0x01 | NOP / MAGIC | 空操作 |
| 0x10 | LEN | `flag = (imm == strlen(candidate))` |
| 0x11 | LDB | `regs[d] = (imm < len) ? cand[imm] : 0`（越界给 0） |
| 0x20..0x27 | MOVI/XORI/ADDI/MULI/ROLI/RORI/XORR/ADDR | u32 寄存器运算（旋转除外，见坑 2） |
| 0x30 | STAGE | 见坑 4 |
| 0x40 / 0x41 | CMPI8 / CMPI32 | `sete` 到零标志（CMPI8 比低字节） |
| 0x50 / 0x51 | JNZ / JMP | 见坑 5 |
| 0xF0 / 0xF1 | OK / FAIL | 停机，halt=0xf0/0xf1 |

---

## 0x04 校验逻辑建模

entry1 反汇编后结构完全规整（脚本正则解析 + 形状断言双确认）：

```
MAGIC; LEN 31; JNZ fail
×31:  LDB i / XORI a_i / ADDI b_i / ROLI c_i / STAGE i / STM i
      （夹着 MOVI r1/MULI r1/XORI r1 的死代码，r1 随后被覆盖，纯干扰）
×7 轮 ×31 块:                          ← STAGE 槽位 0x40..0x118 连续编号
      LDM r0, i
      LDM r1, (i+1)%31
      ADDR r0, r1
      LDM r1, (i+7)%31
      XORR r0, r1
      ROLI r0, k
      STAGE r0, 0x40 + round*31 + i
      ADDI r0, d
      STM i
×31:  LDM i / CMPI8 T_i / JNZ fail
OK
```

要点：块是**顺序就地更新**的——块 i 读的 `mem[i1]`、`mem[i2]`，若下标 ≤ i（回卷）则是本轮已更新的新值，否则是旧值。这决定了求逆时的处理顺序。

---

## 0x05 求解：因为可逆，所以秒杀

把语义代入后，每一步都落在**字节域**上：

```python
# phase-1（每字节独立）
mem[i] = stage_i( rol8(((flag[i] ^ a_i) + b_i) & 0xFF, c_i) )

# mixing（7 轮 × 31 块，顺序就地更新）
mem[i] = ( stage_s( rol8(((mem[i] + mem[i1]) ^ mem[i2]) & 0xFF, k) ) + d ) & 0xFF
```

- xor：双射
- mod-256 加法：双射
- rol8/ror8：双射
- stage：先 xor 常量、再 rol、再加常量、再 xor（`h>>1` 低字节）——双射

所以整条流水线是 31 字节空间上的双射，31 个 CMPI8 目标唯一确定输入。**按块逆序求逆**：

```python
for r in range(6, -1, -1):
    for j in range(30, -1, -1):
        b  = R[r][j]; i1, i2 = (j+1)%31, (j+7)%31
        y   = (mem[j] - b['d']) & 0xFF            # 去掉 ADDI d
        pre = stage_inv(b['s'], y)                 # 逆 STAGE
        x   = ror8(pre, b['k'])                    # 逆 ROLI
        mem[j] = ((x ^ mem[i2]) - mem[i1]) & 0xFF  # 逆 ADDR+XORR
        # 逆序处理保证 mem[i1]/mem[i2] 此刻的值 == 正向块 j 读取时的值
for i in range(31):
    pre = stage_inv(i, mem[i])
    flag[i] = ((ror8(pre, c_i) - b_i) & 0xFF) ^ a_i
```

唯一性顺带说明：不是"可打印 ASCII 里搜出一个解"，而是**全空间唯一解**——它恰好就是 flag。

---

## 0x06 Solver

`solve2.py` 的骨架（完整文件见附件）：

1. 从 `--disasm` / entry1.bin 解析出 `tparams(31)`、`R(7×31)`、`T(31)`；
2. 按 0x03 的语义实现模拟器 `run(candidate)`；
3. **先对拍再解题**：喂 `ABCDEFGHIJKLMNOPQRSTUVWXYZ01234`，模拟器输出

   ```
   steps=2370 pc=0x4ce8 acc=0xe9 zero=0 halt=0xf1
   ```

   与实机 `--run` **逐字段一致**（包括 acc=0xe9 这个中间值），语义确认无误；
4. 执行 0x05 的逆序求逆，再用模拟器复跑确认 `halt=0xf0`；
5. 实机验证。

```text
recovered flag: b'flag{J1nxI_i5_4_6eautiful_g1rl}'
emulator re-run: halt=0xf0 -> ACCEPT

$ ./VVMM.exe --check 'flag{J1nxI_i5_4_6eautiful_g1rl}'
accepted
$ ./VVMM.exe --run   'flag{J1nxI_i5_4_6eautiful_g1rl}'
[vm] ACCEPT
[vm] steps=2460 pc=0x4ce0 acc=0x2a zero=1 halt=0xf0
```

---

## 0x07 附一：`--bof`（另一重关，逆向用不到）

`0x140002860`：`fgets` 读 0x200 字节进 48 字节栈缓冲（`rbp-0x30`），返回地址偏移 **0x48**；循环异或**前 0x30 字节**，结果 == 0x42（'B'）则走 `[bof] checksum branch reached` 分支（`0x1400028f8`）。实测 64 字节开始踩返回地址（exit 65 / SIGSEGV）。这是同题的 pwn 衍生关卡入口，逆向本题不需要。

---

## 0x08 附二：`--audit` 的坑没踩到

`.rdata` 里有 `'[audit] checkpoint=%08x length=%zu'`（`0x1400027e0`，对 stage 数组做 FNV-1a）。正常路径打不出来，属于出题人埋的对拍后门，本题用 `--run` 报告就够，没再深挖。

---

## 0x09 踩坑记录

1. **别把 `0x140002db0` 当解释器**。它只是 disasm 打印器；真正的执行循环在 `0x140003480`，用的是另一张跳转表（0x140006580）。第一版"32 位寄存器 + 内存全零"模型就是从这里开始歪的。
2. **内存初始化 keystream 是最隐蔽的坑**。SSE2 向量循环长得像杂项，但它写的就是 `LDM/STM` 用的那 128 字节；mixing 第 4 轮起就会读到 `mem[31..37]`。不还原它，8 位/32 位怎么试都对不上。
3. **对拍要挑对 oracle**。`--check` 只有 accepted/rejected 两个状态，信息量太低；`--run` 的 `steps/pc/acc/zero/halt` 五元组能把"哪条指令失败 + 算出的字节值"同时钉死，一次对拍等于几十次 `--check`。实测 acc=0xe9 命中的瞬间就可以确定语义对了。
4. **steps 会差 1**：二进制到达 FAIL 指令即上报 halt=0xf1，`steps` 不含 FAIL 本身；模拟器按"执行过才计数"会多 1。纯口径问题，不影响求解，但对拍时要注意对齐。
5. **STAGE 的 imm 是槽位号不是装饰**。它参与 `fmix32`，每个槽位一个独立 S-box；phase-1 用 0x00..0x1e，mixing 用 0x40..0x118，同一函数 248 种密钥。漏掉它整个模型直接报废——这也是"STAGE 看起来像 nop"的最大陷阱。
6. **求逆顺序必须与正向读取时序互逆**。mixing 是顺序就地更新，块 j 读的 `mem[i1]`/`mem[i2]` 在回卷（j≥24 时 i2=j+7-31 < j）情况下是新值；逆序 undo 时恰好"未还原的槽位保持新值、已还原的槽位回到旧值"，天然对齐——但前提是严格按 30→0 处理。
7. **隐藏入口 entry0 的 magic 检查**（`out[4]==0xc0def00d`）兼具解码器自校验与"跳过隐藏 entry"两重作用。写容器解析器时要按"checksum 失败或 magic 不符 → 静默下一个 entry"实现，否则第一个 entry 就会把解码器卡死。
8. 环境花絮：全流程在 Windows 侧完成（`file`/`objdump` 缺失，用 Python `pefile`+`capstone` 手搓了节表、字符串 xref、`.pdata` 函数枚举与孤儿函数分析）。

---

## 0x0A Flag

```
flag{J1nxI_i5_4_6eautiful_g1rl}
```

> J1nxI is a beautiful girl. 一层难后一重关：容器解密（恢复 VM）→ 解释器语义（5 个坑）→ 双射求逆（一发命中）。完整解题脚本：`solve2.py`（模拟器 + 求逆器）、`recover.py`（VMC2 容器恢复）、`decode_hidden.py`（隐藏入口反汇编）。
