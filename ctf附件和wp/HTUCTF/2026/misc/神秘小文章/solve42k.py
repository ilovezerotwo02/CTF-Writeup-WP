# -*- coding: utf-8 -*-
# 42 最终扫描: 全部分组密码流模式 × 密钥派生 × IV × 两种密钥流模型(K 和 K^0x80)
import hashlib, itertools

ENC = bytes.fromhex('f8eaf9fafa9df9ebced6ee9df3d6cfc3e6f8fdcae59eccc4d9c6f1ca')
TAIL = b'4857r4c7_3n0u6h?}'
K = bytes(ENC[11+i] ^ TAIL[i] for i in range(17))      # XOR 模型
k = bytes(x ^ 0x80 for x in K)                          # 0x80+(P^m) 模型
KA = bytes((ENC[11+i] - TAIL[i]) & 0xff for i in range(17))  # ADD 模型

hits = 0
def check(name, st):
    global hits
    n = len(st)
    for off in range(0, max(1, n - 16)):
        for kn, KK in (('K', K), ('k', k), ('A', KA)):
            if st[off:off+17] == KK:
                print('*** 命中 ***', name, kn, 'off', off); hits += 1

from Crypto.Cipher import AES, DES, DES3, Blowfish, ARC2, CAST, ARC4, ChaCha20, Salsa20

keysrcs = [b'abstract', b'key:abstract', b'key:abstract\n', TAIL, b'Abstract']
def derivs(src):
    out = []
    L = 0
    for pad in (b'\0', b' '):
        for sz in (8, 16, 24, 32):
            out.append(('pad%d%d' % (sz, pad[0]), (src * ((sz // len(src)) + 1))[:sz]))
    out.append(('md5', hashlib.md5(src).digest()))
    out.append(('sha1', hashlib.sha1(src).digest()))
    out.append(('sha256', hashlib.sha256(src).digest()))
    out.append(('sha256_16', hashlib.sha256(src).digest()[:16]))
    return out

ivsrcs = [b'', b'abstract', b'key:abstract', b'key:abstract\n', TAIL]
def ivs():
    out = [b'\0' * 16]
    for s in ivsrcs:
        if s:
            out.append((s * 3)[:16].ljust(16, b'\0'))
    out.append(hashlib.md5(b'abstract').digest())
    out.append(hashlib.sha256(b'abstract').digest()[:16])
    return out

IVS = ivs()
cipher_makers = []
for kn, kk in [(n, k) for src in keysrcs for n, k in derivs(src)]:
    cipher_makers.append((kn, kk))

count = 0
for kn, kk in cipher_makers:
    for cn, C in [('aes', AES), ('des', DES), ('3des', DES3), ('bf', Blowfish), ('rc2', ARC2), ('cast', CAST)]:
        # 密钥长度适配
        if cn == 'des':
            if len(kk) < 8: continue
            key = kk[:8]
            bs = 8
        elif cn == '3des':
            if len(kk) < 16: continue
            try: key = DES3.adjust_key_parity((kk * 2)[:24])
            except Exception: continue
            bs = 8
        elif cn == 'cast':
            key = kk[:16].ljust(16, b'\0'); bs = 8
        else:
            if len(kk) not in (16, 24, 32): continue
            key = kk; bs = 16
        ecb = C.new(key, C.MODE_ECB)
        for ivn, iv in enumerate(IVS):
            ivb = iv[:bs]
            # CTR
            st = b''; ctr = int.from_bytes(ivb, 'big')
            for _ in range(4):
                st += ecb.encrypt(ctr.to_bytes(bs, 'big')); ctr += 1
            check('%s-%s-%s-ctr-iv%d' % (cn, kn, kk[:6].hex()[:8], ivn), st)
            # LE counter
            st = b''; ctr = int.from_bytes(ivb, 'little')
            for _ in range(4):
                st += ecb.encrypt(ctr.to_bytes(bs, 'little')); ctr += 1
            check('%s-%s-ctrlle-iv%d' % (cn, kn, ivn), st)
            # OFB
            st = b''; o = ivb
            for _ in range(4):
                o = ecb.encrypt(o); st += o
            check('%s-%s-ofb-iv%d' % (cn, kn, ivn), st)
            # CFB (segment=block)
            st = b''; o = ivb
            for _ in range(4):
                o = ecb.encrypt(o); st += o  # CFB128 密文反馈=OFB? 不对, CFB: o=E(IV)^pt -> keystream=E(o')
            # 正确 CFB128 keystream: E(C_{i-1})
            st = b''; prev = ivb
            for _ in range(4):
                e = ecb.encrypt(prev); st += e; prev = e
            check('%s-%s-cfb-iv%d' % (cn, kn, ivn), st)
            count += 1

# ChaCha20 / Salsa20 with all key derivations
for src in keysrcs:
    for dn, dk in derivs(src):
        if len(dk) != 32: continue
        for nn, nonce in [(b'\0'*8, 8), (b'\0'*12, 12), (b'abstract', 8), (b'abstracten', 12),
                          (hashlib.md5(src).digest()[:8], 8), (hashlib.md5(src).digest()[:12], 12)]:
            try:
                check('chacha-%s-%s' % (dn, nn[:4].hex()), ChaCha20.new(key=dk, nonce=nonce).encrypt(b'\0'*128))
            except Exception: pass
            try:
                check('salsa-%s-%s' % (dn, nn[:4].hex()), Salsa20.new(key=dk, nonce=nonce).encrypt(b'\0'*128))
            except Exception: pass

# SM4-CTR (gmssl)
try:
    from gmssl.sm4 import CryptSM4, SM4_ENCRYPT
    for src in keysrcs:
        for kn, kk in derivs(src):
            if len(kk) != 16: continue
            c = CryptSM4(); c.set_key(kk, SM4_ENCRYPT)
            for ivn, iv in enumerate(IVS):
                st = b''; ctr = int.from_bytes(iv[:16], 'big')
                for _ in range(4):
                    st += c.crypt_ecb(ctr.to_bytes(16, 'big')); ctr += 1
                check('sm4-%s-iv%d' % (kn, ivn), st)
except Exception as e:
    print('sm4 skip', str(e)[:60])

# RC4-16bit (16位字 RC4, 密钥 = "abstract" 的16位单元)
def rc4_16(key16, n=64):
    S = list(range(65536)); j = 0
    for i in range(65536):
        j = (j + S[i] + key16[i % len(key16)]) & 0xffff
        S[i], S[j] = S[j], S[i]
    i = j = 0; out = []
    for _ in range(n):
        i = (i+1) & 0xffff; j = (j + S[i]) & 0xffff
        S[i], S[j] = S[j], S[i]
        out.append(S[(S[i]+S[j]) & 0xffff])
    return out

units = [(ENC[2*i] << 8) | ENC[2*i+1] for i in range(14)]
key16 = [0x0061, 0x0062, 0x0073, 0x0074, 0x0072, 0x0061, 0x0063, 0x0074]
try:
    ks16 = rc4_16(key16, 14)
    pt16 = [units[i] ^ ks16[i] for i in range(14)]
    print('rc4-16 pt:', bytes(u & 0xff for u in pt16), [hex(u) for u in pt16][:6])
    # 也试加法
    pt16b = [(units[i] - ks16[i]) & 0xffff for i in range(14)]
    print('rc4-16 sub:', bytes(u & 0xff for u in pt16b))
except Exception as e:
    print('rc4-16 err', e)

print('done, tested', count, 'configs, hits', hits)
