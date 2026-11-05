#!/usr/bin/env python3
"""
ISCC Mobile Challenge "按步取匙" — 纯 Python 求解脚本
APK: attachment-25.apk  核心库: libzkpcore.so (ARM64)

从 APK 中提取所有常量，完全在 Python 中计算用户名、密码、三个挑战值及最终 flag。
"""
import hashlib
import hmac
import struct

# ============================================================
# 从 libzkpcore.so 中提取的常量
# ============================================================

# ── 用户名解码 ──
USERNAME_MARKER = b"k3y_j4va_k3y!!!!"          # .rodata 0x13d5
USERNAME_XOR = bytes([                          # .rodata 0x13e5，前 10 字节
    0x11, 0x58, 0x09, 0x00, 0x07, 0x55, 0x05, 0x15, 0x3a, 0x19
])

# ── 登录凭证 ──
PASSWORD = "Zkp_M_ast3er"                      # 由 "Zkp_" + "M_as" + "t3er" 拼接
SALT_STR = "CTF_ZKP_apk-15_SALT_V3"            # 会话密钥派生用盐

# ── CH1: Feistel 网络参数 ──
LFSR_SEED   = 0xEE0F                           # LFSR 初始种子
LFSR_POLY   = 0xB400                           # LFSR 多项式
CH1_CONSTS  = [0x7858F355, 0xE0F4EDEA, 0x189D0D3F, 0x98AC1EBF]  # 4 轮常数
CH1_TARGET  = 0x5B7D9AC4                       # Feistel 加密后的目标值
SBOX        = [0xE, 4, 0xD, 1, 2, 0xF, 0xB, 8, 3, 0xA, 6, 0xC, 5, 9, 0, 7]  # 4-bit S盒

# ── CH2: LCG 参数 ──
# .rodata 0x13ef: 8b 48 21 05（大端初始值）
# .rodata 0x13f3: f9 1b f9 00（32位小端，异或时需字节反转）
CH2_INIT_B0, CH2_INIT_B1, CH2_INIT_B2, CH2_INIT_B3 = 0x8b, 0x48, 0x21, 0x05
CH2_XOR_BYTES = b'\xf9\x1b\xf9\x00'
CH2_LCG_MULT  = 0x2056956f                     # LCG 乘数
CH2_LCG_INC   = 0x8535ef14                     # LCG 增量
CH2_FINAL_XOR = 0x7fa77a3a                     # 最终异或

# ── CH3: XOR 常量 ──
CH3_XOR_CONST = 0x2BE99DCFCF628A90             # 与 token 前 8 字节异或

# ============================================================
# 工具函数
# ============================================================

def lfsr16(x):
    """16 位 LFSR（线性反馈移位寄存器），多项式 0xB400"""
    bit = x & 1
    x >>= 1
    if bit:
        x ^= LFSR_POLY
    return x & 0xFFFF

def hex_encode(data, n):
    """将 data 的前 n 字节编码为小写十六进制字符串"""
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
    """从 .rodata 中 XOR 解码用户名"""
    return bytes(USERNAME_XOR[i] ^ USERNAME_MARKER[i] for i in range(10)).decode()

def compute_session_key():
    """
    会话密钥派生流程（与原生 HMAC 一致）：
    U0 = HMAC-SHA256(key=SHA256(salt), data=SHA256(password))
    U1 = HMAC-SHA256(key=U0, data="AUTH_OK" || \\x01)
    session_key = U1
    """
    pw_hash = hashlib.sha256(PASSWORD.encode()).digest()
    salt_hash = hashlib.sha256(SALT_STR.encode()).digest()
    U0 = hmac.new(salt_hash, pw_hash, 'sha256').digest()
    U1 = hmac.new(U0, b"AUTH_OK\x01", 'sha256').digest()
    return U1

# ============================================================
# 第二步：挑战 1 — Feistel 网络
# ============================================================

