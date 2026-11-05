# 强网杯 2026 线上赛 Reverse - license WriteUp

## 题目信息

- 附件：`license`（x86-64 静态链接 ELF，非 PIE）
- 提示：`give me your license, and you will get everything (ps:intel x86-64)`
- 输入：96 个十六进制字符，解码为 48 字节 license
- 最终 flag：

```
flag{9530b81c-61d0-2b62-3e96-f9a5e937f893}
```

对应 license（96 hex，也就是程序要求的输入）：

```
5b6c94d31d85e2344e666179a1d203ef02b5fdcb271d3d0500800cc020e00101600c20e000800ca14040e01a038260e0
```

## 0. 程序总览

`main`（0x402f9a）流程：

1. `sec_env_probe(0)`：反调试；
2. `wb_stream_emit` 打印 `please input your license: `；
3. `wb_read_line(0x5a9b20, 0x61)` 读入 96 个 hex 字符；
4. `chow_wb_encrypt`：白盒 AES 风格加密 + 3000 万次 LCG 掩码，结果写到栈上；
5. `wb_verify_fold`：把加密结果与 `wb_tgt`（0x57e3c0）比较，并把 `g_acc>>33` 写入 VM 上下文 `ctx+0xf`，随后调用 `ext_encoding_apply`（内部用 LCG 生成 0x80 字节、检查 `LIC\x01`，是诱导/装饰层）；
6. `sub_402e5b`：安装 SIGTRAP 处理函数（0x406000）、校验并 hex 解码输入到 `ctx+0x60`（ctx = 0x5aa360），生成 sin/S 盒等表；
7. `sub_4028d6`：`mprotect(0x404000, 0x80000, 7)`，置 TF 后 `jmp 0x404000`，进入 VM。

白盒层不是最终门：它比较的 `wb_tgt` 只是第一层校验，真正的接受/拒绝由 VM 决定。我们的 license 并不会让白盒比较通过（`edi≠0`），但 VM 通过后程序会直接打印 flag。

## 1. 反调试与 tracer

`sec_env_probe` 会检查：

- `/proc/self/status` 里的 `TracerPid`；
- `fork` 子进程 `ptrace(PTRACE_PEEKDATA, ...)` 比较；
- `rt_sigaction` 安装的 SIGTRAP 处理函数；
- 全局代码校验和（0x401000–0x5022E0，dword@0x50d845 设计为 0）与 `ctx+0x4C` 局部校验。

直接 patch 二进制会破坏 VM 的全局校验和（进入 VM 后 SIGILL），所以采用**自定义 ptrace tracer**（`tracer.c`）：

- 在 `read` 系统调用返回时把 `TracerPid:` 后的数字改成 0；
- 伪造 `PTRACE_ATTACH/PEEKDATA/DETACH`，让反调试走“未检测到”分支；
- 原样传递 SIGTRAP（VM 用 TF 单步，必须让它自己的 0x406000 处理）；
- 支持 `ctxat:N` / `regat:N` 在指定 trap 转储 VM 上下文与寄存器。

## 2. VM 的 license 检查

VM 是一台“自解密 + TF 单步”的解释器：

- 0x406000 的 SIGTRAP handler 每次取 16 字节块，用由 `ctx` 状态派生的哈希决定**下一块地址**并解密；
- 驱动哈希有 4 个 bank（0x404000/0x404800/0x405000/0x405800），bank 由 `ctx+8 & 3` 选择，`ctx+0xa` 混入哈希；
- `ctx+0xa` 同时是 VM 的“校验累加器”，各段代码会把计算出的字节异或进去。

进入 VM 后，程序先把 `ctx+0x60..0x77`（license 前 24 字节）复制到 `ctx+0x90..0xA7`，然后做变换 T：

1. **3 轮 Feistel**，对三个 64-bit 对：`(0x90,0x9C)`、`(0x94,0xA0)`、`(0x98,0xA4)`；
   每轮：`(x,y) -> (y, x ^ F_r(y))`，F 为 4 个 S 盒 + 线性异或（每轮 12 个 S 盒查表，所有常数从 trace 中提取）。
