# -*- coding: utf-8 -*-
"""42 - 用 QR 尾部已知明文反推加密算法"""
import hashlib, random
from Crypto.Cipher import ARC4, AES, ChaCha20, Salsa20, Blowfish, DES

ENC = bytes.fromhex('f8eaf9fafa9df9ebced6ee9df3d6cfc3e6f8fdcae59eccc4d9c6f1ca')
TAIL = b'4857r4c7_3n0u6h?}'  # 17 chars, QR 内容
HEAD1 = b'HTUCTF{n07_'   # 假设1: not abstract enough?
HEAD2 = b'HTUCTF{1s_17_'   # 假设2: is it abstract enough?
FLAG1 = HEAD1 + TAIL       # 28 chars
FLAG2 = HEAD2 + TAIL

def rc4_ks(key, n, drop=0):
    c = ARC4.new(key)
    if drop: c.encrypt(b'\0'*drop)
    return c.encrypt(b'\0'*n)

def search(ks_pool, need, tag):
    idx = ks_pool.find(need)
    if idx >= 0:
        print('*** FOUND *** %s at offset %d' % (tag, idx))
    return idx

# 候选密钥流池
pools = {}
keys = [b'abstract', b'key:abstract', b'key:abstract\n', b'Abstract', b'4857r4c7',
        b'abstract_enough?', b'abstract\n', b'4857r4c7_3n0u6h?}',
        hashlib.md5(b'abstract').digest(), hashlib.sha256(b'abstract').digest()[:16],
        hashlib.sha256(b'abstract').digest()]
for k in keys:
    kn = k[:12].decode('latin1')
    pools['rc4:' + kn] = rc4_ks(k, 600)
    pools['rc4d256:' + kn] = rc4_ks(k, 600, 256)

# hash-CTR 流
for hname, h in [('md5', hashlib.md5), ('sha1', hashlib.sha1), ('sha256', hashlib.sha256)]:
    for key in [b'abstract', b'key:abstract']:
        ks = bytearray(); i = 0
        while len(ks) < 600:
            ks += h(key + i.to_bytes(4, 'big')).digest(); i += 1
        pools['hctr4-%s:%s' % (hname, key)] = bytes(ks)
        ks = bytearray(); i = 0
        while len(ks) < 600:
            ks += h(key + bytes([i % 256])).digest(); i += 1
        pools['hctr1-%s:%s' % (hname, key)] = bytes(ks)

# Python random 流
for sv in ['abstract', b'abstract', 'key:abstract']:
    for gn, gen in [('randint', lambda r: bytes(r.randint(0,255) for _ in range(600))),
                    ('randbytes', lambda r: r.randbytes(600) if hasattr(r,'randbytes') else bytes(r.randint(0,255) for _ in range(600)))]:
        r = random.Random(sv)
        try: pools['rand:%s:%s' % (sv, gn)] = gen(r)
        except Exception: pass

# ChaCha/Salsa
for kn, k in [('sha256', hashlib.sha256(b'abstract').digest()), ('pad', (b'abstract'*5)[:32])]:
    for nn, nc in [('z8', b'\0'*8), ('abs8', b'abstract'), ('z12', b'\0'*12)]:
        try:
            c = ChaCha20.new(key=k, nonce=nc)
            pools['chacha:%s:%s' % (kn, nn)] = c.encrypt(b'\0'*600)
        except Exception: pass
        try:
            c = Salsa20.new(key=k, nonce=nc[:8])
            pools['salsa:%s:%s' % (kn, nn)] = c.encrypt(b'\0'*600)
        except Exception: pass

print('流池数量:', len(pools))
# 已知明文假设
for fname, flag in [('FLAG1(n07)', FLAG1), ('FLAG2(1s_17)', FLAG2)]:
    ks_needed = bytes(a ^ b for a, b in zip(ENC, flag))
    print('%s 需要的ks: %s' % (fname, ks_needed.hex()))
    for pname, pool in pools.items():
        search(pool, ks_needed, '%s full-xor %s' % (fname, pname))
    # 尾部片段(位置无关搜索)
    tailks = bytes(a ^ b for a, b in zip(ENC[11:28], TAIL))
    for pname, pool in pools.items():
        search(pool, tailks, '%s tail-xor %s' % (fname, pname))
    # ADD 形式
    ks_add = bytes((a - b) & 0xff for a, b in zip(ENC, flag))
    for pname, pool in pools.items():
        search(pool, ks_add, '%s full-add %s' % (fname, pname))

# 也直接验证: RC4 ks[13:41] (header 连续流) 与 FLAG1/FLAG2
for kn, k in [('abstract', b'abstract'), ('key:abstract', b'key:abstract')]:
    ks = rc4_ks(k, 41)
    for fname, flag in [('FLAG1', FLAG1), ('FLAG2', FLAG2)]:
        dec = bytes(a ^ b for a, b in zip(ENC, ks[13:41]))
        if dec == flag:
            print('*** RC4 %s ks[13:41] EXACT MATCH %s ***' % (kn, fname))
print('done')
