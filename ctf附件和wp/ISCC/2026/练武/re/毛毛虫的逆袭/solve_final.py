#!/usr/bin/env python3
"""
ISCC 毛毛虫的逆袭 解题脚本
关键：IDA把shr 24误标为HIBYTE，实际取bits 24-31
"""

def lcg_stream(state, n):
    """生成n个密钥字节"""
    keys = []
    for _ in range(n):
        state = (state * 1103515245 + 12345) & 0xFFFFFFFF
        keys.append(((state >> 24) & 0xFF) % 95)
    return keys

def decrypt(ct, seed):
    """反向LCG：密文→明文"""
    keys = lcg_stream(seed, len(ct))
    plain = bytearray(b - 32 for b in ct)
    plain = bytearray((p - k) % 95 + 32 for p, k in zip(plain, keys))
    return plain.decode()

def encrypt(pt, seed):
    """正向LCG：明文→密文"""
    keys = lcg_stream(seed, len(pt))
    data = bytearray(ord(c) - 32 for c in pt)
    data = bytearray((d + k) % 95 + 32 for d, k in zip(data, keys))
    return bytes(data)

def verify_sha256(content):
    import hashlib
    h1 = hashlib.sha256(content[:10].encode()).hexdigest()
    h2 = hashlib.sha256(content[10:].encode()).hexdigest()
    return (h1 == "7c9a4772c5c1b43f5ccee4e81f46a33aa5a80ffb7d232ae5a118e80a7d558777" and
            h2 == "0fc7f97b5dcd75e6c999ec614bd5522338ecc8fe3a2f7954a3536187d5ccc69d")

def main():
    seed = 36
    target = b"*Y{4ZNrxfAYO,a_za&XG"

    flag_text = decrypt(target, seed)
    full_flag = f"ISCC{{{flag_text}}}"
    print(full_flag)

    # 正向验证
    assert encrypt(flag_text, seed) == target, "LCG mismatch"
    print("[+] LCG check passed")

    # SHA-256验证
    if verify_sha256(flag_text):
        print("[+] SHA-256 check passed")
    else:
        print("[-] SHA-256 mismatch")
        return

    print("[+] All checks OK")

if __name__ == "__main__":
    main()
