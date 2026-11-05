---
title: "ScatterRSA — 带线性填充的 Hastad 广播攻击"
ctf: "内部密码学挑战赛"
date: 2026-06-01
category: crypto
difficulty: medium
points: 300
flag_format: "flag{...}"
author: "void"
---

## 1. 题目描述

同一明文 $m$（即 flag 的整数形式）被分别用三条不同的 RSA 通道加密：

$$
c_i \equiv (a_i \cdot m + b_i)^3 \pmod{n_i}, \qquad i = 1, 2, 3
$$

其中 $\{n_i, a_i, b_i, c_i\}$ 全部已知，指数固定为 $e = 3$。每个 $n_i$ 是
1024 位的 RSA 模数（由两个 512 位素数相乘得到），$a_i$ 为 129 位随机奇数，
$b_i$ 为 257 位随机奇数，均已随密文一同给出。

核心问题：**同一小消息在三条通道上被带有已知线性掩码的 RSA 加密了三次**，
这是 Hastad 广播攻击的变体。

## 2. 攻击原理

### 2.1 问题归约

对每条通道定义多项式：

$$
f_i(x) = (a_i x + b_i)^3 - c_i \equiv 0 \pmod{n_i}
$$

则真实消息 $x = m$ 同时满足三个同余方程。因为 $m \ll n_i$（约 256 位 vs
1024 位），可将三条方程通过 CRT 合并为一条模 $N = n_1 n_2 n_3$ 的多项式，
再使用 **Coppersmith 小根求解法** 恢复 $m$。

### 2.2 逐步推导

**第一步：展开每个通道的多项式系数。**

将 $(a_i x + b_i)^3 - c_i$ 按 $x$ 的幂次展开：

$$
\begin{aligned}
\alpha_{i,0} &= b_i^3 - c_i &\pmod{n_i} \\
\alpha_{i,1} &= 3 a_i b_i^2 &\pmod{n_i} \\
\alpha_{i,2} &= 3 a_i^2 b_i &\pmod{n_i} \\
\alpha_{i,3} &= a_i^3 &\pmod{n_i}
\end{aligned}
$$

**第二步：逐系数 CRT 合并。**

对每个次数 $k \in \{0, 1, 2, 3\}$，将三条通道的对应系数用中国剩余定理
合并，得到关于模数 $N = n_1 n_2 n_3$ 的全局三次多项式，再通过首项系数
求逆化为首一多项式 $f(x)$。

**第三步：构造 Coppersmith–Howgrave-Graham 格。**

对于首一三次多项式 $f(x)$，取移位多项式组：

$$
\{N,\; Nx,\; Nx^2,\; f(x),\; x f(x),\; x^2 f(x)\}
$$

每个多项式的最高次数不超过 $5$。将每个 $k$ 次项系数乘以 $X^k$（其中
$X = 2^{256}$ 为根的界），得到 $6 \times 6$ 的整数矩阵：

$$
\mathbf{B} =
\begin{pmatrix}
N & 0 & 0 & 0 & 0 & 0 \\
0 & N X & 0 & 0 & 0 & 0 \\
0 & 0 & N X^2 & 0 & 0 & 0 \\
f_0 & f_1 X & f_2 X^2 & f_3 X^3 & 0 & 0 \\
0 & f_0 X & f_1 X^2 & f_2 X^3 & f_3 X^4 & 0 \\
0 & 0 & f_0 X^2 & f_1 X^3 & f_2 X^4 & f_3 X^5
\end{pmatrix}
$$

**第四步：LLL 格基约简。**

使用 LLL 算法（取 $\delta = 0.99$）对上述格基进行约简，得到的最短向量
对应的多项式将以 $m$ 作为一个整数根。由于 $m$ 较小（约 256 位），该根
会落在多项式实根隔离区间的端点处，遍历前几行约简结果即可恢复。

## 3. 实现要点

- **高精度浮点**：LLL 的 Gram–Schmidt 正交化容易因舍入误差发散，此处使用
  `mpmath` 并设置 350 位十进制精度以确保数值稳定。
- **手写 CRT**：为避免引入不必要的依赖，使用增量式 CRT 自行实现，简洁且
  完全等价于 SymPy 的 `crt`。
- **$\delta = 0.99$**：与常见的 0.75 相比，更严格的 Lovász 参数会产生更
  短的约简向量，代价是少许额外的 swap 轮次，但对本场景收敛性更好。

## 4. 核心代码

完整脚本见 `exp_new.py`，以下是关键步骤：

```python
# 展开每条通道的多项式系数
for a, b, c, n in zip(a_list, b_list, c_list, n_list):
    c0 = (b**3 - c) % n          # 常数项
    c1 = (3 * a * b**2) % n      # x 一次项
    c2 = (3 * a**2 * b) % n      # x 二次项
    c3 = (a**3) % n              # x 三次项
    cubics.append((n, [c0, c1, c2, c3]))

# 逐系数 CRT 合并
for deg in range(4):
    residues = [coeffs[deg] for _, coeffs in cubics]
    val, _ = crt_combine(residues, n_list)
    global_coeffs.append(val % big_n)

# 化为首一多项式
lead_inv = pow(global_coeffs[3], -1, big_n)
monic = [(c * lead_inv) % big_n for c in global_coeffs]

# 构造移位格基 (X = 2^256)
B = 1 << 256
shifts = []
for s in range(3):
    row = [0] * 6; row[s] = big_n; shifts.append(row)
for s in range(3):
    row = [0] * 6
    for d in range(4):
        row[d + s] = monic[d]
    shifts.append(row)

mat = [[coeff * (B ** k) for k, coeff in enumerate(row)] for row in shifts]
reduced = lll(mat)          # δ = 0.99

# 从约简向量中提取候选根
for r in reduced[:3]:
    coeffs = [int(c) // (B ** k) for k, c in enumerate(r)]
    poly = Poly(sum(c * y**k for k, c in enumerate(coeffs)), y, domain="ZZ")
    for iv, _ in poly.intervals():
        for cand in {int(iv[0]), int(iv[1])}:
            if cand > 0 and all(
                pow((a * cand + b) % n, 3, n) == c
                for a, b, c, n in zip(a_list, b_list, c_list, n_list)
            ):
                return cand
```

## 5. Flag

```
flag{d3e053494a1280f3cff1c22c170069c0}
```
