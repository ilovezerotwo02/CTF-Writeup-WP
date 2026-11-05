# -*- coding: utf-8 -*-
"""42 - 第四轮: 逐位置生成器 + RC4变体"""
import hashlib, hmac, random
from Crypto.Cipher import ARC4

ENC = bytes.fromhex('f8eaf9fafa9df9ebced6ee9df3d6cfc3e6f8fdcae59eccc4d9c6f1ca')

def check(tag, pt):
    pr = sum(1 for b in pt if 32 <= b < 127)
    s = ''.join(chr(b) if 32 <= b < 127 else '.' for b in pt)
    if pr >= 25 or s.startswith('H') or 'HTU' in s or 'flag' in s:
        print('*** %-40s %r' % (tag, s))
    try:
        t = pt.decode('utf-8')
        if 'HTU' in t or 'flag' in t or ('{' in t and '}' in t):
            print('*** %-40s UTF8 %r' % (tag, t))
    except Exception:
        pass

keys = {
    'abstract': b'abstract', 'key:abstract': b'key:abstract', '4857r4c7': b'4857r4c7',
    'abstract_enough': b'abstract_enough?', 'Abstract': b'Abstract',
    'chouxiang-u8': '抽象'.encode('utf-8'), 'chouxiang-gbk': '抽象'.encode('gbk'),
    'md5abs': hashlib.md5(b'abstract').digest(), 'sha256abs16': hashlib.sha256(b'abstract').digest()[:16],
    'sha256abs': hashlib.sha256(b'abstract').digest(), 'sha1abs': hashlib.sha1(b'abstract').digest(),
}

# ---- 1. 逐位置哈希: ks[i] = H(key || ctr)[j] ----
for kn, key in keys.items():
    for hn, H in [('md5', hashlib.md5), ('sha1', hashlib.sha1), ('sha256', hashlib.sha256)]:
        dlen = H(key).digest().__len__()
        for ctr_name, ctrf in [
            ('b1', lambda i: bytes([i & 0xff])),
            ('b1x', lambda i: bytes([(i+1) & 0xff])),
            ('i4be', lambda i: i.to_bytes(4, 'big')),
            ('i4le', lambda i: i.to_bytes(4, 'little')),
            ('str', lambda i: str(i).encode()),
            ('str1', lambda i: str(i+1).encode()),
        ]:
            for j in range(0, dlen, 1):
                ks = bytes(H(key + ctrf(i)).digest()[j] for i in range(28))
                check('ph/%s/%s/%s/j%d' % (kn, hn, ctr_name, j), bytes(a ^ b for a, b in zip(ENC, ks)))
        # counter 在前
        for ctr_name, ctrf in [('b1', lambda i: bytes([i & 0xff])), ('i4be', lambda i: i.to_bytes(4, 'big'))]:
            for j in range(dlen):
                ks = bytes(H(ctrf(i) + key).digest()[j] for i in range(28))
                check('phF/%s/%s/%s/j%d' % (kn, hn, ctr_name, j), bytes(a ^ b for a, b in zip(ENC, ks)))

# ---- 2. HMAC 逐位置 ----
for kn, key in keys.items():
    for hn in ('md5', 'sha1', 'sha256'):
        for ctr_name, ctrf in [('b1', lambda i: bytes([i & 0xff])), ('i4be', lambda i: i.to_bytes(4, 'big'))]:
            for j in range(0, 32, 4):
                try:
                    ks = bytes(hmac.new(key, ctrf(i), hn).digest()[j] for i in range(28))
                    check('hm/%s/%s/%s/j%d' % (kn, hn, ctr_name, j), bytes(a ^ b for a, b in zip(ENC, ks)))
                except Exception:
                    pass

# ---- 3. RC4 KSA/PRGA 变体 ----
def rc4v(key, data, variant):
    S = list(range(256)); j = 0
    kl = len(key)
    if variant == 'std':
        rng = range(256)
    elif variant == 'rev':
        rng = range(255, -1, -1)
    elif variant == 'x3':
        rng = range(768)
    for i in rng:
        j = (j + S[i % 256] + key[i % kl]) % 256
        S[i % 256], S[j] = S[j], S[i % 256]
    i = j = 0; out = bytearray()
    for b in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) % 256])
    return bytes(out)

for kn, key in keys.items():
    for v in ('std', 'rev', 'x3'):
        try:
            check('rc4v/%s/%s' % (kn, v), rc4v(key, ENC, v))
        except Exception as e:
            print('rc4v err', kn, v, str(e)[:40])

# ---- 4. 逐步密钥扩展: ks[i] = H(prev + key)[0] ----
for kn, key in keys.items():
    for hn, H in [('md5', hashlib.md5), ('sha256', hashlib.sha256)]:
        for j in range(4):
            ks = bytearray(); prev = key
            for i in range(28):
                prev = H(prev + key).digest()
                ks.append(prev[j])
            check('chain/%s/%s/j%d' % (kn, hn, j), bytes(a ^ b for a, b in zip(ENC, bytes(ks))))

# ---- 5. random 系统化 ----
for kn, sv in [('abs', 'abstract'), ('absb', b'abstract'), ('k:a', 'key:abstract'),
               ('leet', '4857r4c7'), ('int', int.from_bytes(b'abstract', 'big'))]:
    for gn, gen in [('randint', lambda r: [r.randint(0, 255) for _ in range(28)]),
                    ('randbytes', lambda r: list(r.randbytes(28)) if hasattr(r, 'randbytes') else None),
                    ('grb8', lambda r: [r.getrandbits(8) for _ in range(28)]),
                    ('urandom', lambda r: list(random.Random(sv).randbytes(28)) if hasattr(random.Random(sv), 'randbytes') else None)]:
        try:
            r = random.Random(sv)
            lst = gen(r)
            if lst is None: continue
            ks = bytes(lst)
            check('rand/%s/%s' % (kn, gn), bytes(a ^ b for a, b in zip(ENC, ks)))
            check('randS/%s/%s' % (kn, gn), bytes((a - b) & 0xff for a, b in zip(ENC, ks)))
            check('randA/%s/%s' % (kn, gn), bytes((a + b) & 0xff for a, b in zip(ENC, ks)))
        except Exception:
            pass

print('done')
