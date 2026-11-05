# -*- coding: utf-8 -*-
"""42 - 第二轮: random种子流 / 抽象中文key / 索引理论 / hash-CTR / RC4变体"""
import hashlib, random, re
from Crypto.Cipher import ARC4

ENC = bytes.fromhex('f8eaf9fafa9df9ebced6ee9df3d6cfc3e6f8fdcae59eccc4d9c6f1ca')

def show(tag, dec):
    pr = sum(1 for b in dec if 32 <= b < 127)
    s = ''.join(chr(b) if 32 <= b < 127 else '.' for b in dec)
    if pr >= 26 or 'HTU' in s or 'flag' in s or '{' in s:
        print('%-36s %r' % (tag, s))
    try:
        t = dec.decode('utf-8')
        if 'HTU' in t or 'flag' in t:
            print('%-36s UTF8 %r' % (tag, t))
    except Exception:
        pass

# ---- 1. random 种子流 ----
for seed_name, sv in [('abstract-str', 'abstract'), ('abstract-bytes', b'abstract'),
                      ('key:abstract', 'key:abstract'), ('Abstract', 'Abstract'),
                      ('int8', int.from_bytes(b'abstract', 'big'))]:
    for gen_name, gen in [
        ('randint', lambda r: [r.randint(0, 255) for _ in range(28)]),
        ('randrange', lambda r: [r.randrange(256) for _ in range(28)]),
        ('getrandbits', lambda r: [r.getrandbits(8) for _ in range(28)]),
        ('randbytes', lambda r: list(r.randbytes(28)) if hasattr(r, 'randbytes') else [r.randint(0,255) for _ in range(28)]),
        ('randint1_255', lambda r: [r.randint(1, 255) for _ in range(28)]),
        ('choice', lambda r: [r.choice(range(256)) for _ in range(28)]),
    ]:
        try:
            r = random.Random(sv)
            ks = bytes(gen(r))
            show('rand/%s/%s/xor' % (seed_name, gen_name), bytes(a ^ b for a, b in zip(ENC, ks)))
            show('rand/%s/%s/sub' % (seed_name, gen_name), bytes((a - b) & 0xff for a, b in zip(ENC, ks)))
            show('rand/%s/%s/add' % (seed_name, gen_name), bytes((a + b) & 0xff for a, b in zip(ENC, ks)))
        except Exception:
            pass

# ---- 2. 抽象 / 中文 key ----
cn_keys = {
    '抽象-utf8': '抽象'.encode('utf-8'),
    '抽象-gbk': '抽象'.encode('gbk'),
    '神秘小文章-utf8': '神秘小文章'.encode('utf-8'),
    '我不知道你在说什么-utf8': '我不知道你在说什么'.encode('utf-8'),
}
for kn, k in cn_keys.items():
    # XOR/SUB/ADD 全偏移
    for op in ('xor', 'sub', 'add'):
        for off in range(len(k)):
            if op == 'xor':
                dec = bytes(ENC[i] ^ k[(i + off) % len(k)] for i in range(28))
            elif op == 'sub':
                dec = bytes((ENC[i] - k[(i + off) % len(k)]) & 0xff for i in range(28))
            else:
                dec = bytes((ENC[i] + k[(i + off) % len(k)]) & 0xff for i in range(28))
            pr = sum(1 for b in dec if 32 <= b < 127)
            if pr >= 26:
                print('%-36s %r' % ('%s/%s/off%d' % (op, kn, off), ''.join(chr(b) if 32 <= b < 127 else '.' for b in dec)))
            try:
                t = dec.decode('utf-8')
                if 'HTU' in t or 'flag' in t or ('{' in t and '}' in t):
                    print('%-36s UTF8 %r' % ('%s/%s/off%d' % (op, kn, off), t))
            except Exception:
                pass
    # RC4
    try:
        dec = ARC4.new(k).encrypt(ENC)
        show('rc4/%s' % kn, dec)
    except Exception:
        pass

# ---- 3. 索引理论: 密文字节作为文本索引 ----
d = open('我不知道你在说什么.txt', encoding='utf-8').read()
vis = ''.join(ch for ch in d if ord(ch) < 0x2000)
uniq_sorted = sorted(set(c for c in vis if '一' <= c <= '鿿'))
seen = set(); uniq_first = []
for c in vis:
    if '一' <= c <= '鿿' and c not in seen:
        seen.add(c); uniq_first.append(c)
