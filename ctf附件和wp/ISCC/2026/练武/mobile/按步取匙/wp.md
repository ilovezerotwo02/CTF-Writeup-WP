# ISCC Mobile Challenge "按步取匙" — Writeup

## 题目概述

**题目名称**: 按步取匙（Step by Step Key）  
**分类**: Mobile  
**核心文件**: `attachment-25.apk` → `lib/arm64-v8a/libzkpcore.so`（ARM64 原生库）  

该 APK 是一个 Android 应用，通过 JNI 调用 ARM64 原生库 `libzkpcore.so` 实现登录验证、三重挑战认证和最终的 flag 生成。用户需要依次通过三道挑战，才能触发 flag 的生成。

---

## 第一步：APK 分析

解压 APK，提取关键文件：

```
attachment-25.apk
├── lib/arm64-v8a/libzkpcore.so    # ARM64 原生库（核心逻辑）
├── classes.dex                      # Java 层
└── res/                             # 资源文件
```

通过 `jadx` 反编译 Java 层 `MainActivity.java`，可以窥见整体流程：

```java
// JNI 方法声明
private native int nativeLogin(String username, String password);
private native int nativeVerifyChallenge1(String value);
private native int nativeVerifyChallenge2(String value);
private native int nativeVerifyChallenge3WithToken(String finalKey, String token);
private native String nativeGetIntermediateToken();
private native String nativeGenerateFlag();
```

**认证流程**：
1. `nativeLogin` → 用户名密码验证 → 成功进入挑战界面
2. `nativeVerifyChallenge1` → 第一重验证（Feistel 网络）
3. `nativeVerifyChallenge2` → 第二重验证（LCG + SHA256）
4. `nativeGetIntermediateToken` → 生成中间令牌（存到 SharedPreferences）
5. `nativeVerifyChallenge3WithToken` → 第三重验证（XOR + SHA256）
6. `nativeGenerateFlag` → 所有挑战通过后生成 flag

---

## 第二步：核心库逆向

使用 `readelf` 和反汇编工具分析 `libzkpcore.so`：

```
架构: ARM64 (AArch64)
关键段: 
  .text  0x1d84 — 原生函数代码
  .rodata 0xf30 — 只读数据（字符串、常量）
  .bss   0x8018 — 未初始化数据（中间令牌存储）
```

将 `.text` 段反汇编后，逐个分析关键函数：

| 函数地址 | 名称 | 功能 |
|---------|------|------|
| 0x297C | FN_ALLOC_AUTH | 分配认证上下文（含会话密钥存储） |
| 0x2E84 | FN_ALLOC_STATE | 分配挑战状态结构体 |
| 0x2A0C | FN_LOGIN_CORE | 执行登录验证 |
| 0x336C | FN_CHECK_CH1 | 第一重验证（Feistel） |
| 0x4034 | FN_MAKE_CH2 | 生成第二重验证值 |
| 0x3C4C | FN_CHECK_CH2 | 验证第二重 |
| 0x43D0 | FN_CHECK_CH3 | 第三重验证 |
| 0x2F14 | FN_GEN_FLAG | 生成最终 flag |

---

## 第三步：用户名与密码

在 `.rodata` 中找到用户名加密标记：

```
偏移 0x13d5: "k3y_j4va_k3y!!!!" （16 字节标记）
偏移 0x13e5: 后 10 字节为 XOR 掩码 → [0x11, 0x58, 0x09, 0x00, 0x07, 0x55, 0x05, 0x15, 0x3a, 0x19]
```

解码：`marker[i] ^ mask[i]` → `"zkp_master"`

密码则在 `FN_LOGIN_CORE` 中构造，由三个子串拼接：

```
"Zkp_" + "M_as" + "t3er" = "Zkp_M_ast3er"
```

```python
def compute_username():
    marker = b"k3y_j4va_k3y!!!!"
    mask = bytes([0x11, 0x58, 0x09, 0x00, 0x07, 0x55, 0x05, 0x15, 0x3a, 0x19])
    return bytes(marker[i] ^ mask[i] for i in range(10)).decode()
```

---

## 第四步：会话密钥派生

`FN_LOGIN_CORE` 中实现了 HMAC-SHA256 双重派生：

