# 强网杯 / yactf —— Reverse：ELFStudy WriteUp

> **题目附件**：`elfstudy_401568f195e6e6e12923a6b9687d14b5.zip`（内含 stripped 的 x86-64 PIE ELF `elfstudy`，43,304 字节）
>
> **Flag：`flag{4865f2079724968a95c217e0ff4db6c6}`**

---

## 0. 题目概览

`elfstudy` 是一个"ELF 结构查看器"（ELFStudy 1.4.2），用法：

```
usage: elfstudy [-q] [-p|-s|-y] [file|-]
```

运行后打印输入文件的 ELF header / program headers / sections，功能完全正常、没有任何显式的 flag 校验分支——**flag 藏在 ELF 文件结构本身**。本题考察对 ELF 加载流程（`ld.so` 重定位处理）的深度理解。

---

## 1. 静态分析：正常的部分

* stripped PIE，C++ 编写，导入 `fopen/__fread_chk/memcmp/Rb_tree(ostringstream)` 等。
* `main`（0x2a50）：解析参数 → `strncpy` 把 `argv[1]` 存入全局 `0xb1c0` → `fopen` 读文件到 0xb260 的静态 64KB 缓冲 → 调用 0x4080 生成输出行 → 0x3f60 打印 → **调用 0x3b30**（一个 8 条 `nop` + `ret` 的"空函数"）→ 退出。
* rodata / dynsym / 动态段看起来都正常。

## 2. 关键发现：两个"文件空洞"

逐节比对 section header / program header 的覆盖范围，发现有两块**不被任何 LOAD 段和任何 section 覆盖的死区**：

| 区域 | 范围 | 内容 |
|---|---|---|
| 空洞 1 | `0x1988 ~ 0x2000`（`.rela.plt` 结束 → `.init` 之前） | 22 条 24 字节的"伪 relocation"记录 |
| 空洞 2 | `0x7325 ~ 0x8000`（`.fini` 结束 → `.rodata` 之前） | 14 个清零的 qword（0x7325-0x7395）+ 高熵数据 0x7396-0x76c6 + 一份完整的 `.rela.plt` 副本（0x76c6 起，39×24=0x3a8 字节） |

## 3. 伪 relocation 记录（0x1988+）

22 条记录形如 `(r_offset, r_info, r_addend)`，其中藏着全部机关：

| 记录 | 含义 |
|---|---|
| `(0x3b34, IRELATIVE, 0x9090c300003861e8)` | **0x3b34 原始字节**：`e8 61 38 00 00 / c3 / 90 90` = `call 0x739a; ret` —— 现在 0x3b34 被nop成了 8 个 0x90 |
| `(0x920, IRELATIVE, 0xfff10a0000000000)` | dynsym[55] 原始 `{st_name=0, st_info=0x0a, st_shndx=0xfff1(SHN_ABS), ...}` |
| `(0x928, RELATIVE, 0x7325)` | 原始 dynsym[55].st_value = **0x7325**（指向隐藏数据起点） |
| `(0x958, RELATIVE, 0x76c6)` / `(0x960, IRELATIVE, 0x3a8)` | 原始 dynsym[57].st_value = **0x76c6**（指向 .rela.plt 副本）、st_size = **0x3a8** |
| 14 条 `(0x7325+k*8, R_X86_64_64, sym=0x37/0x39)` | 伪装成重定位的杂讯 |

也就是说：原二进制里 main 在退出前调用 0x3b30 → `call 0x739a`，执行藏在文件空洞里的**隐藏函数**；出题人随后把 call nop 掉、把 LOAD/section 范围改小形成空洞，把原始元数据以"relocation"形式存进空洞 1。

## 4. ld.so 运行时自解密机制（本题精髓）

动态段有两处刻意构造：

* `DT_RELASZ = 1512 (0x5e8)`，大于 `.rela.dyn` 实际大小（600 字节）——ld.so 会**多处理 38 条**、一直读到 0x1970，覆盖整个 `.rela.plt` 前段；
* `DT_FLAGS` 带 **TEXTREL**，允许 ld.so 写只读段。

`.rela.dyn` 里 4 条伪造 RELATIVE 记录把 **dynsym[57] 运行时改成 `SHN_ABS @ 0x1d30`**；而两条 **COPY 重定位** `(0x894, COPY, sym 0x39)`、`(0x15e0, COPY, sym 0x31)` 会把函数代码 `memcpy` 进重定位表区域，**污染 ld.so 接下来要处理的 .rela.plt**。被污染的"重定位条目"被 ld.so 当成代码路径继续走，最终导致 ld.so 在重定位阶段**执行了文件空洞 0x7325 处的代码**（gdb watchpoint 可见写入者帧为 `elf_dynamic_do_Rela` / `elf_machine_rela`）。

该段引导代码做两件事：

1. **滚动校验/解密** 0x7396~0x76c6 共 203 个 dword（`ecx` 从 0xcb 递减，地址 `0x7396+rcx*4`，即从 0x76c2 递减到 0x739a）：

   ```asm
   xor  eax, eax
   L:   xor  DWORD PTR [rdi+rcx*4], eax   ; mem ^= acc
        je   bail                         ; 结果为 0 → 检测到篡改，直接退出
        add  eax, DWORD PTR [rdi+rcx*4]   ; acc += 解密后的值
        loop L
   ```