import collections
cnt = collections.Counter(c for c in vis if '一' <= c <= '鿿')
uniq_freq = [c for c, _ in cnt.most_common()]
sents = [s for s in re.split(r'[。，]', vis) if s.strip()]
uniq_sents = list(dict.fromkeys(sents))
lines = vis.split('\n')

def idx_chars(idxf, table, tag):
    try:
        chars = ''.join(table[idxf(b)] for b in ENC)
        print('%-36s %s' % (tag, chars))
    except Exception as e:
        print('%-36s ERR %s' % (tag, str(e)[:30]))

for base_name, basefn in [('raw', lambda b: b), ('-0x80', lambda b: b - 0x80), ('-0x9d', lambda b: b - 0x9d)]:
    idx_chars(lambda b, f=basefn: f(b) % len(uniq_sorted), uniq_sorted, 'idx/%s/uniqsorted' % base_name)
    idx_chars(lambda b, f=basefn: f(b) % len(uniq_first), uniq_first, 'idx/%s/uniqfirst' % base_name)
    idx_chars(lambda b, f=basefn: f(b) % len(uniq_freq), uniq_freq, 'idx/%s/uniqfreq' % base_name)
    idx_chars(lambda b, f=basefn: f(b) % len(uniq_sents), uniq_sents, 'idx/%s/uniqsents' % base_name)
    idx_chars(lambda b, f=basefn: f(b) % len(sents), sents, 'idx/%s/sents' % base_name)
    idx_chars(lambda b, f=basefn: f(b) % len(vis), vis, 'idx/%s/vis' % base_name)

# ---- 4. hash-CTR 密钥流 ----
key = b'abstract'
for hname, h in [('md5', hashlib.md5), ('sha1', hashlib.sha1), ('sha256', hashlib.sha256)]:
    for ctr_mode in ('byte', 'int4', 'int8'):
        ks = bytearray()
        i = 0
        while len(ks) < 28:
            if ctr_mode == 'byte':
                blk = h(key + bytes([i])).digest()
            elif ctr_mode == 'int4':
                blk = h(key + i.to_bytes(4, 'big')).digest()
            else:
                blk = h(key + i.to_bytes(8, 'big')).digest()
            ks += blk; i += 1
        ks = bytes(ks[:28])
        show('hctr/%s/%s/xor' % (hname, ctr_mode), bytes(a ^ b for a, b in zip(ENC, ks)))
        show('hctr/%s/%s/sub' % (hname, ctr_mode), bytes((a - b) & 0xff for a, b in zip(ENC, ks)))
        # 也试 key||counter 与 counter||key
        ks2 = bytearray(); i = 0
        while len(ks2) < 28:
            if ctr_mode == 'byte':
                blk = h(bytes([i]) + key).digest()
            elif ctr_mode == 'int4':
                blk = h(i.to_bytes(4, 'big') + key).digest()
            else:
                blk = h(i.to_bytes(8, 'big') + key).digest()
            ks2 += blk; i += 1
        ks2 = bytes(ks2[:28])
        show('hctr2/%s/%s/xor' % (hname, ctr_mode), bytes(a ^ b for a, b in zip(ENC, ks2)))

# ---- 5. RC4 变体 KSA ----
def rc4_variant(key, data, ksa_rev=False, prga_swap_after=False):
    S = list(range(256)); j = 0
    if not ksa_rev:
        for i in range(256):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]
    else:
        for i in range(255, -1, -1):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]
    i = j = 0; out = bytearray()
    for b in data:
        i = (i + 1) % 256; j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) % 256])
    return bytes(out)

for vn, kw in [('rev', dict(ksa_rev=True)), ('std', dict())]:
    dec = rc4_variant(key, ENC, **kw)
    show('rc4v/%s' % vn, dec)

# 6. 密文自身可能与 "key:abstract\n" 有关系: 用前缀做密钥流
prefix = b'key:abstract\n'
show('prefix-xor', bytes(ENC[i] ^ prefix[i % 13] for i in range(28)))
show('prefix-sub', bytes((ENC[i] - prefix[i % 13]) & 0xff for i in range(28)))
show('prefix-add', bytes((ENC[i] + prefix[i % 13]) & 0xff for i in range(28)))

print('done')
