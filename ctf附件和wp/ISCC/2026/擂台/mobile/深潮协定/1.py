#!/usr/bin/env python3
"""
ISCC 深潮协定 — 解题脚本
用法: python exp.py app-release.apk
"""

import sys, os, base64, zipfile


def extract_telemetry(apk_path):
    with zipfile.ZipFile(apk_path, 'r') as zf:
        with zf.open('assets/telemetry.bin') as f:
            content = f.read().decode('utf-8').strip()
    lines = content.split('\n')
    assert len(lines) == 4
    shifts = bytes.fromhex(lines[0])
    mask = bytes.fromhex(lines[1])
    alphabet = lines[2]
    target = lines[3]
    return shifts, mask, alphabet, target


def custom_b64_decode(s, alphabet):
    std_alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
               + 'abcdefghijklmnopqrstuvwxyz0123456789+/'
    table = str.maketrans(alphabet, std_alpha)
    return base64.b64decode(s.translate(table))


def reverse_lfsr(data):
    state = 0x5D
    out = bytearray(data)
    for i in range(len(out)):
        fb = ((state >> 2) ^ (state >> 3) ^ (state >> 5) ^ state) & 1
        state = ((fb << 7) | (state >> 1)) & 0xFF
        out[i] ^= (i * 7 + state) & 0xFF
    return bytes(out)


def reverse_transform(data, shifts, mask):
    result = bytearray()
    prev = 0
    for i in range(len(data)):
        c_xor_mask = (data[i] - prev - i * 3) & 0xFF
        c_shifted = c_xor_mask ^ mask[i % len(mask)]
        prev = data[i]
        sft = shifts[i % len(shifts)]
        orig = ((c_shifted - 32 - sft) % 95) + 32
        result.append(orig)
    return result.decode('ascii')


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else 'app-release.apk'
    if not os.path.exists(apk):
        print(f"[-] 找不到: {apk}"); return
    print("[*] 提取 telemetry.bin ...")
    shifts, mask, alphabet, target = extract_telemetry(apk)
    print(f"    shifts = {list(shifts)}")
    print(f"    mask   = {list(mask)}")
    print(f"    target = {target}")
    print("[*] 自定义Base64解码 ...")
    decoded = custom_b64_decode(target, alphabet)
    print(f"    解码后 ({len(decoded)}B): {decoded.hex()}")
    print("[*] 逆推LFSR混合 ...")
    after_lfsr = reverse_lfsr(decoded)
    print("[*] 逆推CryptoEngine.transform ...")
    flag_inner = reverse_transform(after_lfsr, shifts, mask)
    flag = f"ISCC{{{flag_inner}}}"
    print(f"\n[+] FLAG: {flag}")
    return flag


if __name__ == '__main__':
    main()