2. **恢复调用点**：向 0x3b34 写回 `e8 61 38 00 00 c3`（`call 0x739a; ret`）。

## 5. 重建二进制

只需 3 个补丁即可让原程序跑通隐藏流程（`elfstudy_restored`）：

1. 0x3b34 写回 `e8 61 38 00 00 c3 90 90`；
2. 第一个 LOAD（R--）`filesz/memsz` 0x1988 → 0x2000（把空洞 1 映射进来）；
3. 第二个 LOAD（R-X）`filesz/memsz` 0x5325 → 0x6000（把空洞 2 映射进来）。

## 6. 隐藏函数（0x739a）分析

静态重放第 4 节的滚动解密即可还原完整代码（`decrypted.bin`），逻辑：

1. **反调试**：
   * `DT_DEBUG` → `r_debug` → `r_brk`（偏移 0x10，即 ld.so 的 `_dl_debug_state`），检查首字节是否 `0xCC`（gdb 对动态库事件下断会命中）；
   * `open("/proc/self/status")`，搜索 `"TracerPid:"`，跳过空白后要求字符为 `'0'`。
2. **校验 argv[1]**（全局 0xb1c0）：必须形如 `flag{` + 32 个 hex 字符 + `}`，总长 38。
3. 把 32 个 hex 字符解码成 16 字节 `P0 || P1`（两个 u64）。
4. 取 blob 内嵌密钥：`KEY_A = [0x7686]^ [0x768e]`，`KEY_B = [0x7696]^ [0x769e]`；
   `r8 = P0^KEY_A`，`r9 = P1^KEY_B`。
5. **密钥扩展**（Simon 风格，黄金比例常量 `0x9e3779b97f4a7c15`）：

   ```
   slot[0]=KEY_A, slot[1]=KEY_B
   slot[i] = rol64(slot[i-1] + slot[i-2], 13) ^ ror64(slot[i-2], 7) ^ (i * 0x9e3779b97f4a7c15)
   ```

6. **30 轮 Feistel**（i = 2..31，代码里 `(a|b)+(a&b)` 即加法、`(a|b)-(a&b)` 即异或）：

   ```
   F(x,k) = ( rol64(x + k, 13) ^ rol64(x, 29) ) + rol64(x, 47)
   每轮: (r8, r9) -> (r9, r8 ^ F(r9, slot[i]))
   ```

7. 与 blob 内目标 `T0=[0x76a6]`、`T1=[0x76ae]` 比较，成功则 `write(1, "flag accepted\n", 14)`。

实测常量：`KEY_A=0x1fa6bee7224fb586`，`KEY_B=0x56fc5596cf5bad58`，`T0=0x4fb335a84fa7d2d7`，`T1=0x02a183e3b4f4f49f`。

## 7. 求逆

Feistel 可直接逆推：从 `(T0,T1)` 按 `i=31..2` 反向（`r9 = r8; r8 = r9 ^ F(r8, slot[i])`），最后 `P0 = r8^KEY_A, P1 = r9^KEY_B`，得到 16 字节 `4865f2079724968a95c217e0ff4db6c6`。

## 8. 验证

```
$ ./elfstudy_restored 'flag{4865f2079724968a95c217e0ff4db6c6}'
ELFStudy: cannot open 'flag{4865f2079724968a95c217e0ff4db6c6}'
ELFStudy 1.4.2 — ELF structure inspector
...
flag accepted
```

## Flag

```
flag{4865f2079724968a95c217e0ff4db6c6}
```

---

## 附：一键求解脚本 solve.py

```python
import struct

data = open('elfstudy', 'rb').read()

# 1) 滚动解密 0x7396-0x76c6（203 个 dword，从高地址向低地址）
blob = bytearray(data[0x7396:0x76c6])
acc = 0
for c in range(203, 0, -1):
    off = c * 4
    v = struct.unpack_from('<I', blob, off)[0] ^ acc
    struct.pack_into('<I', blob, off, v)
    assert v != 0
    acc = (acc + v) & 0xffffffff

M = (1 << 64) - 1
rol = lambda x, n: ((x << (n % 64)) | (x >> (64 - n % 64))) & M
ror = lambda x, n: ((x >> (n % 64)) | (x << (64 - n % 64))) & M
g = lambda off: struct.unpack_from('<Q', blob, off - 0x7396)[0]

KEY_A = g(0x7686) ^ g(0x768e)      # slot[0]
KEY_B = g(0x7696) ^ g(0x769e)      # slot[1]
T0, T1 = g(0x76a6), g(0x76ae)
R = 0x9e3779b97f4a7c15

slot = {0: KEY_A, 1: KEY_B}
for i in range(2, 32):
    slot[i] = (rol((slot[i-1] + slot[i-2]) & M, 13) ^ ror(slot[i-2], 7) ^ (i * R & M)) & M

F = lambda x, k: ((rol((x + k) & M, 13) ^ rol(x, 29)) + rol(x, 47)) & M

r8, r9 = T0, T1
for i in range(31, 1, -1):
    r9, r8 = r8, r9 ^ F(r8, slot[i])
P0, P1 = r8 ^ KEY_A, r9 ^ KEY_B
print('flag{%s}' % struct.pack('<QQ', P0, P1).hex())
# flag{4865f2079724968a95c217e0ff4db6c6}
```

**工具**：readelf/objdump (llvm-mingw)、capstone、gdb (WSL Ubuntu 24.04)。
