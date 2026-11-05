# ISCC "where's bunny" Reverse Writeup

## 题目描述

山顶环绕着十个洞穴，兔子和狐狸分别住在其中。狐狸一直想抓住兔子。有一天，兔子对狐狸说："如果你想抓我，可以按我定的规则在十个洞里找我，次数随你。如果能找到，我就认输。"可是狐狸找了整整一千次都落空，于是它动起了别的念头...

## 静态分析

使用 IDA Pro 打开程序，定位到 `main` 函数 (0x4030B0)。

### 程序流程

1. 读取用户输入 flag
2. 检查是否以 `ISCC{` 开头、以 `}` 结尾
3. 提取花括号内的内容
4. 模拟狐狸找兔子的过程，确定哪些洞穴未被访问
5. 用未访问洞穴对应的数字作为密钥，对 flag 内容进行多层加密
6. 将最终结果转为大写十六进制字符串，与硬编码的 target 比较

### 关键函数识别

| 地址 | 功能 |
|------|------|
| `0x402C00` | 检查 flag 前缀"ISCC{" |
| `0x402D30` | 提取 `{}` 间的内容 |
| `0x401FF0` | **RC4** 加密 |
| `0x402370` | 循环 **XOR** |
| `0x402410` | 循环 **ADD** |
| `0x401AC0` | 整数 → 字符串 → SHA-256 → 前16字节hex输出 |
| `0x401B80` | 自定义 **Feistel** 密码 (8轮，delta=0x61C88647) |
| `0x4024B0` | **SHA-256** 哈希 |
| `0x402FD0` | 二进制 → 大写十六进制字符串 |
| `0x401880` | Feistel 轮函数 |

## 算法详解

### 1. 狐狸找兔子 (Fox Search)

```c
v18 = 0;
for (i = 1; i < 1000; ++i) {
    v20 = v18 % 10;          // 当前检查的洞穴
    v18 = (v18 % 10) + i + 1; // 更新步长
    occupancy[v20] = 0;      // 标记为已访问
}
```

运行后未访问的洞穴索引为 **[1, 3, 6, 8]**（0-indexed）。

### 2. 洞穴编号数组

```c
v77[0] = 5;    v77[1] = 344;   v77[2] = 13;
v77[3] = 21;   v77[4] = 34;    v77[5] = 55;
v77[6] = 89;   v77[7] = 144;   v77[8] = 233;
v77[9] = 377;
```

（除 344 外均为斐波那契数）

未访问洞穴对应的数字：
- 洞穴 1 → 344
- 洞穴 3 → 21
- 洞穴 6 → 89
- 洞穴 8 → 233

### 3. 加密管道

按发现顺序，4个未访问洞穴对应的数字依次作为4个操作步骤的密钥：

| 步骤 | 操作 | 密钥 | 详细 |
|------|------|------|------|
| 1 | **RC4** | "344" | KSA + PRGA 标准RC4 |
| 2 | **循环 XOR** | "21" | data[i] ^= key[i % len(key)] |
| 3 | **循环 ADD** | "89" | data[i] += key[i % len(key)] |
| 4 | **Feistel** | SHA-256("233")[:16] | 自定义Feistel密码，8轮，每轮4对 |

**Feistel 密码细节** (sub_401880)：
- delta = 1640531527 = 0x61C88647
- 8 轮 × 4 对 = 32 对更新
- 每对：`v0 += (sum + v1) ^ (k1 + v1>>5) ^ (k0 + v1<<4)`，然后 `v1 += (sum + v0) ^ (k2 + v0<<4) ^ (k3 + v0>>5)`
- sum 值依次为：-delta, -2×delta, ..., -32×delta

**第4步中密钥派生** (sub_401AC0)：
1. `sprintf("%d", 233)` → "233"
2. SHA-256("233") → 32字节
3. 取前16字节 → 转为32字符hex串 → 再解码回16字节 → 作为4个little-endian dword

### 4. 最终比对

```c
// target 字符串
"D4BB5EF2AF2AE849607A3D0B78CCF17071C5851C10551C52"
```

sub_402FD0 将加密结果转为大写 hex 后与之比较。

## 解密脚本

```python
import hashlib
import struct

TARGET = bytes.fromhex("D4BB5EF2AF2AE849607A3D0B78CCF17071C5851C10551C52")
DELTA = 1640531527
keys = ["344", "21", "89", "233"]

def feistel_decrypt_block(data, key):
    v0, v1 = struct.unpack('<2I', data)
    k0, k1, k2, k3 = struct.unpack('<4I', key)
    sums, vs = [], 0
    for _ in range(8):
        v6 = (vs - DELTA) & 0xFFFFFFFF; sums.append(v6)
        v6 = (v6 - DELTA) & 0xFFFFFFFF; sums.append(v6)
        v6 = (v6 - DELTA) & 0xFFFFFFFF; sums.append(v6)
        vs = (v6 - DELTA) & 0xFFFFFFFF; sums.append(vs)
    for s in reversed(sums):
        v1 = (v1 - ((s + v0) ^ (k2 + ((v0 << 4) & 0xFFFFFFFF)) ^ (k3 + (v0 >> 5)))) & 0xFFFFFFFF
        v0 = (v0 - ((s + v1) ^ (k1 + (v1 >> 5)) ^ (k0 + ((v1 << 4) & 0xFFFFFFFF)))) & 0xFFFFFFFF
    return struct.pack('<2I', v0, v1)

def feistel_decrypt(data, key):
    return b''.join(feistel_decrypt_block(data[i:i+8], key) for i in range(0, len(data), 8))

def rc4(data, key_str):
    key = [ord(c) for c in key_str]
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0
    res = bytearray(len(data))
    for n in range(len(data)):
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        res[n] = data[n] ^ S[(S[i] + S[j]) % 256]
    return bytes(res)

def xor_key(data, ks):
    k = [ord(c) for c in ks]
    return bytes(data[i] ^ k[i % len(k)] for i in range(len(data)))

def sub_key(data, ks):
    k = [ord(c) for c in ks]
    return bytes((data[i] - k[i % len(k)]) & 0xFF for i in range(len(data)))

# 逆向解密管道
d = feistel_decrypt(TARGET, hashlib.sha256(keys[3].encode()).digest()[:16])
d = sub_key(d, keys[2])     # 逆 ADD
d = xor_key(d, keys[1])     # 逆 XOR
d = rc4(d, keys[0])         # RC4 解密（加解密相同）
d = d[:-1]                  # 去除 PKCS#7 填充（1字节）

flag = f"ISCC{{{d.decode()}}}"
print(flag)
```

## Flag

```
ISCC{ilwhutyaIrsdueoleaIoylc}
```
