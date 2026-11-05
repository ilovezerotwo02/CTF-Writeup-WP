#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 先声夺人 solver — 全自动解题脚本
# Usage: python3 exp.py

import hashlib, json, zlib, sys
from pathlib import Path

try:
    from Crypto.Cipher import AES as _AES
    from Crypto.Hash import SHA256 as _SHA256
    from Crypto.Protocol.KDF import PBKDF2 as _PBKDF2
    from Crypto.Util.Padding import unpad as _unpad
except ImportError:
    print("[!] 缺少 pycryptodome，请执行: pip install pycryptodome")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 编码表
# ---------------------------------------------------------------------------
CODEBOOK = {
    "\u200b": "0",
    "\u200c": "1",
    "\u200d": "2",
    "\ufeff": "3",
}

# ---------------------------------------------------------------------------
# 阶段 A: 剥离干扰文本，还原载荷
# ---------------------------------------------------------------------------
def phase_a_extract(fp="challenge.txt"):
    """Step A: 从多语言文本中筛选零宽字符→四进制→zlib→JSON"""
    raw = Path(fp).read_text("utf-8")
    seq = "".join(CODEBOOK[ch] for ch in raw if ch in CODEBOOK)
    blob = bytes(int(seq[k:k+4], 4) for k in range(0, len(seq), 4))
    return json.loads(zlib.decompress(blob[4:]))   # 跳过 4 字节偏移

# ---------------------------------------------------------------------------
# 阶段 B: 工作量证明
# ---------------------------------------------------------------------------
class PoWSolver:
    """暴力搜索满足前 N 比特为零的 SHA256 原像"""

    def __init__(self, nonce_str, diff_bits):
        self.prefix = nonce_str.encode()
        self.diff = diff_bits

    @staticmethod
    def _check(digest, bits):
        n = bits // 8
        if digest[:n] != bytes(n):
            return False
        rem = bits % 8
        return True if rem == 0 else (digest[n] >> (8 - rem)) == 0

    def search(self):
        x = 0
        while True:
            h = hashlib.sha256(self.prefix + str(x).encode()).digest()
            if self._check(h, self.diff):
                return x, h.hex()
            x += 1

# ---------------------------------------------------------------------------
# 阶段 C: 密钥派生 + 解密
# ---------------------------------------------------------------------------
def phase_c_decrypt(conf, s_val):
    """用 PBKDF2 推导演出 AES-256 密钥，再 CBC 解密"""
    k = _PBKDF2(
        str(s_val).encode(),
        conf["nonce"].encode(),
        dkLen=conf["key_derivation"]["dklen"],
        count=conf["key_derivation"]["iterations"],
        hmac_hash_module=_SHA256,
    )
    iv = bytes.fromhex(conf["encrypted_flag"]["iv"])
    ct = bytes.fromhex(conf["encrypted_flag"]["ciphertext"])
    return _unpad(_AES.new(k, _AES.MODE_CBC, iv).decrypt(ct), 16).decode()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 阶段 A: 提取
    cfg = phase_a_extract()
    print("[A] 零宽字符已提取，JSON 配置加载完毕")
    print(f"    nonce = {cfg['nonce']}")
    print(f"    diff  = {cfg['difficulty_bits']} bits")

    # 阶段 B: PoW
    solver = PoWSolver(cfg["nonce"], cfg["difficulty_bits"])
    s, hsh = solver.search()
    print(f"[B] PoW 爆破完成")
    print(f"    s    = {s}")
    print(f"    hash = {hsh}")

    # 阶段 C: 解密
    flag = phase_c_decrypt(cfg, s)
    print(f"[C] FLAG = {flag}")
