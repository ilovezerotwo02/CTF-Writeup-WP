#!/usr/bin/env python3
# ISCC 逆向题「消失的喵星密使 / MeowLocker」
# 用法：python3 solve_meowlocker.py [app-release.apk]
import sys, io, zipfile, base64, hashlib
from PIL import Image

# ============ 从原生库逆向得到的正确参数 ============
M_TBL = b"kwpu3e91rg8vo2nzyfqi456ahc7sm0ljxbdt"  # 来自 libmobile03.so .rodata
IDX = {ord('A'): 0, ord('D'): 1, ord('F'): 2, ord('G'): 3, ord('V'): 4, ord('X'): 5}
SEQ = "FFVAXDAVGDDF"           # 路径：🐾→🦋→🌿→☀️→😿→🐈‍⬛
CHECK_MD5 = "8026fc502d36d57c03c31b9866f1d699"
B64 = "LUwkCaSlpOfG5+UcHf0mu7lHVnjnJqsQKtuhpBSzAkY="  # 来自 _c_str
RCON = [1, 2, 4, 8, 16, 32, 64, 128, 0x1b, 0x36]

def extract_sbox(png_bytes):
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    pixels = list(im.getdata())
    need_bits = (4 + 256) * 8
    bits = [(pixels[i][2] & 1) for i in range(need_bits)]
    data = bytearray()
    for i in range(0, need_bits, 8):
        b = 0
        for bit in bits[i:i + 8]:
            b = (b << 1) | bit
        data.append(b)
    assert data[:4] == b"MEOW", f"隐写头错误: {data[:4]!r}"
    sbox = list(data[4:4 + 256])
    assert len(set(sbox)) == 256
    return sbox

def permute(seq):
    b = seq.encode()
    return bytes([*b[1::4], *b[0::4], *b[2::4], *b[3::4]])

def derive_key(seq, sbox):
    buf = permute(seq)
    out = bytearray()
    ctr = 0
    for rcx in range(0, 0x40, 2):
        a = buf[rcx % len(buf)]
        b = buf[(rcx + 1) % len(buf)]
        row = IDX.get(a, 0)
        col = IDX.get(b, 0)
        ch = M_TBL[row * 6 + col]
        out.append(sbox[ch] ^ ctr)
        ctr = (ctr + 0x13) & 0xff
    return bytes(out)

def xtime(a):
    a &= 0xff
    return (((a << 1) ^ 0x1b) & 0xff) if (a & 0x80) else ((a << 1) & 0xff)

def mul(a, b):
    res = 0
    while b:
        if b & 1: res ^= a
        a = xtime(a)
        b >>= 1
    return res & 0xff

def inv_sbox(sbox):
    inv = [0] * 256
    for i, x in enumerate(sbox):
        inv[x] = i
    return inv

def key_expansion(key, sbox):
    Nk, Nb, Nr = 8, 4, 14
    w = [list(key[4 * i:4 * i + 4]) for i in range(Nk)]
    i = Nk
    while len(w) < Nb * (Nr + 1):
        temp = w[-1][:]
        if i % Nk == 0:
            temp = temp[1:] + temp[:1]
            temp = [sbox[x] for x in temp]
            temp[0] ^= RCON[i // Nk - 1]
        elif i % Nk == 4:
            temp = [sbox[x] for x in temp]
        w.append([a ^ b for a, b in zip(w[i - Nk], temp)])
        i += 1
    return [sum(w[4 * r:4 * r + 4], []) for r in range(Nr + 1)]

def decrypt_block(block, key, sbox):
    inv = inv_sbox(sbox)
    rk = key_expansion(key, sbox)
    s = bytearray(block)
    # Round 14
    for i in range(16): s[i] ^= rk[14][i]
    # InvShiftRows
    t = s[:]
    for r in range(4):
        row = [t[4 * c + r] for c in range(4)]
        if r: row = row[-r:] + row[:-r]
        for c in range(4): s[4 * c + r] = row[c]
    # InvSubBytes
    for i in range(16): s[i] = inv[s[i]]
    # Rounds 13..1
    for rnd in range(13, 0, -1):
        for i in range(16): s[i] ^= rk[rnd][i]
        for c in range(4):
            i = c * 4
            a = s[i:i + 4]
            s[i + 0] = mul(a[0], 14) ^ mul(a[1], 11) ^ mul(a[2], 13) ^ mul(a[3], 9)
            s[i + 1] = mul(a[0], 9) ^ mul(a[1], 14) ^ mul(a[2], 11) ^ mul(a[3], 13)
            s[i + 2] = mul(a[0], 13) ^ mul(a[1], 9) ^ mul(a[2], 14) ^ mul(a[3], 11)
            s[i + 3] = mul(a[0], 11) ^ mul(a[1], 13) ^ mul(a[2], 9) ^ mul(a[3], 14)
        t = s[:]
        for r in range(4):
            row = [t[4 * c + r] for c in range(4)]
            if r: row = row[-r:] + row[:-r]
            for c in range(4): s[4 * c + r] = row[c]
        for i in range(16): s[i] = inv[s[i]]
    for i in range(16): s[i] ^= rk[0][i]
    return bytes(s)

def main():
    apk_path = sys.argv[1] if len(sys.argv) > 1 else "app-release.apk"
    with zipfile.ZipFile(apk_path) as z:
        png = z.read("assets/hint.png")
    sbox = extract_sbox(png)

    md5 = hashlib.md5(SEQ.encode()).hexdigest()
    assert md5 == CHECK_MD5, f"SEQ 校验失败: {md5}"

    key = derive_key(SEQ, sbox)
    target = bytes(x ^ 0x66 for x in base64.b64decode(B64))
    pt = decrypt_block(target[:16], key, sbox) + decrypt_block(target[16:32], key, sbox)
    inner = pt.rstrip(b"\x00").decode("utf-8", errors="replace")
    print(f"flag = ISCC{{{inner}}}")

if __name__ == "__main__":
    main()