```
盐: "CTF_ZKP_apk-15_SALT_V3"
密码: "Zkp_M_ast3er"

pw_hash   = SHA256(password)
salt_hash = SHA256(salt)
U0 = HMAC-SHA256(key=salt_hash, data=pw_hash)
U1 = HMAC-SHA256(key=U0, data="AUTH_OK" || \x01)
session_key = U1  # 32 字节
```

```python
def compute_session_key():
    pw_hash = hashlib.sha256(PASSWORD.encode()).digest()
    salt_hash = hashlib.sha256(SALT_STR.encode()).digest()
    U0 = hmac.new(salt_hash, pw_hash, 'sha256').digest()
    U1 = hmac.new(U0, b"AUTH_OK\x01", 'sha256').digest()
    return U1
```

会话密钥将被用于最终的 flag 生成。

---

## 第五步：第一重挑战 — Feistel 网络

`FN_CHECK_CH1` 实现了一个 4 轮 Feistel 网络加密。用户输入 8 位十六进制字符串，经过 Feistel 加密后与目标值 `0x5B7D9AC4` 比较。

### 参数提取

从反汇编中提取所有常量：

| 参数 | 值 | 来源 |
|------|-----|------|
| LFSR 种子 | `0xEE0F` | 指令 `mov w8, #0xee0f` |
| LFSR 多项式 | `0xB400` | 常量 |
| 轮常数 K0 | `0x7858F355` | `movk w9, #0x7858, lsl #16` |
| 轮常数 K1 | `0xE0F4EDEA` | |
| 轮常数 K2 | `0x189D0D3F` | |
| 轮常数 K3 | `0x98AC1EBF` | |
| 目标值 | `0x5B7D9AC4` | `movk w9, #0x5b7d, lsl #16` |
| S-Box | `[0xE, 4, 0xD, 1, 2, 0xF, 0xB, 8, 3, 0xA, 6, 0xC, 5, 9, 0, 7]` | 4-bit S 盒 |

### 算法流程

```
1. LFSR 迭代 8 次，生成 8 个 16 位随机数 r0..r7
2. 轮密钥: keys[i] = (r[2i] << 16 | r[2i+1]) ^ CONSTS[i]
3. Feistel 加密:

   左半 L, 右半 R（各 16 位）
   对每轮 i = 0..3:
        newL = R
        newR = L ^ f(R, keys[i])
   其中 f(v, k) = SBoxExpand(v << 16 | v) ^ k → 压缩回 16 位

4. 结果: result = (R4 << 16) | L4
5. 比较 result == 0x5B7D9AC4
```

### 逆向求解

由于知道目标值，我们可以逆向 Feistel 解密：

```python
# Feistel 解密: 反向使用轮密钥
right = (CH1_TARGET >> 16) & 0xFFFF   # R4
left  = CH1_TARGET & 0xFFFF            # L4

for key in reversed(keys):
    left, right = (right ^ round_f(left, key)) & 0xFFFF, left

# 原始输入 = (L0 << 16) | R0
result = ((left << 16) | right) & 0xFFFFFFFF
```

得到 CH1 输入: `63AB20B7`

---

## 第六步：第二重挑战 — LCG + SHA256

`FN_MAKE_CH2`（地址 0x4034）使用线性同余生成器（LCG）生成 CH2 的值。

### 参数提取

| 参数 | 值 | 说明 |
|------|-----|------|
| 初始值 | `0x8B482105` | `.rodata` 0x13ef 处 4 字节大端 |
| XOR 掩码 | `0x00F91BF9` | `.rodata` 0x13f3 处 4 字节小端（需字节反转） |
| LCG 乘数 | `0x2056956F` | |
| LCG 增量 | `0x8535EF14` | |
| 最终 XOR | `0x7FA77A3A` | |
| 迭代次数 | 7 | |

### 算法流程

```
1. init_val = 0x8B482105
2. xor_mask = byteswap(0x00F91BF9) = 0xF91BF900
3. state = init_val ^ xor_mask
4. 7 轮: state = state * 0x2056956F + 0x8535EF14 (mod 2^32)
5. state ^= 0x7FA77A3A
6. buf = state 转 4 字节大端
7. hash = SHA256(buf)
8. 输出 = hex_encode(hash, 16)  → 32 字符小写十六进制
```

