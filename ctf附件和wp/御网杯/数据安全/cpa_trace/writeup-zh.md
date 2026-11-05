---
title: "cpa_trace"
ctf: "数据安全"
date: 2026-05-31
category: forensics
difficulty: 初级
points: 500
flag_format: "flag{...}"
---

# cpa_trace

## 题目概述

某数据加密设备在处理敏感数据时留下了一批侧信道采集记录，包括加密明文、双通道功耗/电磁迹线，以及一份被加密保存的敏感结果 flag.enc。通过 CPA（相关功耗分析）攻击恢复 AES-128 密钥，并进一步解密 flag.enc。

## 解题步骤

### Step 1: 选择正确的泄漏模型进行 CPA

数据规格：
- `plaintexts.npy`：5000 × 16 uint8，AES 加密明文
- `traces.npy`：5000 × 2 × 1024 float64，双通道功耗/电磁迹线
- `flag.enc`：48 字节，加密后的 flag

迹线在 1024 个时间采样点中呈现 16 个等间距的相关峰（t = 32, 96, 160, ..., 992），间距 64 个采样点，对应 AES 第一轮逐字节 SubBytes 运算。

**标准 HW 模型（S 盒输出的汉明重量）** 相关性仅为 0.12-0.18，部分字节边距极小（如字节 13 仅 0.0001），不够可靠。

**关键发现：正确模型是汉明距离（HD）模型**

```
HD(plaintext, SBOX[plaintext ⊕ key]) = HW(plaintext ⊕ SBOX[plaintext ⊕ key])
```

该模型模拟 CMOS 寄存器从持有明文值跳变到持有 S 盒输出值的功耗。由于寄存器在两个值之间切换，其功耗正比于两者的汉明距离，相关性高达 **0.72-0.78**，边距达 0.57-0.64。

### Step 2: 密钥编排推导轮密钥

CPA 恢复的是 AES-128 主密钥：`422c174a4a89d96af0b7de281dc01324`

但是直接用主密钥解密 flag.enc 得到的是乱码。这是因为 flag.enc 使用了**第 10 轮轮密钥**（最后一轮）进行加密，而非主密钥。

通过 AES-128 密钥编排算法从主密钥导出第 10 轮密钥：
`e53b897e61d2391c2bf0d70727f48509`

### Step 3: 解密 flag

使用 AES-128-ECB 模式和第 10 轮轮密钥解密 flag.enc，去除 PKCS7 填充，得到 flag。

## Flag

```
flag{76ff6af8-f9f8-49ec-ad20-673f2f9c06e7}
```