def compute_ch1():
    """
    CH1 是一个 4 轮 Feistel 网络。
    用户输入 8 位十六进制字符串 → Feistel 加密 → 与 CH1_TARGET 比较。
    我们通过逆向 Feistel 解密来求出正确输入。
    """
    # 生成 8 个 LFSR 值
    s = LFSR_SEED
    vals = []
    for _ in range(8):
        s = lfsr16(s)
        vals.append(s)

    # 生成轮密钥: keys[i] = (lfsr[2i] << 16 | lfsr[2i+1]) ^ consts[i]
    keys = []
    for i in range(4):
        k = (vals[2*i] << 16) | vals[2*i+1]
        k ^= CH1_CONSTS[i]
        keys.append(k & 0xFFFFFFFF)

    def sub_nibbles(x):
        """4-bit S-Box 替换（32 位值分为 8 个半字节）"""
        out = 0
        for i in range(8):
            nibble = (x >> (i * 4)) & 0xF
            out |= SBOX[nibble] << (i * 4)
        return out & 0xFFFFFFFF

    def round_f(value, key):
        """Feistel 轮函数"""
        dup = ((value << 16) | value) & 0xFFFFFFFF  # 16 位扩展到 32 位
        substituted = sub_nibbles(dup ^ key)
        return (substituted ^ (substituted >> 16)) & 0xFFFF  # 压缩回 16 位

    # Feistel 加密: L' = R, R' = L ^ f(R, K)
    # 最终结果: result = (R4 << 16) | L4 = CH1_TARGET
    # 所以: R4 = CH1_TARGET 高 16 位, L4 = CH1_TARGET 低 16 位
    right = (CH1_TARGET >> 16) & 0xFFFF   # R4
    left  = CH1_TARGET & 0xFFFF            # L4

    # Feistel 解密: 反向使用轮密钥
    for key in reversed(keys):
        left, right = (right ^ round_f(left, key)) & 0xFFFF, left

    # 解密后: left = L0, right = R0, 原始输入 = (L0 << 16) | R0
    result = ((left << 16) | right) & 0xFFFFFFFF
    return f"{result:08X}"  # 大写十六进制

# ============================================================
# 第三步：挑战 2 — LCG + SHA256
# ============================================================

def lcg_step(state):
    """单步 LCG: state = state * mult + inc (mod 2^32)"""
    return (state * CH2_LCG_MULT + CH2_LCG_INC) & 0xFFFFFFFF

def compute_ch2():
    """
    CH2 由 FN_MAKE_CH2 (0x4034) 生成：
    - 初始值 = 4 字节大端整数
    - 异或字节反转后的掩码
    - 7 轮 LCG 迭代
    - 异或最终常数
    - 转为 4 字节大端 → SHA256 → 十六进制编码前 16 字节 → 32 字符小写十六进制
    """
    # 大端初始值
    init_val = (CH2_INIT_B0 << 24) | (CH2_INIT_B1 << 16) | \
               (CH2_INIT_B2 << 8)  | CH2_INIT_B3

    # 掩码: .rodata 中的 32 位小端数值进行字节反转
    xor_le = struct.unpack('<I', CH2_XOR_BYTES)[0]
    xor_rev = ((xor_le & 0xFF) << 24) | ((xor_le & 0xFF00) << 8) | \
              ((xor_le & 0xFF0000) >> 8) | ((xor_le & 0xFF000000) >> 24)

    state = init_val ^ xor_rev

    # 7 轮 LCG
    for _ in range(7):
        state = lcg_step(state)

    # 最终异或
    state ^= CH2_FINAL_XOR

    # 4 字节大端
    buf = bytes([(state >> 24) & 0xFF, (state >> 16) & 0xFF,
                 (state >> 8) & 0xFF, state & 0xFF])

    # SHA256 → 十六进制前 16 字节
    h = hashlib.sha256(buf).digest()
    return hex_encode(h, 16)

def compute_ch2_verify(ch2_val):
    """CH2 验证哈希 = SHA256("t2_dynamic_" || ch2_val)"""
    return hashlib.sha256(b"t2_dynamic_" + ch2_val.encode()).digest()

# ============================================================
# 第四步：中间令牌
# ============================================================

def compute_token(ch2_val):
    """
    中间令牌 = SHA256(ch2_val || "CTF_ZKP_INTERMEDIATE_SEED_V2") 的前 16 字节
    十六进制编码为 32 字符小写字符串
    """
    data = ch2_val.encode() + b"CTF_ZKP_INTERMEDIATE_SEED_V2"
    h = hashlib.sha256(data).digest()
    return hex_encode(h, 16)

