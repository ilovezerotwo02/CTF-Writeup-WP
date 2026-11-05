# 强网杯 2026 线上赛 · 密码 · vmshare Writeup

> **Flag：`flag{3174812_31af718}`**
>
> 附件：`vmshare_6d3416fb746f85cad8020e41571f8b7b.zip`（`encryptor` + `cipher.bin`）
> 题目分值 264.00（动态积分）

---

## 1. 附件初探

```
cipher.bin    32 字节密文
encryptor     ELF64 PIE, x86-64, stripped，.text 仅 0x65d 字节
```

```bash
$ xxd cipher.bin
e717f224 9f53836b 6e1792c0 1ddf37d4 3782463c e9671154 6045b23d dd537527
```

`strings` 直接把题目意图写脸上了：

```
wrote %u bytes to %s
error: flag must match flag{XXXXXXX_YYYYYYY}
       where each XXXXXXX/YYYYYYY is 7 uppercase hex digits
usage: %s flag{XXXXXXX_YYYYYYY} [out.bin]
       (or place the flag in flag.txt)
SIMD_TINY_BLOCK_IS_A_NIGHTMARE!!
```

结论：**明文是固定串 `SIMD_TINY_BLOCK_IS_A_NIGHTMARE!!`（32 字节），flag 的两段各 7 个十六进制字符被当作密钥**，题目本质是"已知明文 + 已知密文，恢复 56 bit 密钥"。

---

## 2. 逆向 encryptor

### 2.1 main 流程（0x1eb0）

1. `argc<=1` 读 `flag.txt`，否则取 `argv[1]`；输出文件默认 `cipher.bin`。
2. 校验 flag：`strlen==21`、前缀 `flag{`、`flag[20]=='}'`、`flag[12]=='_'`、其余 14 个字符必须是十六进制（大小写都收）。
3. 把 flag 拼进 16 字节 key 材料缓冲区（**两段之间用一个 NUL 隔开**）：

   ```
   buf[0..6]  = "XXXXXXX"     buf[7]  = 0
   buf[8..14] = "YYYYYYY"     buf[15] = 0
   ```
4. `strtoul(buf,0,16)` → `X`；`strtoul(buf+8,0,16)` → `Y`。
5. 两次密钥扩展 `fn()`（0x1c60）：
   - `fn(X, 0x31415926)` → 16 字节 `k1`
   - `fn(Y, 0x27182818)` → 16 字节 `k2`
6. 两次核心变换 `transform()`（0x1cc0）：`ymm0 = P` → `transform(ymm0,k1)` → `transform(ymm0,k2)`
7. 把 `ymm0` 写文件。

即 **`C = E_{k2}( E_{k1}( P ) )`**。

### 2.2 密钥扩展 fn（0x1c60）

```asm
1c60: mov  eax, edi
1c62: and  eax, 0xffffff      ; ★ 只取低 24 bit（第 4 节详述）
1c67: xor  eax, esi           ; ^= salt
1c69: xor  esi, esi           ; 计数器清零
1c6b: ... eax ^= eax>>13; eax *= 0x45d9f3b; eax ^= eax>>16
1c80: loop:
       eax = eax + esi - 0x61c88647   ; += 0x9e3779b9
       esi += 0x7f4a7c15              ; 黄金分割高 32 位
       ecx = (eax>>13) ^ eax
       ecx *= 0x85ebca6b
       eax = ecx ^ (ecx>>16)
       store16( (eax ^ (eax>>16)) & 0xffff )
     until esi == 0xfa53e0a8
```

`esi` 从 0 开始每次加 `0x7f4a7c15`，第 **8** 次恰好等于 `0xfa53e0a8`：

```
8 * 0x7f4a7c15 mod 2^32 = 0xfa53e0a8
```

所以 `fn()` 输出 **8 个 16 bit 小端字（16 字节）**。

> 调试提示：`0x1c69` 的 `xor esi,esi` 很容易看漏，会误以为循环计数用的是 salt 本身，从而算错迭代次数。gdb 在 `0x204e` 处 dump 内存即可核对：
> ```
> k1 = 36 d2 e6 35 12 f6 ff 69 61 aa 1e 16 16 4e ed b5     (X=FFFFFFF, salt=0x31415926)
> k2 = fe fb 33 86 8c 8c 03 3a 17 90 82 cb 4e 86 6c 97     (Y=FFFFFFF, salt=0x27182818)
> ```

### 2.3 核心变换 transform（0x1cc0）

整个函数被 GCC 展开成 **8 段几乎相同的 AVX2 指令**，每段是一轮，**全部在 16 条 16 bit lane 上并行**（`vpaddw/vpxor/vpsrlw/vpsllw`，没有任何跨 lane 操作 ⇒ 16 条 lane 完全独立，只是共享同一个 16 bit 轮密钥）。

第一轮（唯一带"前置 xor-shift"的一轮）：

