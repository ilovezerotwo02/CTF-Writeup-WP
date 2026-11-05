# ECB Pattern Leakage — 完整 Writeup

## 题目信息

- **题目名**: ECB Pattern Leakage
- **分类**: CRYPTO
- **分值**: 300（中级）
- **附件**: `otp_10.zip` → `ciphertext.bin`（80 字节）

## 一、附件分析

### 1.1 解压附件

```powershell
Expand-Archive -LiteralPath .\otp_10.zip -DestinationPath .\otp_10_unzipped -Force
```

解压后只有一个文件 `ciphertext.bin`，80 字节，正好 5 个 16 字节分组。

### 1.2 ZIP 元数据检查

| 属性 | 值 |
|------|-----|
| 文件名 | ciphertext.bin |
| 原始大小 | 80 bytes |
| 压缩方式 | 0 (存储，未压缩) |
| CRC32 | 0xb5ebaf64 |
| 修改时间 | 2026-04-01 10:45:48 |
| ZIP 注释 | 无 |
| 额外数据 | 无 |

ZIP 中**没有隐藏数据**（无注释、无额外字段、无后置数据）。

### 1.3 密文分块

```
Block 00: 97c266c5b1c929e1ac07ccf592599dd8
Block 01: b577f3f777783d3b8f6ab17acd3f78c9
Block 02: 6b2afc84559d6443c042f6225b6dcb7d
Block 03: 56a4c94a9d532bf7d045f14b00990253
Block 04: 84163f757a2ab28337aefa7aeb72e087
```

5 个分组全部不同，**没有任何重复分组**。

## 二、ECB Pattern Leakage 原理

ECB 模式的性质：

```
相同的 16 字节明文分组 + 相同的密钥 → 相同的 16 字节密文分组
```

这个特性只能泄露**哪些分组相同**这一种信息。要从 ECB pattern leakage 恢复完整明文，通常还需要：

1. **已知密钥** — 直接 AES-ECB 解密
2. **加密 Oracle** — Byte-at-a-time ECB 攻击，逐字节爆破
3. **多份同密钥密文** — 通过分组碰撞建立 codebook 映射
4. **明文高度重复** — 例如加密的位图图像（经典 ECB 企鹅图）

## 三、本题为什么无法求解

本题**不具备上述任何附加条件**：

| 条件 | 本题情况 |
|------|----------|
| 密钥 | ❌ 未提供 |
| 加密 Oracle | ❌ 未提供 |
| 多份同密钥密文 | ❌ 只有 1 份 |
| 重复分组 | ❌ 5 个分组全部不同 |
| 已知部分明文 | ❌ 未知 |

### 3.1 已尝试的解密方法（全部失败）

| 方法 | 尝试范围 | 结果 |
|------|----------|------|
| AES-128-ECB 密钥搜索 | 2000+ 候选密钥（含 MD5/SHA 派生） | 无 |
| AES-192/256-ECB | SHA-256/512 派生密钥 | 无 |
| DES/3DES-ECB | 常见密钥 100+ | 无 |
| Blowfish-ECB | 常见密钥 | 无 |
| XOR 暴力破解 | 1-3 字节全空间，4-5 字节可打印字符 | 无 |
| ROT-N 加/减 | 全部 256 种偏移 | 无 |
| ECB/CBC/CFB/OFB/CTR | 各种常见 IV | 无 |
| PKCS#7 填充验证 | 370,000+ 密钥 | 仅误报 |
| MD5(3 字符) 密钥 | ~705,000 个 | 无 |
| MD5(4 字符小写) 密钥 | ~1,874,000 个 | 无 |
| PBKDF2/HKDF/scrypt | 常见参数组合 | 无 |
| 块排列 (5! = 120) | 全部排列 + 常见 XOR 密钥 | 无 |
| ZIP 隐写分析 | 注释、额外字段、EOCD 后数据 | 无 |
| Fernet / JWE / OpenSSL 格式 | 常见密钥 | 无 |
| 在线搜索 | Google, CTFtime, CSDN | 未找到 |

### 3.2 理论依据

AES 是经过充分研究的对称加密算法。在唯密文攻击 (ciphertext-only attack) 场景下，没有已知的实际攻击方法能够恢复 AES-ECB 的密钥或明文。

## 四、结论

**本题在当前附件条件下无法唯一求解**。

要使题目可解，至少需要补充以下之一：

1. **提供密钥** — 最直接
2. **提供 ECB 加密 Oracle** — 选手可构造选择明文，进行逐字节 ECB 攻击
3. **提供多份同密钥密文** — 建立分组映射表
4. **提供含有重复分组的密文** — 利用 ECB 模式图样泄露

## 五、如果题目是标准的 Byte-at-a-Time ECB Attack

如果题目实际包含一个加密 Oracle（可能在 CTF 平台服务器上），Exp 脚本如下：

```python
# 标准 ECB Byte-at-a-Time 攻击框架
import requests
from Crypto.Cipher import AES

# 1. 探测 block_size（通常为 16）
# 2. 探测是否使用 ECB 模式（发送重复块，检查密文是否出现重复）
# 3. 逐字节爆破 flag：
#    - 发送 "A" * (block_size - 1) + 猜测字符
#    - 比较密文块
# 4. 重复直到恢复完整 flag
```

但由于缺少 Oracle 地址，此框架无法实际运行。
