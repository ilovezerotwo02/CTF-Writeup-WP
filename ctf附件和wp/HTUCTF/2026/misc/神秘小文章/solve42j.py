# -*- coding: utf-8 -*-
# 42 终极扫描: EVP_BytesToKey(openssl enc -k abstract) + PBKDF2 + RC4变体 + 逐字节双射变换 + PHP/MSVC PRNG
import hashlib, itertools

ENC = bytes.fromhex('f8eaf9fafa9df9ebced6ee9df3d6cfc3e6f8fdcae59eccc4d9c6f1ca')
TAIL = b'4857r4c7_3n0u6h?}'

# 各种 P 侧双射下需要的密钥流
def swapnib(b): return ((b & 0xf) << 4) | ((b >> 4) & 0xf)
def bitrev(b):
    r = 0
    for _ in range(8): r = (r << 1) | (b & 1); b >>= 1
    return r
BIJ = {'id': lambda b: b, 'nib': swapnib, 'bitrev': bitrev, 'not': lambda b: b ^ 0xff}
KST = {}
for name, f in BIJ.items():
    KST['P-'+name] = bytes(f(TAIL[i]) ^ ENC[11+i] for i in range(17))  # ENC = T(P)^K

def match(name, stream, minlen=28):
    for kn, K in KST.items():
        L = len(K)
        for off in range(0, min(len(stream) - L + 1, 4096)):
            if stream[off:off+L] == K:
                print('*** 命中 ***', name, kn, 'off', off)
                return True
    return False

# ---------- EVP_BytesToKey ----------
def evp(pw, keylen, ivlen, digest):
    d = b''; prev = b''
    while len(d) < keylen + ivlen:
        prev = digest(prev + pw + b'').digest()
        d += prev
    return d[:keylen], d[keylen:keylen+ivlen]

hits = 0
for pw in [b'abstract', b'key:abstract', TAIL]:
    for dname, D in [('md5', hashlib.md5), ('sha256', hashlib.sha256), ('sha1', hashlib.sha1)]:
        for kl, ivl, cn in [(16,16,'aes128'), (32,16,'aes256'), (24,16,'aes192'), (8,8,'des'), (16,8,'bf')]:
            key, iv = evp(pw, kl, ivl, D)
            from Crypto.Cipher import AES, DES, Blowfish
            for mode, mn in [('ctr','CTR'), ('ofb','OFB'), ('cfb','CFB8'), ('cfb128','CFB128')]:
                try:
                    if cn == 'aes128' or cn == 'aes256' or cn == 'aes192':
                        C = AES.new(key, AES.MODE_ECB)
                    elif cn == 'des':
                        C = DES.new(key, DES.MODE_ECB)
                    else:
                        C = Blowfish.new(key, Blowfish.MODE_ECB)
                except Exception:
                    continue
                # 手工 CTR/OFB/CFB 流
                if mn == 'CTR':
                    st = b''
                    ctr = int.from_bytes(iv, 'big')
                    for _ in range(4):
                        st += C.encrypt(ctr.to_bytes(C.block_size, 'big')); ctr += 1
                elif mn == 'OFB':
                    st = b''; o = iv
                    for _ in range(4):
                        o = C.encrypt(o); st += o
                elif mn == 'CFB8':
                    st = b''; o = iv
                    for _ in range(64):
                        o = C.encrypt(o)[:1] if False else b''
                        e = C.encrypt(o if o else iv)  # 简化: 跳过CFB8
                        break
                    continue
                else:  # CFB128
                    st = b''; o = iv
                    for _ in range(4):
                        e = C.encrypt(o); st += e; o = e
                if match('EVP-%s-%s-%s-%s' % (pw[:8], dname, cn, mn), st):
                    hits += 1
print('EVP done', hits)

# ---------- openssl pbkdf2 ----------
for pw in [b'abstract', b'key:abstract']:
    for iters in (1, 2048, 10000, 4096):
        for kl in (16, 32):
            key = hashlib.pbkdf2_hmac('sha256', pw, b'', iters, kl)
            iv = hashlib.pbkdf2_hmac('sha256', pw, b'', iters, 16)
            from Crypto.Cipher import AES
            try:
                C = AES.new(key, AES.MODE_ECB)
                st = b''; ctr = int.from_bytes(iv, 'big')
                for _ in range(4):
                    st += C.encrypt(ctr.to_bytes(16, 'big')); ctr += 1
                match('PBKDF2-%s-%d-%d' % (pw[:8], iters, kl), st)
            except Exception: pass

