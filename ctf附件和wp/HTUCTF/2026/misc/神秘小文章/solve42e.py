# -*- coding: utf-8 -*-
"""42 - 第三轮: 全位置尾部搜索 + 更多流密码"""
import hashlib, hmac, random
from Crypto.Cipher import ARC4, AES, ChaCha20, Salsa20

ENC = bytes.fromhex('f8eaf9fafa9df9ebced6ee9df3d6cfc3e6f8fdcae59eccc4d9c6f1ca')
TAIL = b'4857r4c7_3n0u6h?}'

# 构造所有位置的尾部密钥流片段
frags = {}
for p in range(0, 12):  # 尾部起点 0..11
    ks = bytes(ENC[p+i] ^ TAIL[i] for i in range(17))
    frags[('xor', p)] = ks
    ks2 = bytes((ENC[p+i] - TAIL[i]) & 0xff for i in range(17))
    frags[('sub', p)] = ks2

def rc4_ks(key, n):
    return ARC4.new(key).encrypt(b'\0' * n)

pools = {}
keys = [b'abstract', b'key:abstract', b'key:abstract\n', b'Abstract', b'ABSTRACT',
        b'4857r4c7', b'abstract_enough?', b'abstract\n', b' abstract',
        hashlib.md5(b'abstract').digest(), hashlib.sha1(b'abstract').digest()[:16],
        hashlib.sha256(b'abstract').digest()[:16], hashlib.sha256(b'abstract').digest(),
        hashlib.md5(b'key:abstract').digest(), b'abstract' * 2, b'abstract' * 4]
for k in keys:
    kn = k[:10].decode('latin1').replace('\n', '_')
    try: pools['rc4:' + kn] = rc4_ks(k, 8192)
    except Exception: pass

# 链式哈希流
for hname, h in [('md5', hashlib.md5), ('sha1', hashlib.sha1), ('sha256', hashlib.sha256)]:
    for key in [b'abstract', b'key:abstract']:
        ks = bytearray(); prev = key
        while len(ks) < 8192:
            prev = h(prev).digest(); ks += prev
        pools['chain-%s:%s' % (hname, key[:9].decode())] = bytes(ks)
        # HMAC-CTR
        ks = bytearray(); i = 0
        while len(ks) < 8192:
            ks += hmac.new(key, i.to_bytes(8, 'big'), hname).digest(); i += 1
        pools['hmac8-%s:%s' % (hname, key[:9].decode())] = bytes(ks)

# PBKDF2 直接作为 28 字节密钥流
for hn in ('md5', 'sha1', 'sha256'):
    for it in (1, 10, 100, 1000, 2048, 10000):
        for salt in (b'', b'abstract', b'key:abstract', b'salt'):
            try:
                ks = hashlib.pbkdf2_hmac(hn, b'abstract', salt, it, dklen=28)
                pt = bytes(a ^ b for a, b in zip(ENC, ks))
                pr = sum(1 for b in pt if 32 <= b < 127)
                if pr >= 26 or b'H' == pt[:1] or b'f' == pt[:1]:
                    print('PBKDF2 %s it%d salt%s -> %r' % (hn, it, salt, pt))
                pt2 = bytes((a - b) & 0xff for a, b in zip(ENC, ks))
                pr2 = sum(1 for b in pt2 if 32 <= b < 127)
                if pr2 >= 26:
                    print('PBKDF2sub %s it%d salt%s -> %r' % (hn, it, salt, pt2))
            except Exception:
                pass

# AES-CTR 各种 nonce, 32字节key
k32 = hashlib.sha256(b'abstract').digest()
for nn, nc in [('z4', b'\0'*4), ('z8', b'\0'*8), ('z12', b'\0'*12), ('z16', b'\0'*16),
               ('abs', b'abstract'), ('abs8', b'abstract')]:
    try:
        if len(nc) == 16:
            c = AES.new(k32, AES.MODE_CTR, initial_value=int.from_bytes(nc, 'big'), nonce=b'')
        else:
            c = AES.new(k32, AES.MODE_CTR, nonce=nc)
        pt = c.decrypt(ENC)
        pr = sum(1 for b in pt if 32 <= b < 127)
        if pr >= 26:
            print('AES256-CTR %s -> %r' % (nn, pt))
    except Exception: pass

found = 0
for pname, pool in pools.items():
    for (kind, p), frag in frags.items():
        idx = pool.find(frag)
        if idx >= 0:
            print('*** FOUND *** %s %s p=%d 在 %s 偏移 %d' % (kind, 'xor' if kind=='xor' else 'sub', p, pname, idx))
            found += 1
print('搜索完成, 命中', found)