# ============================================================
# 第五步：挑战 3 — XOR + SHA256
# ============================================================

def compute_ch3(token):
    """
    CH3 finalKey:
    1. 取 token 前 8 ASCII 字节为 64 位大端整数
    2. 异或 CH3_XOR_CONST
    3. 以 LITTLE-ENDIAN 字节序（匹配 ARM64 str 指令）写入 8 字节
    4. SHA256 → 完整十六进制 → 取前 16 字符 = finalKey
    """
    value = int.from_bytes(token[:8].encode(), 'big')
    value ^= CH3_XOR_CONST
    h = hashlib.sha256(value.to_bytes(8, 'little')).digest()
    return hex_encode(h, 32)[:16]

def compute_ch3_verify(final_key, token):
    """CH3 验证哈希 = SHA256("t3_android_" || finalKey || token)"""
    data = b"t3_android_" + final_key.encode() + token.encode()
    return hashlib.sha256(data).digest()

# ============================================================
# 第六步：Flag 生成
# ============================================================

def compute_flag(session_key, ch1_verify, ch2_verify, ch3_verify):
    """
    Flag 生成流程（匹配 FN_GEN_FLAG 0x2F14）：
    1. 拼接 71 字节数据: "CTF_ZKP_FLAG_V2" + session_key(32) + ch1_v[0:8] + ch2_v[0:8] + ch3_v[0:8]
       （注意 "CTF_ZKP_FLAG_V2" 长度为 15，不包含 null 终止符）
    2. SHA256
    3. 取前 24 字节 → 48 字符小写十六进制
    4. 格式化为 ISCC{...}
    """
    data = b"CTF_ZKP_FLAG_V2"       # 15 字节，无 null（与原生 memcpy size=15 一致）
    data += session_key              # 32 字节
    data += ch1_verify[:8]           # 8 字节
    data += ch2_verify[:8]           # 8 字节
    data += ch3_verify[:8]           # 8 字节
    # 总计 71 字节

    h = hashlib.sha256(data).digest()
    flag_hex = hex_encode(h, 24)     # 前 24 字节 → 48 十六进制字符
    return f"ISCC{{{flag_hex}}}"

# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("  ISCC 按步取匙 — 完整求解")
    print("=" * 60)

    # 用户名和密码
    username = compute_username()
    print(f"\n[1] 用户名: {username}")
    print(f"    密码: {PASSWORD}")

    # 会话密钥
    session_key = compute_session_key()
    print(f"[2] 会话密钥: {session_key.hex()}")

    # CH1
    ch1_val = compute_ch1()
    ch1_verify = hashlib.sha256(b"t1_static_" + ch1_val.encode()).digest()
    print(f"[3] CH1 输入: {ch1_val}")
    print(f"    CH1 验证哈希 (前 8 字节): {ch1_verify[:8].hex()}")

    # CH2
    ch2_val = compute_ch2()
    ch2_verify = compute_ch2_verify(ch2_val)
    print(f"[4] CH2 输入 (32 hex): {ch2_val}")
    print(f"    CH2 验证哈希 (前 8 字节): {ch2_verify[:8].hex()}")

    # 中间令牌
    token = compute_token(ch2_val)
    print(f"[5] 中间令牌 (32 hex): {token}")

    # CH3
    ch3_val = compute_ch3(token)
    ch3_verify = compute_ch3_verify(ch3_val, token)
    print(f"[6] CH3 输入 (finalKey): {ch3_val}")
    print(f"    CH3 验证哈希 (前 8 字节): {ch3_verify[:8].hex()}")

    # Flag
    flag = compute_flag(session_key, ch1_verify, ch2_verify, ch3_verify)
    print(f"\n[7] FLAG: {flag}")

    # 汇总
    print("\n" + "=" * 60)
    print("  求解结果")
    print("=" * 60)
    print(f"  用户名:     {username}")
    print(f"  密码:       {PASSWORD}")
    print(f"  会话密钥:   {session_key.hex()}")
    print(f"  CH1 输入:   {ch1_val}")
    print(f"  CH2 输入:   {ch2_val}")
    print(f"  中间令牌:   {token}")
    print(f"  CH3 输入:   {ch3_val}")
    print(f"  FLAG:       {flag}")

    return flag

if __name__ == "__main__":
    main()