# ---------- RC4 变体 ----------
def rc4v(key, variant, n=512):
    S = list(range(256)); j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xff
        S[i], S[j] = S[j], S[i]
    i = j = 0; out = bytearray()
    for _ in range(n):
        i = (i+1) & 0xff; j = (j + S[i]) & 0xff
        if variant == 'std':
            S[i], S[j] = S[j], S[i]; out.append(S[(S[i]+S[j]) & 0xff])
        elif variant == 'pre':
            out.append(S[(S[i]+S[j]) & 0xff]); S[i], S[j] = S[j], S[i]
        elif variant == 'si':
            S[i], S[j] = S[j], S[i]; out.append(S[i])
        elif variant == 'noswap':
            out.append(S[(S[i]+S[j]) & 0xff])
        elif variant == 'j1':
            j = (j + S[i] + 1) & 0xff; S[i], S[j] = S[j], S[i]; out.append(S[(S[i]+S[j]) & 0xff])
    return bytes(out)

rc4keys = [b'abstract', b'key:abstract', b'key:abstract\n', TAIL, b'abstract'*2, b'abstract'*3,
           hashlib.md5(b'abstract').digest(), hashlib.sha256(b'abstract').digest()]
for k in rc4keys:
    for v in ('std','pre','si','noswap','j1'):
        if match('RC4v-%s-%s' % (k[:10], v), rc4v(k, v)):
            hits += 1

# ---------- PHP mt_rand / MSVC rand ----------
def php_mt_stream(seed, n=64):
    st = [0]*624
    st[0] = seed & 0xffffffff
    for i in range(1, 624):
        st[i] = (1812433253 * (st[i-1] ^ (st[i-1] >> 30)) + i) & 0xffffffff
    idx = 624
    def gen32():
        nonlocal idx
        if idx >= 624:
            for i in range(624):
                y = (st[i] & 0x80000000) | (st[(i+1) % 624] & 0x7fffffff)
                nxt = y >> 1
                if y & 1: nxt ^= 0x9908b0df
                st[i] = st[(i+397) % 624] ^ nxt
            idx = 0
        y = st[idx]; idx += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9d2c5680
        y ^= (y << 15) & 0xefc60000
        y ^= y >> 18
        return y & 0xffffffff
    out = bytearray()
    for _ in range(n):
        v = gen32()
        out.append((v >> 1) & 0xff)  # php mt_rand = int31
    return bytes(out)
for seed in (0, 1, 852, 0x61627374, 0x74627361, 1234, 2026, 0xdeadbeef):
    if match('phpmt-%d' % seed, php_mt_stream(seed)): hits += 1

def msvc_stream(seed, n=64):
    out = bytearray(); s = seed & 0xffffffff
    for _ in range(n):
        s = (s * 214013 + 2531011) & 0xffffffff
        out.append(((s >> 16) & 0x7fff) & 0xff)
    return bytes(out)
for seed in (0, 1, 852, 0x61627374):
    if match('msvc-%d' % seed, msvc_stream(seed)): hits += 1

# glibc rand (多种子)
import sys
sys.path.insert(0, 'D:/桌面/htu/pwn/game')
try:
    from rand_glibc import GlibcRand
    for seed in list(range(0, 64)) + [852, 0x61627374, 0x74627361, 1635, 2026]:
        try:
            r = GlibcRand(seed)
            if match('glibc-%d' % seed, bytes(r.next() & 0xff for _ in range(64))): hits += 1
        except Exception: pass
except Exception as e:
    print('glibc skip', str(e)[:40])

# python random 多种子
import random
for sn, seed in [('852',852), ('absint',int.from_bytes(b'abstract','big')), ('str','abstract'),
                 ('md5int',int(hashlib.md5(b'abstract').hexdigest(),16))]:
    random.seed(seed)
    if match('pyrand-%s' % sn, random.randbytes(256)): hits += 1
    random.seed(seed)
    if match('pyrandb-%s' % sn, bytes(random.getrandbits(8) for _ in range(256))): hits += 1

print('total hits', hits)
