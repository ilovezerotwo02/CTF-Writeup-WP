img = open('image.bin', 'rb').read()
M64 = (1 << 64) - 1

tab1 = img[0x8040:0x8050]
tab2 = img[0x8050:0x8060]
table = img[0x8010:0x8010 + 40]
print('table:', table[:34])

# ---- 0x14b0: 生成 16 字节密钥 ----
def gen_key():
    key = bytearray()
    eax = 2; dl = 0x29; r8b = 0x6d; r9 = 1
    while True:
        bl = tab1[r9 & 0xf]
        bl = (bl + dl) & 0xff
        bl = ((bl << 3) | (bl >> 5)) & 0xff
        sil = tab2[eax & 0xf]
        sil ^= r8b
        sil ^= bl
        key.append(sil)
        eax = (eax + 9) & 0xffffffff
        dl = (dl + 7) & 0xff
        r8b = (r8b + 0xd) & 0xff
        r9 += 5
        if r9 == 0x51:
            break
    return bytes(key)

key = gen_key()
print('key:', key.hex())

# ---- 0x1510: RC4 变体 ----
def rc4(data):
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i & 0xf]) & 0xff
        s[i], s[j] = s[j], s[i]
    out = bytearray(data)
    a = 0
    j = 0
    for k in range(1, 0x23):
        r8d = s[k]
        a = (a + r8d) & 0xffffffff
        jj = a & 0xff
        s[k], s[jj] = s[jj], s[k]
        t = (s[k] + s[jj]) & 0xff
        out[k - 1] ^= s[t]
    return bytes(out)

# ---- 比较循环：求每个位置需要的变换后字节 ----
req = bytearray()
r8 = 0; r11 = (-0x3da) & M64; ebx = 1; edi = 0
for i in range(34):
    # rdx:rax = r8 * 0xf0f0f0f0f0f0f0f1
    prod = r8 * 0xf0f0f0f0f0f0f0f1
    rdx = (prod >> 64) & M64
    rax = ((edi * 0xaaaaaaab) & M64) >> 0x21
    eax = (rax * 3) & 0xffffffff
    cl = (ebx - (eax & 0xff)) & 0xff
    rdx >>= 5
    idx = (0xb * i - 0x22 * rdx)
    tgt = table[idx]
    # al = rol8(((r11+0x2d)^in), cl) == tgt  → in = ror8(tgt,cl) ^ ((r11+0x2d)&0xff)
    base = ((r11 + 0x2d) & 0xffffffff) & 0xff
    # ror8
    v = tgt
    cl2 = cl % 8
    ror = ((v >> cl2) | (v << (8 - cl2))) & 0xff
    req.append(ror ^ base)
    r8 += 0xb
    r11 = (r11 + 0x1d) & M64
    ebx = (ebx + 1) & 0xffffffff
    edi += 1

print('required transformed:', bytes(req))
flag = rc4(bytes(req))
print('flag =', flag)
open('flag.txt', 'wb').write(flag)
