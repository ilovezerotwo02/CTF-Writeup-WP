# -*- coding: utf-8 -*-
# 42 题第二轮: 链式/位置哈希高位/完美幂/插入位置/SM4/UTF16BE
import hashlib

ENC = bytes.fromhex('f8eaf9fafa9df9ebced6ee9df3d6cfc3e6f8fdcae59eccc4d9c6f1ca')
TAIL = b'4857r4c7_3n0u6h?}'

def rep_ok_and_head(K, tag):
    """K: 位置11-27的密钥流。检查周期<=17一致性,恢复头部"""
    for L in range(1, 18):
        resid = {}; ok = True
        for i in range(17):
            r = (11+i) % L
            if r in resid and resid[r] != K[i]: ok = False; break
            resid[r] = K[i]
        if ok and len(resid) == L:
            print(tag, '周期', L, 'key=', bytes(resid[r] for r in range(L)).hex())
            return L, [resid[r] for r in range(L)]
    return None, None

# ---- A. 链式变体 ----
# ENC[i] = P[i] ^ K[i] ^ ENC[i-1]  (K 与 ENC 链)
K1 = bytes(ENC[11+i] ^ ENC[10+i] ^ TAIL[i] for i in range(17))
rep_ok_and_head(K1, '链XOR(ENC[i-1])')
# ENC[i] = P[i] ^ K[i] ^ P[i-1] -> K[i] = ENC[i]^P[i]^P[i-1]
K2 = bytes(ENC[11+i] ^ TAIL[i] ^ TAIL[i-1] for i in range(17))
rep_ok_and_head(K2, '链XOR(P[i-1])')
# ENC[i] = (P[i] + K[i] + P[i-1]) mod 256
K3 = bytes((ENC[11+i] - TAIL[i] - TAIL[i-1]) & 0xff for i in range(17))
rep_ok_and_head(K3, '链ADD(P[i-1])')
# 累积: ENC[i] = P[i] ^ K[i%8] ^ ENC[i-1] 已含; 再试 K=abstract 直接验证
for kn, key in [('abstract', b'abstract'), ('key:abstract', b'key:abstract')]:
    p1 = bytes((ENC[i] ^ (ENC[i-1] if i else 0) ^ key[i % 8]) for i in range(28))
    if TAIL in p1: print('链命中!', kn, p1)
    p2 = bytes(ENC[i] ^ p1[i-1] ^ key[i % 8] for i in range(28)) if False else None

# ---- B/C. 更多密钥素材 ----
ZW = set('\u200c\u200d\u202c\ufeff')
d = open('我不知道你在说什么.txt', encoding='utf-8').read()
vis = ''.join(ch for ch in d if ch not in ZW)
prefixes = ['在未命名的边界上','沿着沉默的内侧','向着没有方向的深处','顺着不可见的纹理',
            '循着未完成的弧线','沿着不确定的路径','在尚未命名的深处','于彼此错开的片刻',
            '循着看不见的折痕','在回返尚未发生时']
keysrcs = [b'abstract', TAIL, b'4857r4c7_3n0u6h?', '我不知道你在说什么'.encode(),
           ''.join(prefixes).encode(), vis[:29].encode('utf-8'), b'key:abstract',
           b'Clipboard_Screenshot', b'Clipboard', b'HTUCTF', hashlib.md5(b'abstract').digest(),
           hashlib.sha256(b'abstract').digest()]

def rc4(key, n=512):
    S = list(range(256)); j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xff; S[i], S[j] = S[j], S[i]
    i = j = 0; out = bytearray()
    for _ in range(n):
        i = (i+1) & 0xff; j = (j+S[i]) & 0xff; S[i], S[j] = S[j], S[i]
        out.append(S[(S[i]+S[j]) & 0xff])
    return bytes(out)

def try_streams(tag, st):
    for off in range(0, max(1, len(st)-27)):
        if st[off+11:off+28] == bytes(a^b for a,b in zip(ENC[11:28], TAIL)):
            pt = bytes(a^b for a,b in zip(ENC, st[off:off+28]))
            print('*** XOR命中 ***', tag, 'off', off, pt)
        if st[off+11:off+28] == bytes((a-b)&0xff for a,b in zip(ENC[11:28], TAIL)):
            pt = bytes((a-b)&0xff for a,b in zip(ENC, st[off:off+28]))
            print('*** SUB命中 ***', tag, 'off', off, pt)

