#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ISCC Mobile 「按步取匙」 — 完整求解脚本
import hashlib
import hmac
import struct

# ============================================================
# 常量（从 libzkpcore.so 提取）
# ============================================================

USERNAME_MARKER = b"k3y_j4va_k3y!!!!"
USERNAME_XOR = bytes([0x11, 0x58, 0x09, 0x00, 0x07,
                      0x55, 0x05, 0x15, 0x3a, 0x19])
PASSWORD = "Zkp_M_ast3er"
SALT_STR = "CTF_ZKP_apk-15_SALT_V3"

# CH1 - Feistel
LFSR_SEED   = 0xEE0F
CH1_CONSTS  = [0x7858F355, 0xE0F4EDEA, 0x189D0D3F, 0x98AC1EBF]
CH1_TARGET  = 0x5B7D9AC4
SBOX        = [0xE, 4, 0xD, 1, 2, 0xF, 0xB, 8,
               3, 0xA, 6, 0xC, 5, 9, 0, 7]

# CH2 - LCG
CH2_LCG_MULT  = 0x2056956f
CH2_LCG_INC   = 0x8535ef14
CH2_FINAL_XOR = 0x7fa77a3a

# CH3 - XOR
CH3_XOR_CONST = 0x2BE99DCFCF628A90


def lfsr16(x):
    bit = x & 1
    x >>= 1
    if bit:
        x ^= 0xB400
    return x & 0xFFFF


def hex_encode(data, n):
    table = "0123456789abcdef"
    out = ""
    for i in range(n):
        b = data[i]
        out += table[b >> 4]
        out += table[b & 0xF]
    return out


# 第一步：登录凭证
def compute_username():
    return bytes(USERNAME_XOR[i] ^ USERNAME_MARKER[i]
                 for i in range(10)).decode()


def compute_session_key():
    pw_hash = hashlib.sha256(PASSWORD.encode()).digest()
    salt_hash = hashlib.sha256(SALT_STR.encode()).digest()
    U0 = hmac.new(salt_hash, pw_hash, 'sha256').digest()
    return hmac.new(U0, b"AUTH_OK\x01", 'sha256').digest()


# 第二步：挑战1 — Feistel 解密
def compute_ch1():
    s = LFSR_SEED
    vals = []
    for _ in range(8):
        s = lfsr16(s)
        vals.append(s)
    keys = [((vals[2*i] << 16) | vals[2*i+1]) ^ CH1_CONSTS[i]
            for i in range(4)]

    def sub_nibbles(x):
        o = 0
        for i in range(8):
            o |= SBOX[(x >> (i*4)) & 0xF] << (i*4)
        return o & 0xFFFFFFFF

    def round_f(v, k):
        x = sub_nibbles(((v << 16) | v) ^ k)
        return (x ^ (x >> 16)) & 0xFFFF

    right = (CH1_TARGET >> 16) & 0xFFFF
    left = CH1_TARGET & 0xFFFF
    for k in reversed(keys):
        left, right = (right ^ round_f(left, k)) & 0xFFFF, left
    return f"{((left << 16) | right) & 0xFFFFFFFF:08X}"


# 第三步：挑战2 — LCG
def compute_ch2():
    init_val = (0x8b << 24) | (0x48 << 16) | (0x21 << 8) | 0x05
    xor_le = struct.unpack('<I', b'\xf9\x1b\xf9\x00')[0]
    xor_rev = (((xor_le & 0xFF) << 24) | ((xor_le & 0xFF00) << 8) |
               ((xor_le & 0xFF0000) >> 8) | ((xor_le & 0xFF000000) >> 24))
    state = init_val ^ xor_rev
    for _ in range(7):
        state = (state * CH2_LCG_MULT + CH2_LCG_INC) & 0xFFFFFFFF
    state ^= CH2_FINAL_XOR
    buf = struct.pack('>I', state)
    return hex_encode(hashlib.sha256(buf).digest(), 16)


# 第四步：中间令牌
def compute_token(ch2_val):
    data = ch2_val.encode() + b"CTF_ZKP_INTERMEDIATE_SEED_V2"
    return hex_encode(hashlib.sha256(data).digest(), 16)


# 第五步：挑战3 — XOR（注意小端！）
def compute_ch3(token):
    value = int.from_bytes(token[:8].encode(), 'big')
    value ^= CH3_XOR_CONST
    h = hashlib.sha256(value.to_bytes(8, 'little')).digest()
    return hex_encode(h, 32)[:16]


# 第六步：Flag 生成
def compute_flag(sk, c1v, c2v, c3v):
    data = b"CTF_ZKP_FLAG_V2"  # 15字节，无null
    data += sk
    data += c1v[:8]
    data += c2v[:8]
    data += c3v[:8]
    h = hashlib.sha256(data).digest()
    return f"ISCC{{{hex_encode(h, 24)}}}"


def main():
    username = compute_username()
    print(f"[*] 用户名: {username}")
    print(f"[*] 密码: {PASSWORD}")

    session_key = compute_session_key()
    print(f"[*] 会话密钥: {session_key.hex()}")

    ch1_val = compute_ch1()
    ch1_v = hashlib.sha256(b"t1_static_" + ch1_val.encode()).digest()
    print(f"[*] CH1: {ch1_val}")

    ch2_val = compute_ch2()
    ch2_v = hashlib.sha256(b"t2_dynamic_" + ch2_val.encode()).digest()
    print(f"[*] CH2: {ch2_val}")

    token = compute_token(ch2_val)
    print(f"[*] Token: {token}")

    ch3_val = compute_ch3(token)
    ch3_v = hashlib.sha256(
        b"t3_android_" + ch3_val.encode() + token.encode()
    ).digest()
    print(f"[*] CH3: {ch3_val}")

    flag = compute_flag(session_key, ch1_v, ch2_v, ch3_v)
    print(f"[+] FLAG: {flag}")


if __name__ == "__main__":
    main()