```asm
vpsrlw ymm0, ymm0, 0x5      ; x>>5
vpxor  ymm0, ymm0, ymm1     ; x ^= x>>5      ← 前置，整段变换只做一次
vpsrlw ymm3, ymm0, 0xd
vpsllw ymm1, ymm0, 0x3
vpbroadcastw ymm0, [rdi]    ; k[0]，广播到所有 lane
vpor   ymm1, ymm1, ymm3     ; rotl16(x,3)
vpaddw ymm0, ymm0, ymm2     ; k + T
vpaddw ymm0, ymm0, ymm1     ; k + T + rotl16(x,3)
vpsrlw ymm1, ymm0, 0x7
vpxor  ymm0, ymm0, ymm1     ; x ^= x>>7
vpsrlw ymm1, ymm0, 0x7
vpsllw ymm0, ymm0, 0x9
vpor   ymm0, ymm0, ymm1     ; x = rotl16(x,9)
vpsrlw ymm1, ymm0, 0x5
vpxor  ymm0, ymm0, ymm1     ; x ^= x>>5
```

后面 7 轮只是把 `[rdi]` 换成 `[rdi+2] … [rdi+0xe]`，**并且省掉了开头那句 `x ^= x>>5`**（编译器把不变量提到了循环外）。

**最后一轮（0x1e78）**：`rotl16(x,9)` 之后直接 `ret`，**少了结尾的 `x ^= x>>5`**（尾部循环展开的"少做一步"）。这处细节如果按 8 轮对称处理，解密结果会全错。

`T` 常量表（0xa60，16 个 16 bit 字，**逐 lane 不同**）：

```
1357 2468 369c 48ad 5be1 6cf2 7d03 8e14 9f25 a036 b147 c258 d369 e47a f58b 069c
```

于是单条 lane 的轮函数是（`k_r` = 第 r 轮轮密钥，`T_j` = 该 lane 的常量）：

```
x ^= x >> 5                          # 仅整个变换开始前一次
r = 0..7:
    x = k_r + T_j + rotl16(x,3)      # mod 2^16
    x ^= x >> 7
    x = rotl16(x,9)
    x ^= x >> 5                      # 第 8 轮（最后一轮）不做
```

8 轮 × 8 个密钥字 = 正好把 `fn()` 产出的 16 字节用完。

### 2.4 算法小结

```
P  = "SIMD_TINY_BLOCK_IS_A_NIGHTMARE!!"     (32B, 16 条 16bit lane)
k1 = fn(X, 0x31415926)  (16B)     X = flag[5:12]  按 16 进制解析
k2 = fn(Y, 0x27182818)  (16B)     Y = flag[13:20] 按 16 进制解析
C  = T_{k2}( T_{k1}( P ) )        (两段各 8 轮，16 lane 并行)
```

参考实现见 `sim3.py`（已与官方 `encryptor` 对拍 5 组测试向量全部一致）。

---

## 3. 攻击：中间相遇（MITM）

未知量 `X`、`Y` 各 28 bit，合计 2^56，直接爆破无解。但结构非常友好：

* **前 8 轮只依赖 k1（只依赖 X）**，后 8 轮只依赖 k2（只依赖 Y）；
* 变换是**逐 lane 的置换**，每轮可逆。

于是可以在中间状态 `U = T_{k1}(P)` 上做**中间相遇**：

```
正向：  U(X) = T_{k1}(P)          for X in 0..2^28-1     (8 轮前向)
反向：  U(Y) = T_{k2}^{-1}(C)     for Y in 0..2^28-1     (8 轮逆向)
求 U(X) == U(Y)
```

复杂度 2^28 + 2^28 ≈ 2^29 次 8 轮变换，完全可行。

**逆变换**（`rotl` 的逆是 `rotl(16-n)`；`x ^= x>>s` 的逆是倍增 xor-shift `y^y>>s^y>>2s^…`，位移 <16 为止）：

```
for r = 7..0:
    if r < 7: x = unxorshift(x,5)
    x = rotl16(x,7)          # rotl9 的逆
    x = unxorshift(x,7)
    x = x - k_r - T_j        # mod 2^16
    x = rotl16(x,13)         # rotl3 的逆
x = unxorshift(x,5)          # 前置 xor-shift 的逆
```

> 坑：`unxorshift(y,5)` 一开始写成 `y^y>>5^y>>10^y>>15`，多算了一项（正确是倍增形式 `5,10` 两步，16 bit 下 `>>15` 项已含在 `y>>10` 里），结果解出来的状态全错。写完最好用暴力枚举 0..65535 校验一遍。

### 3.1 内存问题：48 bit 指纹 + Bloom 过滤

2^28 条中间状态 × 32 字节 = 8.6 GB，存不下。做法：

