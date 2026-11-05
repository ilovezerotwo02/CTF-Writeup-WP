# ISCC APK Native Crypto Writeup

**Challenge:** 密码验证 (Password Verification) — Mobile Reverse Engineering  
**APK:** attachment-23.apk  
**Flag format:** `ISCC{...}` (30 bytes inside)

---

## 1. 解包与初步分析

```bash
apktool d attachment-23.apk -o apk_out
```

关键目录：

```
apk_out/lib/x86_64/libnativecrypto.so   # native 校验核心
apk_out/assets/
  ├── cipher1.bin   (8 bytes)  — TEA 加密的第一段密文
  ├── cipher2.bin   (12 bytes) — GF(2^8) 矩阵加密的第二段密文
  ├── cipher3.bin   (10 bytes) — LCG 流加密的第三段密文
  └── puzzle.bin    (20 bytes) — 附加数据（可能用于交叉检验）
```

Java 层通过 `NativeBridge.verifyFlag(AssetManager, String)` 调用 native 校验。

---

## 2. Native 校验逻辑分析

从 `libnativecrypto.so` 的导出函数 `Java_com_example_crypto_NativeBridge_verifyFlag` 入手，逻辑为：

1. 检查输入是否以 `ISCC{` 开头，以 `}` 结尾
2. 总长度固定为 36 字节（`ISCC{` + 30字节 + `}`）
3. 花括号内 30 字节拆为三段：**p1 (8B) + p2 (12B) + p3 (10B)**
4. 三段分别使用不同算法校验
5. 三段之间存在交叉约束

---

## 3. 常量提取

`.rodata` 中有三组 16 字节的编码常量，经过解码变换：

```python
def decode_byte(b):
    return (((b - 0x13) & 0xff) ^ 0x5a) & 0xff
```

解码后得到：

```
C1 = 1a2b3c4d5e6f708192a3b4c5d6e7f809
C2 = 01000000000100000000010000000001
C3 = aabbccdd11223344556677889900feed
```

---

## 4. 中间值计算

### 变换 f1：C1 与 C3 异或后循环左移 3 字节

```python
def f1(a, b):
    d = bytearray(a)
    for i in range(min(len(a), len(b), 16)):
        d[i] ^= b[i]
    return bytes(d[3:] + d[:3])
```

结果：`v128 = 904f4d43c5c7c5c34d4fe706e4b090f0`

### 变换 f2：GF(2^8) 4x4 矩阵乘法 + 行置换

模多项式为 AES 的 `0x1b`。矩阵为 v128 逐字节作用于 C2，最后按 [2,3,0,1] 置换行。

结果：`v140 = 4d4fe706e4b090f0904f4d43c5c7c5c3`

### 变换 f3：三输入异或 → AES S-box → 前缀异或

```python
def f3(a, b, c):
    out[i] = AES_SBOX[a[i] ^ b[i] ^ c[i]]
    out[i] ^= out[i - 1]   # i from 1 to 15
```

结果：`v158 = f51f2c6a6e92a15490a362dfb3462439`

---

## 5. 反解第一段 p1（TEA 解密）

key 由 v128 按大端拆分为 4 个 32-bit 整数：

```
key = [0x904f4d43, 0xc5c7c5c3, 0x4d4fe706, 0xe4b090f0]
```

对 `cipher1.bin` (`0f06b976e2cd6f21`) 进行 TEA 16 轮解密，结果再与 v158 的旋转字节异或：

```python
rot = bytes(v158[(i + 1) % 16] for i in range(8))
p1 = tea_decrypt(cipher1, key) XOR rot
```

得到：`p1 = >/{%v65k`

---

## 6. 反解第二段 p2（GF(2^8) 矩阵求逆）

`cipher2.bin` (`2d4b5c2e6da4faa90cee6f18`) 是 3×4 的矩阵乘法结果：

```
cipher2 = v140 * p2  (在 GF(2^8) 上)
```

对 4×4 矩阵 v140 求 GF(2^8) 逆矩阵，再与密文相乘得到 p2。

得到：`p2 = oK7o8^7fo\e(`

---

## 7. 反解第三段 p3（LCG 流解密）

LCG 参数：

```
A = 0x5851f42d4c957f2d
C = 0x14057b7ef767814f
seed = v158 前 8 字节 = 0xf51f2c6a6e92a154
```

生成 10 字节伪随机流与 `cipher3.bin` 异或：

得到：`p3 = F5Z7i0crC#`

---

## 8. 最终 Flag

```python
flag = b"ISCC{" + p1 + p2 + p3 + b"}"
```

**Flag: `ISCC{>/{%v65koK7o8^7fo\e(F5Z7i0crC#}`**

---

## 9. 交叉约束验证

Native 代码中还包含两个交叉校验：

**约束 1：** `p2[0]` 与 `p1` 的循环冗余相关

**约束 2：** `hash_pair(p1 + p2)` 的 hash 值映射后应与 `p3[-2:]` 一致

```python
def hash_pair(data):
    x = 0; s = 0
    for b in data:
        x ^= b
        s = (s + b) & 0xff
    return x, s

# hash_pair(p1+p2) = (0x64, 0x44)
# p3[-2:] = 'C#' = (0x43, 0x23)
```

这两个约束由 native 代码自动验证，确保三段数据的完整关联。

---

## 10. 解题工具链

| 步骤 | 工具 |
|------|------|
| APK 解包 | apktool |
| Java 伪代码 | jadx |
| Native 反汇编 | IDA / Ghidra |
| 常量提取 | objdump + Python |
| 计算求解 | Python (capstone, pyelftools) |

---

## 参考

- TEA (Tiny Encryption Algorithm): 64-bit block, 128-bit key, 16 rounds
- AES S-box: 16×16 substitution table
- GF(2^8): AES finite field with irreducible polynomial x⁸ + x⁴ + x³ + x + 1
- LCG: Linear Congruential Generator