for key in keysrcs:
    try_streams('RC4(%r)' % key[:12], rc4(key))
    for hn, H in [('md5',hashlib.md5),('sha1',hashlib.sha1),('sha256',hashlib.sha256),('blake2s',hashlib.blake2s)]:
        d0 = H(key).digest()
        try_streams('cycle %s %r' % (hn, key[:8]), bytes(d0[i % len(d0)] for i in range(512)))
        try_streams('pos %s %r' % (hn, key[:8]),
                    bytes(H(key + str(i).encode()).digest()[j] for i in range(28) for j in [0]))
        # digest[j] 逐位置
        for j in range(1, 16):
            st = bytes(H(key + str(i).encode()).digest()[j % len(H(key+str(i).encode()).digest())] for i in range(28))
            if st[11:28] == bytes(a^b for a,b in zip(ENC[11:28], TAIL)):
                print('*** poshash命中 ***', hn, key[:8], 'j', j, bytes(a^b for a,b in zip(ENC, st)))

# ---- D. 完美幂 (RSA 小指数) ----
for order in ('big', 'little'):
    N = int.from_bytes(ENC, order)
    for e in range(2, 9):
        r = round(N ** (1.0/e))
        for cand in range(max(0, r-2), r+3):
            if cand ** e == N:
                bs = cand.to_bytes((cand.bit_length()+7)//8, 'big')
                print('完美幂!', order, 'e', e, bs)

# ---- E. 零宽插入位置作为数据 ----
clusters = []; cur = []
for i, ch in enumerate(d):
    if ch in ZW: cur.append(i)
    else:
        if cur: clusters.append(cur); cur = []
if cur: clusters.append(cur)
offs = []
for c in clusters:
    st = c[0]
    j = st - 1
    while j >= 0 and d[j] not in ZW and d[j] not in '。，\n': j -= 1
    offs.append(st - (j+1))  # 句内可见偏移
print('插入偏移:', offs)
print('as ascii:', ''.join(chr(o+32) if 32 <= o+32 < 127 else '?' for o in offs))
print('mod94+33:', ''.join(chr((o % 94)+33) for o in offs))
# 簇所在句序号
sents = []; cur = ''
for ch in d:
    if ch in '。，\n':
        if cur.strip(): sents.append(cur)
        cur = ''
    else: cur += ch
if cur.strip(): sents.append(cur)
zwpos = []
ci = 0
for si, s in enumerate(sents):
    if any(c in ZW for c in s):
        zwpos.append(si)
print('ZW句序号:', zwpos)
print('句序号 ascii:', ''.join(chr(p % 128) if 32 <= p % 128 < 127 else '?' for p in zwpos))
# 差分
diffs = [zwpos[i+1]-zwpos[i] for i in range(len(zwpos)-1)]
print('句号差分:', diffs, 'ascii:', ''.join(chr(x+32) if 32 <= x+32 < 127 else '?' for x in diffs))

# ---- F. 句长 3bit 流 ----
import re, functools
lines = vis.split('\n')
lens_grid = []
for ln in lines:
    sents_l = [s.strip() for s in re.split(r'[。，]', ln) if s.strip()]
    prefix = functools.reduce(lambda a,b: a if b.startswith(a) else next((a[:i] for i in range(len(a),0,-1) if b.startswith(a[:i])), ''), sents_l)
    lens_grid.append([len(s[len(prefix):]) for s in sents_l])
mn = min(v for r in lens_grid for v in r)
bits = ''.join(format(v-mn, '03b') for r in lens_grid for v in r)
for off in range(8):
    out = bytearray()
    for i in range(off, len(bits)-7, 8):
        out.append(int(bits[i:i+8], 2))
    t = bytes(out); pr = sum(1 for b in t if 32 <= b < 127)
    if pr > len(t)*0.7 or b'HTU' in t or b'flag' in t:
        print('句长3bit off', off, t[:60])

# ---- G. UTF-16BE 解读常见解密结果 ----
def u16(be):
    try:
        s = be.decode('utf-16-be')
    except Exception:
        return None
    good = sum(1 for c in s if c.isprintable())
    return s if good == len(s) else None
for key in [b'abstract', b'key:abstract', b'key:abstract\n', b'abstract\n', TAIL]:
    for st in [rc4(key), bytes(hashlib.sha256(key).digest()[i%32] for i in range(28)),
               bytes(hashlib.md5(key).digest()[i%16] for i in range(28))]:
        for ksn, K in [('xor', None)]:
            pt = bytes(a^b for a,b in zip(ENC, st))
            s = u16(pt)
            if s: print('u16命中', key[:10], repr(s))
# 重复密钥解密后 u16
for key in [b'abstract', b'key:abstract\n', TAIL]:
    pt = bytes(ENC[i] ^ key[i % len(key)] for i in range(28))
    s = u16(pt)
    if s: print('u16 rep命中', key[:10], repr(s))
print('round2 done')