```python
def compute_ch2():
    init_val = (0x8b << 24) | (0x48 << 16) | (0x21 << 8) | 0x05
    xor_le = struct.unpack('<I', b'\xf9\x1b\xf9\x00')[0]
    xor_rev = ((xor_le & 0xFF) << 24) | ((xor_le & 0xFF00) << 8) | \
              ((xor_le & 0xFF0000) >> 8) | ((xor_le & 0xFF000000) >> 24)
    state = init_val ^ xor_rev
    for _ in range(7):
        state = (state * 0x2056956f + 0x8535ef14) & 0xFFFFFFFF
    state ^= 0x7fa77a3a
    buf = struct.pack('>I', state)
    return hex_encode(hashlib.sha256(buf).digest(), 16)
```

得到 CH2 值: `516bf2d94695b0903e8af0b58a354c01`

---

## 第七步：中间令牌

`FN_MAKE_CH2` 执行完毕后，紧接着计算中间令牌并存储到 `.bss`（地址 0x803D）：

```
token = SHA256(ch2_value || "CTF_ZKP_INTERMEDIATE_SEED_V2") 的前 16 字节
      → 十六进制编码为 32 字符字符串
```

```python
def compute_token(ch2_val):
    data = ch2_val.encode() + b"CTF_ZKP_INTERMEDIATE_SEED_V2"
    h = hashlib.sha256(data).digest()
    return hex_encode(h, 16)
```

得到 token: `be459f50a77514e2cac0ef685a912072`

这个 token 将被 CH3 使用，也被 Java 层保存到 SharedPreferences。

---

## 第八步：第三重挑战 — XOR + SHA256

`FN_CHECK_CH3` 使用中间令牌计算 finalKey。

### 关键发现：大小端问题

这是求解过程中最容易出错的地方。ARM64 的 `str` 指令以小端字节序存储 64 位值到内存。因此，虽然 token 的前 8 个 ASCII 字节以大端方式解析为 64 位整数，但 XOR 后的 8 字节值必须以**小端字节序**输入 SHA256：

```
1. 取 token 前 8 ASCII 字节 → 64 位大端整数
2. XOR 0x2BE99DCFCF628A90
3. 以 LITTLE-ENDIAN 写入 8 字节
4. SHA256 → 完整 hex → 取前 16 字符 = finalKey
```

```python
def compute_ch3(token):
    value = int.from_bytes(token[:8].encode(), 'big')
    value ^= CH3_XOR_CONST
    h = hashlib.sha256(value.to_bytes(8, 'little')).digest()
    return hex_encode(h, 32)[:16]
```

> ⚠️ 如果使用 `value.to_bytes(8, 'big')`（大端），会得到不同的 SHA256 结果，导致 CH3 验证失败。而别人提供的其他 APK 版本使用大端还是小端需要根据实际反汇编来判断。本题必须使用小端。

得到 finalKey: `a1bcc496ba8d8bef`

---

## 第九步：Flag 生成

`FN_GEN_FLAG`（地址 0x2F14）是所有挑战通过后的最终步骤。它的逻辑：

```
1. 构造 71 字节数据:
   [0-14]:   "CTF_ZKP_FLAG_V2"        (15 字节，注意没有 null 终止符！)
   [15-46]:  session_key               (32 字节)
   [47-54]:  CH1 verify[0:8]           (8 字节)
   [55-62]:  CH2 verify[0:8]           (8 字节)
   [63-70]:  CH3 verify[0:8]           (8 字节)

2. SHA256(71 字节数据)
3. 取前 24 字节 → 48 字符小写十六进制
4. 格式化为 "ISCC{...}"
```

其中验证哈希分别对应：
- CH1 verify = SHA256("t1_static_" || CH1输入)
- CH2 verify = SHA256("t2_dynamic_" || CH2输入)
- CH3 verify = SHA256("t3_android_" || finalKey || token)

### 又一个关键坑点

`"CTF_ZKP_FLAG_V2"` 的长度为 **15 字节**，原生的 `memcpy` 指令 `mov w8, #0xf` 明确指定复制 15 字节，因此 **不包含 null 终止符**。

如果拼接时误写为 `b"CTF_ZKP_FLAG_V2\x00"`（16 字节），SHA256 的输入将变为 72 字节，与原生不一致，产生完全不同的 flag！