1. 只取 **3 条 lane（48 bit）** 作为指纹 —— 2^28 个 48 bit 指纹两两碰撞期望仅 `2^56/2^48 = 256` 个，后面逐一精确验证即可；
2. 正向表用 **512 MB 的 Bloom filter（2^32 bit，k=4）** 存，误判率约 0.24%；
3. 反向扫到的候选指纹放进哈希表；
4. 再正向扫一遍找回 X，最后用**完整 16 条 lane** 做精确比对。

三轮扫描 + Bloom，内存峰值 < 1.5 GB。

### 3.2 实现与性能

`solve.c`：C + AVX2 intrinsics + OpenMP（WSL/Ubuntu 24.04，20 核，16 线程）。

* 一颗种子 = 一个 `__m256i`，16 条 lane 一次算完；
* `fn()` 标量实现（每种子 ~8 次乘法）；
* Bloom 用 `__atomic_fetch_or` 保证多线程正确（避免丢 bit 造成漏解）。

```
[pass1] forward bloom done,  8.86s      # 2^28 次正向
[pass2] backward candidates: 16, 12.23s  # 2^28 次逆向 + Bloom 查询
[pass3] hashset built, 12.23s
*** MATCH flag{?174812_?1AF718}
[done] 16 match(es), total 12.84s
```

**13 秒出结果**，比暴力快 20 个数量级。

---

## 4. 结果与出题人的两个"坑"

MITM 得到唯一解：

```
X ≡ 0x174812 (mod 2^24)        Y ≡ 0x1AF718 (mod 2^24)
```

### 坑 1：`and eax,0xffffff` —— 每段首位十六进制字符完全无用

`fn()` 第一条指令把种子截断到 24 bit，所以 flag 每段的**最高 4 bit（也就是第 1 个十六进制字符）根本不参与运算**：

```bash
$ ./encryptor 'flag{0174812_01af718}' a.bin
$ ./encryptor 'flag{3174812_31af718}' b.bin
$ cmp a.bin b.bin && cmp b.bin cipher.bin && echo "三个密文完全相同"
三个密文完全相同
```

⇒ 严格来说有 **16 × 16 = 256 个等价 flag**，再叠加大小写，最多 512 个。

### 坑 2：大小写

作者实际用的是**小写十六进制**（`1AF718` 实为 `1af718`）。所以按 `%07X` 习惯写出的 `flag{0174812_01AF718}` 虽然能加出同样的密文，却不是平台要的 flag。

### 最终答案

```
flag{3174812_31af718}
```

验证：

```bash
$ ./encryptor 'flag{3174812_31af718}' out.bin
wrote 32 bytes to out.bin
$ cmp out.bin cipher.bin && echo SAME
SAME
```

> 巧合的是，两段的首位恰好都是 `3`——这也是本题最容易猜中的一种形态（"两段同首位"）。
> 定位这两个坑的代价：大写空间 237 条逐条提交（平台有频率限制，连发会提示"操作太过频繁"），
> 最后改用小写空间枚举才命中。

---

## 5. 复现步骤

```bash
# 1) 参考实现自检（对照 5 组已知明文/密文）
python3 sim3.py

# 2) 编译求解器（约 13 秒解出 24 bit 有效密钥）
gcc -O3 -mavx2 -fopenmp -o solve solve.c
OMP_NUM_THREADS=16 ./solve cipher.bin

# 3) 用官方 encryptor 验证最终 flag
./encryptor 'flag{3174812_31af718}' out.bin && cmp out.bin cipher.bin
```

---

## 6. 小结

| 设计点 | 对攻击者的影响 |
| --- | --- |
| 16 条 16 bit lane 并行、共享轮密钥 | lane 相互独立，但轮密钥跨 lane 共享 ⇒ 只能整体爆破 |
| 密钥 = flag 两段（28 bit × 2） | 2^56 直接爆破不可行 |
| 前后 8 轮密钥分离 | 天然可做中间相遇 2^28 + 2^28 |
| 常量 T 逐 lane 不同、末轮少一步 | 增加逆向细节，但都是可逆的 XOR/ADD/ROT 组合 |
| `seed & 0xffffff` | 白送 4 bit，也带来 256 重歧义 |
| flag 用小写 hex | 按 `%07X` 习惯会写错，需要额外确认 |

最终：**`flag{3174812_31af718}`**，MITM 13 秒恢复 24 bit 有效密钥，再逐一枚举两个首位 + 大小写即可锁定。

---

## 7. 附件说明

| 文件 | 说明 |
| --- | --- |
| `vmshare_6d3416fb...zip` | 原始附件 |
| `cipher.bin` / `encryptor` | 解包后的题目文件 |
| `sim3.py` | 算法 Python 参考实现（已对拍验证） |
| `solve.c` | MITM 求解器（C + AVX2 + OpenMP，13 秒出解） |
| `brute.js` / `brute_lower.js` | 平台提交枚举脚本（大写 / 小写空间），用于确定两个首位与大小写 |
| `candidates.txt` / `todo.txt` | 等价候选清单（512 个）及状态标注 |
