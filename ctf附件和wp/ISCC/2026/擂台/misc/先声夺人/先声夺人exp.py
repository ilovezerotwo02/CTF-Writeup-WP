"""
ISCC 先声夺人 - Exploit Script

Misc 150: 零宽字符隐写 + PoW + PBKDF2 + AES-256-CBC
"""

import hashlib
import json
import struct
import time
import zlib
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import unpad

# ---------------------------------------------------------------------------
# Step 1: 从 challenge.txt 中提取零宽字符
# ---------------------------------------------------------------------------

ZERO_WIDTH_MAP = {
    "​": "0",  # Zero Width Space
    "‌": "1",  # Zero Width Non-Joiner
    "‍": "2",  # Zero Width Joiner
    "﻿": "3",  # Zero Width No-Break Space (BOM)
}


def extract_payload(path: str = "challenge.txt") -> dict:
    """从零宽字符中提取、解码、解压得到配置 JSON。"""
    text = Path(path).read_text("utf-8")

    # 1) 挑出所有零宽字符
    hidden_chars = [ch for ch in text if ch in ZERO_WIDTH_MAP]

    # 2) 映射为四进制数字串
    digits = "".join(ZERO_WIDTH_MAP[ch] for ch in hidden_chars)

    # 3) 每 4 位四进制 → 1 字节
    data = bytes(int(digits[i: i + 4], 4) for i in range(0, len(digits), 4))

    # 4) 前 4 字节是偏移量，跳过之后 zlib 解压
    return json.loads(zlib.decompress(data[4:]))


# ---------------------------------------------------------------------------
# Step 2: Proof of Work — 找到 s 使 SHA256 的前 difficulty_bits 位为0
# ---------------------------------------------------------------------------


def has_leading_zero_bits(digest: bytes, bits: int) -> bool:
    """检查 digest 的前 bits 个比特是否全为 0 (MSB first)。"""
    zero_bytes = bits // 8
    remain_bits = bits % 8
    if digest[:zero_bytes] != b"\x00" * zero_bytes:
        return False
    if remain_bits == 0:
        return True
    mask = (0xFF << (8 - remain_bits)) & 0xFF
    return (digest[zero_bytes] & mask) == 0


def solve_pow(nonce: str, difficulty: int) -> tuple[int, str]:
    """暴力搜索最小 s，返回 (s, hash_hex)。"""
    prefix = nonce.encode()
    s = 0
    while True:
        h = hashlib.sha256(prefix + str(s).encode()).digest()
        if has_leading_zero_bits(h, difficulty):
            return s, h.hex()
        s += 1


# ---------------------------------------------------------------------------
# Step 3: PBKDF2 派生密钥 + AES-256-CBC 解密
# ---------------------------------------------------------------------------


def decrypt_flag(cfg: dict, s: int) -> str:
    nonce = cfg["nonce"].encode()
    key = PBKDF2(
        str(s).encode(),
        nonce,
        dkLen=cfg["key_derivation"]["dklen"],
        count=cfg["key_derivation"]["iterations"],
        hmac_hash_module=SHA256,
    )
    iv = bytes.fromhex(cfg["encrypted_flag"]["iv"])
    ct = bytes.fromhex(cfg["encrypted_flag"]["ciphertext"])
    return unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16).decode()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("[*] 提取零宽字符载荷...")
    cfg = extract_payload()
    nonce = cfg["nonce"]
    diff = cfg["difficulty_bits"]
    print(f"    nonce = {nonce}")
    print(f"    difficulty = {diff} bits")

    print(f"[*] PoW 爆破中 (difficulty={diff})...")
    t0 = time.time()
    s, h = solve_pow(nonce, diff)
    t = time.time() - t0
    print(f"    s = {s}")
    print(f"    hash = {h}")
    print(f"    耗时: {t:.2f}s")

    print("[*] 派生 AES 密钥并解密...")
    flag = decrypt_flag(cfg, s)
    print(f"[+] FLAG: {flag}")


if __name__ == "__main__":
    main()
