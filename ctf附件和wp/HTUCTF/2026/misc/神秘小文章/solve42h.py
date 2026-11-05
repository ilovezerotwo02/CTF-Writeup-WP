# -*- coding: utf-8 -*-
# 42 题:用已知明文尾部(17字节)做"密钥流精确匹配"判定
# ENC[11:28] ^ TAIL = 真实密钥流 K[11:28]。任何生成器只要在对应位置匹配即命中。
import hashlib, itertools

ENC = bytes.fromhex('f8eaf9fafa9df9ebced6ee9df3d6cfc3e6f8fdcae59eccc4d9c6f1ca')
TAIL = b'4857r4c7_3n0u6h?}'
KX = bytes(ENC[11+i] ^ TAIL[i] for i in range(17))          # XOR 密钥流
KA = bytes((ENC[11+i] - TAIL[i]) & 0xff for i in range(17))  # ENC = P + KS
KD = bytes((TAIL[i] - ENC[11+i]) & 0xff for i in range(17))  # ENC = P - KS

HITS = []
def check(name, stream, off=0):
    """stream: 生成的密钥流(从位置 off 对应明文位置 0)"""
    for kn, K in (('xor', KX), ('add', KA), ('sub', KD)):
        seg = stream[off+11:off+28]
        if len(seg) == 17 and seg == K:
            HITS.append((name, kn, off))
            print('*** HIT ***', name, kn, 'off', off)

# ---------- RC4 家族 ----------
def rc4(key, n=4096):
    S = list(range(256)); j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xff
        S[i], S[j] = S[j], S[i]
    i = j = 0; out = bytearray()
    for _ in range(n):
        i = (i+1) & 0xff; j = (j + S[i]) & 0xff
        S[i], S[j] = S[j], S[i]
        out.append(S[(S[i]+S[j]) & 0xff])
    return bytes(out)

rc4_keys = [b'abstract', b'Abstract', b'ABSTRACT', b'key:abstract', b'key:abstract\n',
            b'abstract\n', TAIL, b'abstract_enough?', b'n0t_abstract_enough?',
            b'4857r4c7_3n0u6h?', b'HTUCTF', b'abstract\x00', b'abstract ',
            hashlib.md5(b'abstract').digest(), hashlib.sha256(b'abstract').digest()[:16],
            hashlib.sha256(b'abstract').digest()]
for k in rc4_keys:
    st = rc4(k)
    for off in range(0, 2048):
        check('RC4(%s)' % k[:16], st, off)

# ---------- 逐位置哈希 ----------
keysrcs = [b'abstract', b'Abstract', b'key:abstract', b'key:abstract\n', b'abstract\n',
           TAIL, b'HTUCTF', b'']
hashes = [('md5', hashlib.md5), ('sha1', hashlib.sha1), ('sha256', hashlib.sha256),
          ('sha512', hashlib.sha512), ('blake2s', hashlib.blake2s), ('sha3_256', hashlib.sha3_256)]
for hn, H in hashes:
    for key in keysrcs:
        for fmtn, fmt in [('k+i', lambda key,i: key + str(i).encode()),
                          ('i+k', lambda key,i: str(i).encode() + key),
                          ('k+b', lambda key,i: key + bytes([i])),
                          ('k+i4', lambda key,i: key + i.to_bytes(4,'big')),
                          ('k+i4l', lambda key,i: key + i.to_bytes(4,'little'))]:
            st = bytes(H(fmt(key,i)).digest()[0] for i in range(28))
            check('poshash %s %s %s' % (hn, key[:10], fmtn), st)

# ---------- 哈希摘要循环/链 ----------
for hn, H in hashes:
    for key in keysrcs:
        d = H(key).digest()
        L = len(d)
        st = bytes(d[i % L] for i in range(28))
        check('digestcycle %s %s' % (hn, key[:10]), st)
        # 链式
        chain = d; out = bytearray()
        for i in range(28):
            out.append(chain[i % len(chain)])
        cur = d
        while len(out) < 28:
            cur = H(cur).digest(); out.extend(cur)
        check('digestchain %s %s' % (hn, key[:10]), bytes(out[:28]))

# shake 流
for key in keysrcs:
    if key:
        st = hashlib.shake_128(key).digest(64)
        check('shake128 %s' % key[:10], st)
        st = hashlib.shake_256(key).digest(64)
        check('shake256 %s' % key[:10], st)
        st = hashlib.blake2s(b'', key=key, digest_size=28).digest()
        check('blake2s-keyed %s' % key[:10], st)
        st = hashlib.blake2s(key=key, digest_size=28).digest() if False else st
        st = hashlib.blake2b(key=key, digest_size=28).digest()
        check('blake2b-keyed %s' % key[:10], st)