```python
def compute_flag(session_key, ch1_verify, ch2_verify, ch3_verify):
    data = b"CTF_ZKP_FLAG_V2"       # 15 字节，无 null！
    data += session_key              # 32 字节
    data += ch1_verify[:8]
    data += ch2_verify[:8]
    data += ch3_verify[:8]
    h = hashlib.sha256(data).digest()
    flag_hex = hex_encode(h, 24)
    return f"ISCC{{{flag_hex}}}"
```

---

## 最终结果

```
FLAG: ISCC{00ab85cba2ce04a9148d7c79dc4f27556b03997a2bf300c5}
```

---

## 完整求解脚本

以下为完整的纯 Python 求解脚本（无需 Unicorn 模拟器，直接计算所有值）：

```python
#!/usr/bin/env python3
"""
ISCC Mobile Challenge "按步取匙" — 纯 Python 求解脚本
"""
import hashlib
import hmac
import struct

# ============================================================
# 从 libzkpcore.so 中提取的常量
# ============================================================

USERNAME_MARKER = b"k3y_j4va_k3y!!!!"
USERNAME_XOR = bytes([0x11, 0x58, 0x09, 0x00, 0x07, 0x55, 0x05, 0x15, 0x3a, 0x19])

PASSWORD = "Zkp_M_ast3er"
SALT_STR = "CTF_ZKP_apk-15_SALT_V3"

LFSR_SEED   = 0xEE0F
LFSR_POLY   = 0xB400
CH1_CONSTS  = [0x7858F355, 0xE0F4EDEA, 0x189D0D3F, 0x98AC1EBF]
CH1_TARGET  = 0x5B7D9AC4
SBOX        = [0xE, 4, 0xD, 1, 2, 0xF, 0xB, 8, 3, 0xA, 6, 0xC, 5, 9, 0, 7]

CH2_INIT = (0x8b, 0x48, 0x21, 0x05)
CH2_XOR_BYTES = b'\xf9\x1b\xf9\x00'
CH2_LCG_MULT  = 0x2056956f
CH2_LCG_INC   = 0x8535ef14
CH2_FINAL_XOR = 0x7fa77a3a

CH3_XOR_CONST = 0x2BE99DCFCF628A90

# ============================================================
# 工具函数
# ============================================================

def lfsr16(x):
    bit = x & 1
    x >>= 1
    if bit:
        x ^= LFSR_POLY
    return x & 0xFFFF

def hex_encode(data, n):
    table = "0123456789abcdef"
    out = ""
    for i in range(n):
        b = data[i]
        out += table[b >> 4]
        out += table[b & 0xF]
    return out

# ============================================================
# 第一步：登录凭证
# ============================================================

def compute_username():
    return bytes(USERNAME_XOR[i] ^ USERNAME_MARKER[i] for i in range(10)).decode()

def compute_session_key():
    pw_hash = hashlib.sha256(PASSWORD.encode()).digest()
    salt_hash = hashlib.sha256(SALT_STR.encode()).digest()
    U0 = hmac.new(salt_hash, pw_hash, 'sha256').digest()
    return hmac.new(U0, b"AUTH_OK\x01", 'sha256').digest()

# ============================================================
# 第二步：挑战 1 — Feistel 网络
# ============================================================

def compute_ch1():
    # LFSR 生成 8 个值
    s = LFSR_SEED
    vals = []
    for _ in range(8):
        s = lfsr16(s)
        vals.append(s)
    
    # 轮密钥
    keys = [((vals[2*i] << 16) | vals[2*i+1]) ^ CH1_CONSTS[i] for i in range(4)]

    def sub_nibbles(x):
        out = 0
        for i in range(8):
            out |= SBOX[(x >> (i * 4)) & 0xF] << (i * 4)
        return out & 0xFFFFFFFF

    def round_f(value, key):
        dup = ((value << 16) | value) & 0xFFFFFFFF
        substituted = sub_nibbles(dup ^ key)
        return (substituted ^ (substituted >> 16)) & 0xFFFF

    # Feistel 解密
    right = (CH1_TARGET >> 16) & 0xFFFF
    left  = CH1_TARGET & 0xFFFF

    for key in reversed(keys):
        left, right = (right ^ round_f(left, key)) & 0xFFFF, left

    result = ((left << 16) | right) & 0xFFFFFFFF
    return f"{result:08X}"

# ============================================================
# 第三步：挑战 2 — LCG + SHA256
# ============================================================

def compute_ch2():
    init_val = (CH2_INIT[0] << 24) | (CH2_INIT[1] << 16) | (CH2_INIT[2] << 8) | CH2_INIT[3]
    xor_le = struct.unpack('<I', CH2_XOR_BYTES)[0]
    xor_rev = ((xor_le & 0xFF) << 24) | ((xor_le & 0xFF00) << 8) | \
              ((xor_le & 0xFF0000) >> 8) | ((xor_le & 0xFF000000) >> 24)
    state = init_val ^ xor_rev
    for _ in range(7):
        state = (state * CH2_LCG_MULT + CH2_LCG_INC) & 0xFFFFFFFF
    state ^= CH2_FINAL_XOR
    buf = struct.pack('>I', state)
    return hex_encode(hashlib.sha256(buf).digest(), 16)

# ============================================================
# 第四步：中间令牌
# ============================================================

def compute_token(ch2_val):
    data = ch2_val.encode() + b"CTF_ZKP_INTERMEDIATE_SEED_V2"
    return hex_encode(hashlib.sha256(data).digest(), 16)

# ============================================================
# 第五步：挑战 3 — XOR + SHA256（小端！）
# ============================================================

def compute_ch3(token):
    value = int.from_bytes(token[:8].encode(), 'big')
    value ^= CH3_XOR_CONST
    h = hashlib.sha256(value.to_bytes(8, 'little')).digest()  # 关键：小端
    return hex_encode(h, 32)[:16]

# ============================================================
# 第六步：Flag 生成
# ============================================================

def compute_flag(session_key, ch1_verify, ch2_verify, ch3_verify):
    # "CTF_ZKP_FLAG_V2" 长度 15，无 null 终止符（严格匹配原生 memcpy size=15）
    data = b"CTF_ZKP_FLAG_V2"
    data += session_key
    data += ch1_verify[:8]
    data += ch2_verify[:8]
    data += ch3_verify[:8]
    h = hashlib.sha256(data).digest()
    return f"ISCC{{{hex_encode(h, 24)}}}"

# ============================================================
# 主流程
# ============================================================

def main():
    username = compute_username()
    session_key = compute_session_key()

    ch1_val = compute_ch1()
    ch1_verify = hashlib.sha256(b"t1_static_" + ch1_val.encode()).digest()

    ch2_val = compute_ch2()
    ch2_verify = hashlib.sha256(b"t2_dynamic_" + ch2_val.encode()).digest()

    token = compute_token(ch2_val)

    ch3_val = compute_ch3(token)
    ch3_verify = hashlib.sha256(b"t3_android_" + ch3_val.encode() + token.encode()).digest()

    flag = compute_flag(session_key, ch1_verify, ch2_verify, ch3_verify)

    print(f"用户名:     {username}")
    print(f"密码:       {PASSWORD}")
    print(f"会话密钥:   {session_key.hex()}")
    print(f"CH1 输入:   {ch1_val}")
    print(f"CH2 输入:   {ch2_val}")
    print(f"中间令牌:   {token}")
    print(f"CH3 输入:   {ch3_val}")
    print(f"FLAG:       {flag}")

if __name__ == "__main__":
    main()
```

---

## 总结

本题 "按步取匙" 通过多层挑战机制充分展示了 Android 原生逆向的常见技术点：

1. **静态分析**：从 APK 中提取原生库，使用反汇编工具定位关键函数
2. **Feistel 网络**：经典的对称加密结构，4 轮 + 4-bit S-Box + LFSR
3. **LCG + SHA256**：伪随机数生成器与哈希函数的结合
4. **字节序陷阱**：ARM64 小端架构下 `str` 指令的存储方式，与 Java/PC 端默认大端的差异
5. **精确的二进制布局**：`memcpy` 大小决定数据边界，多一个 null 字节就导致 flag 完全不同

解题过程中最容易踩的坑：
- **CH3 的大小端**（`to_bytes(8, 'little')` vs `'big'`）
- **flag 字符串的 null 终止符**（"CTF_ZKP_FLAG_V2" 为 15 字节，不包含 null）
- **状态结构体**：如果使用 Unicorn 模拟，需要手动设置状态完成标志位