2. `S4 = state ^ license`。
3. **线性层**：把 `S4`（24 字节）线性混合到 `ctx+0xA8..0xBF`，矩阵记作 `NA`（24×24，字节级 GF(2) 矩阵，可从指令流直接提取）。

随后 VM 做两件事：

- **首判定**：`ctx+0xa` 异或 `A8[0]` 后必须等于 0x5F64，即
  `(NA·S4 ^ S4)[0] == 0x8F`；
- **主检查**：`A8 块 ^ 0x90 块` 与 `ctx[0xC0] ^ ctx[0x200]` 逐字节比较。
  其中 `ctx[0xC0] = edcab103d9cc7285b8e39c5ff1dfac3598285f93c3899c35`（sin 表生成），
  `ctx[0x200]` 为 24 个 0xE5，所以目标值为：

```
EXP = 082f54e63c2997605d0679ba143a49d07dcdba76266c79d0
```

即要求 `NA · S4 = EXP`。

## 3. 反演 T：求前 24 字节

### 3.1 线性层

`NA` 可逆。由 `NA · S4 = EXP` 直接解出：

```
S4 = 8721a19db336fdb91f3f6f5b9a2adcdc0b53034b6a8a0324
```

此时首判定自动满足：`(NA·S4 ^ S4)[0] = 0x8F`，`S4[0] = 0x87`。

### 3.2 Feistel 的反演

对每个 64-bit 对：`S4_pair = F(x,y) ^ (x,y)`，其中

```
u = x ^ F1(y)
v = y ^ F2(u)
F(x,y) = (v, u ^ F3(v))
```

记 `H(y) = y ^ F1(y)`。关键观察：F1 的线性混合是“三角形”的，可由 `H` 的四个字节直接反解出 `y`（例如 pair0 的 H 反解）：

```
t2 = H1, t1 = H2, t3 = H1^H3, t0 = H0^H2^H3
y2 = SI[t0]^0xd6 ^ SI[t2]^0x28
y1 = SI[t1]^0x80 ^ y2
y3 = SI[t3]^0x60 ^ SI[t1]^0x80
y0 = SI[t2]^0x28 ^ y1 ^ y3
```

于是给定 `S4_pair = (P,Q)`，对 `x` 枚举 2^32：

1. 令 `C = Q ^ x ^ F3(P ^ x)`；
2. `y = H^{-1}(C)`；
3. 校验 `P == x ^ y ^ F2(x ^ F1(y))`。

用 C + OpenMP（`license_bf.c`）三对并行枚举，几十秒内得到：

- pair0：2 个解，pair1：3 个解，pair2：1 个解，共 **6 个前缀候选**。

## 4. 尾部 24 字节：VM 的反篡改链

主检查通过后，VM 还要处理 `license[24..47]`（`ctx+0x78..0x8F`）。这段代码是 24 份几乎相同的“结构更新”拷贝（每份约 0xE00 字节，指令被逐块加密）：

- 每份读取一个 license 字节；
- 用高 3 位选分支、低 5 位做移位，更新 `ctx+0xE0..0xEF` 的 16 字节状态，并用 S 盒/ROR/ADD 混合；
- 把结构字节与 license 字节异或进 `ctx+0xa`；
- 驱动用 `ctx+0xa` 等状态做哈希，决定**下一块的地址**并解密。地址若不对，就会跳到未解密的“乱码”上崩溃。

求解方式（逐字节）：

1. 用 tracer 在下一个 dispatch 的 trap 处 `ctxat`/`regat` 或 watch `ctx+4`，拿到 `ctx` 与 `rbx`（varint 游标）、`ctx0 = rip-base`；
2. 对 4 个 bank 的驱动哈希建模（例如 bank2）：
   `ecx = (ctx+0xa)*0xC6AF + (ctx+8) ^ 0x72CF ^ ...`，再乘 0xB2F1、与 `[base+0x2000]*const` 混合、mix 链；