# ---------- AES-CTR / OFB / CFB / ChaCha20 / Salsa20 ----------
from Crypto.Cipher import AES, ChaCha20, Salsa20
from hashlib import md5, sha256
def ctr_stream(key, nonce16):
    e = AES.new(key, AES.MODE_ECB)
    out = bytearray(); ctr = int.from_bytes(nonce16, 'big')
    while len(out) < 64:
        out.extend(e.encrypt(ctr.to_bytes(16, 'big')))
        ctr += 1
    return bytes(out[:64])

aes_keys = [('raw', b'abstract'.ljust(16, b'\0')), ('md5', md5(b'abstract').digest()),
            ('sha256', sha256(b'abstract').digest()),
            ('sha256_16', sha256(b'abstract').digest()[:16]),
            ('md5ka', md5(b'key:abstract').digest())]
ivs = [b'\0'*16, b'abstract'.ljust(16,b'\0'), b'key:abstract\n'[:16].ljust(16,b'\0'),
      (b'abstract'*2), sha256(b'abstract').digest()[:16], md5(b'abstract').digest()]
for kn, k in aes_keys:
    kk = k[:32] if len(k)>=32 else k
    for ivn, iv in enumerate(ivs):
        try:
            check('AESCTR %s iv%d' % (kn, ivn), ctr_stream(kk, iv))
        except Exception as e:
            pass
        try:
            c = AES.new(kk[:16] if len(kk)>=16 else kk, AES.MODE_OFB, iv=iv[:16])
            check('AESOFB %s iv%d' % (kn, ivn), c.encrypt(b'\0'*64))
        except Exception: pass
        try:
            c = AES.new(kk[:16] if len(kk)>=16 else kk, AES.MODE_CFB, iv=iv[:16], segment_size=128)
            check('AESCFB %s iv%d' % (kn, ivn), c.encrypt(b'\0'*64))
        except Exception: pass

for kn, k in [('sha256', sha256(b'abstract').digest())]:
    for nn, nonce in [(b'\0'*8, 8), (b'abstract', 8), (b'\0'*12, 12), (b'abstracten', 12)]:
        try:
            c = ChaCha20.new(key=k, nonce=nonce)
            check('ChaCha20 %s' % nn.decode('latin1'), c.encrypt(b'\0'*64))
        except Exception: pass
    for nn, nonce in [(b'\0'*8, 8), (b'abstract', 8)]:
        try:
            c = Salsa20.new(key=k, nonce=nonce)
            check('Salsa20 %s' % nn.decode('latin1'), c.encrypt(b'\0'*64))
        except Exception: pass

# ---------- PRNG ----------
import random, sys
for seedn, seed in [('852', 852), ('absint', int.from_bytes(b'abstract','big')),
                    ('str', 'abstract'), ('bytes', b'abstract')]:
    random.seed(seed); st = bytes(random.randbytes(64))
    check('pyrand %s' % seedn, st)
    random.seed(seed); st = bytes(random.getrandbits(8) for _ in range(64))
    check('pyrandbits %s' % seedn, st)

sys.path.insert(0, 'D:/桌面/htu/pwn/game')
try:
    from rand_glibc import GlibcRand
    for seed in (0, 1, 852, 0x61627374, 0x74627361, 2026):
        r = GlibcRand(seed)
        st = bytes(r.next() & 0xff for _ in range(64))
        check('glibc %d' % seed, st)
except Exception as e:
    print('glibc skip', str(e)[:40])

class JR:
    def __init__(s, seed):
        s.seed = (seed ^ 0x5DEECE66D) & ((1<<48)-1)
    def next8(s):
        s.seed = (s.seed * 0x5DEECE66D + 0xB) & ((1<<48)-1)
        return (s.seed >> 40) & 0xff
for seed in (0, 1, 852, 0x61627374):
    j = JR(seed); st = bytes(j.next8() for _ in range(64))
    check('java %d' % seed, st)

# ---------- 可见文本滑窗(精确) ----------
ZW = set('\u200c\u200d\u202c\ufeff')
d = open('我不知道你在说什么.txt', encoding='utf-8').read()
vis = ''.join(ch for ch in d if ch not in ZW)
for encn, vb in [('utf8', vis.encode('utf-8')), ('gbk', vis.encode('gbk', errors='ignore'))]:
    for off in range(len(vb) - 27):
        check('text-%s off%d' % (encn, off), vb, off)

# ---------- 代数: ks[i] = f(key, i) ----------
key = b'abstract'
for a in range(-8, 9):
    for b in range(0, 256, 1):
        st = bytes((key[i % 8] + a*i + b) & 0xff for i in range(28))
        check('alg k+%d*i+%d' % (a, b), st)
        st = bytes((key[i % 8] ^ ((a*i + b) & 0xff)) for i in range(28))
        check('algx k^(%d*i+%d)' % (a, b), st)

print('---- 完成, 命中数:', len(HITS))