3. 对 256 个候选字节修改 `ctx+0xa` 低字节，重算哈希与目标地址；
4. 用哈希派生的 keystream 解密目标块，要求其首指令为 `89 C2`（`mov edx,eax`，即下一份结构拷贝的开头）；
5. 命中即该位置的 license 字节。

最终求得尾部：

```
00800cc020e00101600c20e000800ca14040e01a038260e0
```

## 5. flag 生成与最终前缀选择

尾部链走完后，`ctx+0xd = 1`，VM 进入 flag 生成循环（同样是 24 份展开的拷贝）。每个字节：

```c
idx = (r13 ^ r8 ^ r10 ^ (r15 * 0x3dfd6041)) & 0xff;
flag[r15] = SBOX[idx] ^ mem[0x5aa320 + r15];   // 写到 ctx+0x1c8
```

后面的 PRNG 更新代码还会读取 license 字节（例如 `ctx+0x7e`、`ctx+0x6c` 等）来更新 `ctx+0xa` 并决定下一次派遣。

6 个前缀候选分别测试后，只有：

```
前缀 = 5b6c94d3 1d85e234 4e666179 a1d203ef 02b5fdcb 271d3d05
```

能使 flag 循环的哈希链正确，`ctx+0x1c8` 依次生成 `flag{...}`，最后 `sub_402995` 的完成回调调用 `puts(ctx+0x1c8)` 输出：

```
flag{9530b81c-61d0-2b62-3e96-f9a5e937f893}
```

## 6. 复现

完整 license（96 hex）：

```
5b6c94d31d85e2344e666179a1d203ef02b5fdcb271d3d0500800cc020e00101600c20e000800ca14040e01a038260e0
```

直接运行原始二进制会被反调试拦截/干扰，需在 tracer 下运行（处理 TracerPid、伪造 ptrace、放行 SIGTRAP）：

```bash
gcc -O2 -o tracer tracer.c
./tracer ./license in_license.txt
# 程序输出:
# please input your license: flag{9530b81c-61d0-2b62-3e96-f9a5e937f893}
```

其中 `in_license.txt` 内容为上面的 96 个 hex 字符。

## 7. 关键文件

| 文件 | 说明 |
| --- | --- |
| `license` | 原题附件 |
| `license_final.txt` | 可用的 license 与 flag |
| `tracer.c` | ptrace 反反调试 + VM 单步 tracer |
| `feistel_fwd.py` | 从 trace 提取的 T 正向模型（已用真实状态校验） |
| `lin_extract.py` / `lin_solve.py` | 线性层 NA 提取与求逆 |
| `h_inv_test.py` | H(y)=y^F1(y) 的三角反解验证 |
| `gen_bf.py` / `license_bf.c` | 每对 2^32 的 Feistel 反演（OpenMP） |
| `vm_solve.py` / `vm_emu.py` | VM 的符号/具体仿真（校验状态） |
| `trap_solver.py` / `analyze_event.py` / `scan_hits.py` / `chain_solve4.py` | 尾部链逐字节求解（驱动哈希 + 解密块 89C2 判定） |
| `dispatch_bank2.py` / `dispatch_calc.py` | 驱动哈希（bank）建模与校准 |
| `gen_combos.py` / `run_combos.sh` | 6 个前缀候选的测试 |
| `regs_stores.sh` | flag 循环各次 PRNG 寄存器采样 |
| `wp.md` | 本 WriteUp |

## 8. 小结

- 第一层白盒 AES + 3000 万次 LCG 掩码是幌子，真正的门是第二阶段的自解密 VM；
- VM 用 `ctx+0xa` 把 license 字节耦合进“下一次取指地址”，形成逐字节反篡改链；
- 检查函数本身是可逆的：3 轮 Feistel + 字节线性层，用 `H(y)` 三角反解把 2^64 降成 3×2^32；
- flag 不在二进制里，而是 VM 通过后由 PRNG 在 `ctx+0x1c8` 逐字节生成并打印。
