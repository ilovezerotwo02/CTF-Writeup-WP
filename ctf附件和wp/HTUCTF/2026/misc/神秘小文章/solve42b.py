# -*- coding: utf-8 -*-
"""42 神秘小文章 - 系统化解密 28 字节密文 (key:abstract)"""
import hashlib, itertools, re
from Crypto.Cipher import AES, DES, DES3, Blowfish, ARC4, ChaCha20, Salsa20

ENC = bytes.fromhex('f8eaf9fafa9df9ebced6ee9df3d6cfc3e6f8fdcae59eccc4d9c6f1ca')
KEYSRC = b'abstract'

def score(dec):
    """给解密结果打分: flag 关键词 / 全可打印 / 中文"""
    hits = []
    s = None
    try:
        s = dec.decode('utf-8')
        if any(w in s for w in ('HTU', 'flag', 'FLAG', '{')):
            hits.append(('kw-utf8', s))
    except Exception:
        pass
    pr = sum(1 for b in dec if 32 <= b < 127)
    if pr == len(dec):
        hits.append(('all-print', dec.decode('latin1')))
    elif pr >= len(dec) - 2 and len(dec) > 10:
        hits.append(('near-print', dec.decode('latin1')))
    # GBK 中文
    try:
        g = dec.decode('gbk')
        if sum(1 for c in g if '\u4e00' <= c <= '\u9fff') >= 4:
            hits.append(('gbk', g))
    except Exception:
        pass
    # UTF-16-BE (若是 00xx 形式)
    if len(dec) % 2 == 0:
        try:
            u = dec.decode('utf-16-be')
            if all(32 <= ord(c) < 127 for c in u):
                hits.append(('u16be', u))
        except Exception:
            pass
    return hits

def rc4(key, data, drop=0):
    c = ARC4.new(key)
    if drop:
        c.encrypt(b'\0' * drop)
    return c.encrypt(data)

results = []

# ---- 1. RC4 各种密钥 + drop ----
rc4_keys = {
    'abstract': KEYSRC,
    'key:abstract': b'key:abstract',
    'key:abstract\\n': b'key:abstract\n',
    'abstract\\n': b'abstract\n',
    'Abstract': b'Abstract',
    'md5(abstract)': hashlib.md5(KEYSRC).digest(),
    'sha256(abstract)[:16]': hashlib.sha256(KEYSRC).digest()[:16],
    'sha1(abstract)[:16]': hashlib.sha1(KEYSRC).digest()[:16],
    'abstractx2': KEYSRC * 2,
    'tcartsba': KEYSRC[::-1],
    'md5(key:abstract)': hashlib.md5(b'key:abstract').digest(),
    'md5(file)': hashlib.md5(open('我不知道你在说什么.txt','rb').read()).digest(),
    'md5(vis)': hashlib.md5(''.join(c for c in open('我不知道你在说什么.txt',encoding='utf-8').read() if ord(c) < 0x2000).encode('utf-8')).digest(),
}
for kn, k in rc4_keys.items():
    for drop in (0, 256, 768):
        try:
            dec = rc4(k, ENC, drop)
            for tag, txt in score(dec):
                results.append(('RC4/%s/drop%d/%s' % (kn, drop, tag), txt))
        except Exception as e:
            pass

# ---- 2. DES (key 正好 8 字节 = abstract) ----
for iv_name, iv in [('zero', b'\0'*8), ('abstract', KEYSRC), ('enc8', ENC[:8])]:
    for mode_name, mode in [('CFB', DES.MODE_CFB), ('OFB', DES.MODE_OFB), ('CBC', DES.MODE_CBC)]:
        try:
            c = DES.new(KEYSRC, mode, iv=iv)
            dec = c.decrypt(ENC)
            for tag, txt in score(dec):
                results.append(('DES/%s/%s/%s' % (mode_name, iv_name, tag), txt))
        except Exception:
            pass
try:
    dec = DES.new(KEYSRC, DES.MODE_ECB).decrypt(ENC[:24])
    for tag, txt in score(dec):
        results.append(('DES/ECB/%s' % tag, txt))
except Exception:
    pass

# ---- 3. Blowfish (变长密钥, 8字节合法) ----
bf_keys = {'abstract': KEYSRC, 'key:abstract': b'key:abstract', 'abstractx2': KEYSRC*2,
           'Abstract': b'Abstract'}
for kn, k in bf_keys.items():
    for iv_name, iv in [('zero', b'\0'*8), ('abstract', KEYSRC), ('enc8', ENC[:8])]:
        for mode_name, mode in [('CFB', Blowfish.MODE_CFB), ('OFB', Blowfish.MODE_OFB)]:
            try:
                c = Blowfish.new(k, mode, iv=iv)
                dec = c.decrypt(ENC)
                for tag, txt in score(dec):
                    results.append(('BF/%s/%s/%s/%s' % (kn, mode_name, iv_name, tag), txt))
            except Exception:
                pass

# ---- 4. EVP_BytesToKey (openssl 风格, MD5, 无盐) ----
def evp(password, key_len, iv_len):
    dtot = b''; d = b''
    while len(dtot) < key_len + iv_len:
        d = hashlib.md5(d + password).digest()
        dtot += d
    return dtot[:key_len], dtot[key_len:key_len+iv_len]

for pw in [b'abstract', b'key:abstract']:
    for label, klen, ilen in [('AES128', 16, 16), ('AES192', 24, 16), ('AES256', 32, 16), ('RC4k16', 16, 0)]:
        key, iv = evp(pw, klen, ilen)
        if label == 'RC4k16':
            dec = rc4(key, ENC)
            for tag, txt in score(dec):
                results.append(('EVP/%s/%s/%s' % (pw.decode(), label, tag), txt))
            continue
        for mode_name, mkw in [('CTR', dict(nonce=iv[:8])), ('CFB', dict(iv=iv)), ('OFB', dict(iv=iv))]:
            try:
                c = AES.new(key, AES.MODE_CTR if mode_name=='CTR' else (AES.MODE_CFB if mode_name=='CFB' else AES.MODE_OFB), **mkw)
                dec = c.decrypt(ENC)
                for tag, txt in score(dec):
                    results.append(('EVP/%s/%s/%s/%s' % (pw.decode(), label, mode_name, tag), txt))
            except Exception:
                pass

# ---- 5. ChaCha20 / Salsa20 ----
for kn, k in [('sha256', hashlib.sha256(KEYSRC).digest()), ('abstract-pad', (KEYSRC*4)[:32])]:
    for nn, nonce in [('zero8', b'\0'*8), ('abstract8', KEYSRC), ('enc8', ENC[:8])]:
        try:
            c = ChaCha20.new(key=k, nonce=nonce)
            dec = c.decrypt(ENC)
            for tag, txt in score(dec):
                results.append(('ChaCha/%s/%s/%s' % (kn, nn, tag), txt))
        except Exception:
            pass
        try:
            c = Salsa20.new(key=k, nonce=nonce)
            dec = c.decrypt(ENC)
            for tag, txt in score(dec):
                results.append(('Salsa/%s/%s/%s' % (kn, nn, tag), txt))
        except Exception:
            pass

# ---- 6. XOR/SUB/ADD 全偏移, 含 key:abstract 12 字节 ----
for kn, key in [('abstract', KEYSRC), ('key:abstract', b'key:abstract')]:
    for op in ('xor', 'sub', 'add'):
        for off in range(len(key)):
            if op == 'xor':
                dec = bytes(ENC[i] ^ key[(i+off) % len(key)] for i in range(28))
            elif op == 'sub':
                dec = bytes((ENC[i] - key[(i+off) % len(key)]) & 0xff for i in range(28))
            else:
                dec = bytes((ENC[i] + key[(i+off) % len(key)]) & 0xff for i in range(28))
            for tag, txt in score(dec):
                results.append(('%s/%s/off%d/%s' % (op, kn, off, tag), txt))

# ---- 7. a=1..t=20 序号密钥 ----
kseq = bytes(b - 96 for b in KEYSRC)  # 1,2,19,20,18,1,3,20
for op in ('xor', 'sub', 'add'):
    if op == 'xor':
        dec = bytes(ENC[i] ^ kseq[i % 8] for i in range(28))
    elif op == 'sub':
        dec = bytes((ENC[i] - kseq[i % 8]) & 0xff for i in range(28))
    else:
        dec = bytes((ENC[i] + kseq[i % 8]) & 0xff for i in range(28))
    for tag, txt in score(dec):
        results.append(('%s/a1key/%s' % (op, tag), txt))

# ---- 8. 用可见文本做密钥流 (滑窗 XOR/SUB/ADD), 检查中文与关键词 ----
d = open('我不知道你在说什么.txt', encoding='utf-8').read()
vis = ''.join(ch for ch in d if ord(ch) < 0x2000)
for enc_name, vb in [('utf8', vis.encode('utf-8')), ('gbk', vis.encode('gbk'))]:
    for op in ('xor', 'sub', 'add'):
        for start in range(0, min(len(vb) - 28, 4000)):
            if op == 'xor':
                dec = bytes(ENC[j] ^ vb[start+j] for j in range(28))
            elif op == 'sub':
                dec = bytes((ENC[j] - vb[start+j]) & 0xff for j in range(28))
            else:
                dec = bytes((ENC[j] + vb[start+j]) & 0xff for j in range(28))
            pr = sum(1 for b in dec if 32 <= b < 127)
            if pr >= 26:
                results.append(('%s/%s/win%d/HiPrint' % (op, enc_name, start), dec.decode('latin1')))
            try:
                s = dec.decode('utf-8')
                if any(w in s for w in ('HTU', 'flag', '{')):
                    results.append(('%s/%s/win%d/kw' % (op, enc_name, start), s))
            except Exception:
                pass

# ---- 9. 哈希密钥流 XOR ----
hashes = {
    'md5(text)': hashlib.md5(open('我不知道你在说什么.txt','rb').read()).digest(),
    'md5(vis)': hashlib.md5(vis.encode('utf-8')).digest(),
    'sha1(text)': hashlib.sha1(open('我不知道你在说什么.txt','rb').read()).digest(),
    'sha256(text)': hashlib.sha256(open('我不知道你在说什么.txt','rb').read()).digest(),
    'md5(abstract)': hashlib.md5(KEYSRC).digest(),
    'sha256(abstract)': hashlib.sha256(KEYSRC).digest(),
    'sha224(abstract)': hashlib.sha224(KEYSRC).digest(),
    'sha1(abstract)': hashlib.sha1(KEYSRC).digest(),
    'blake2s(abstract)': hashlib.blake2s(KEYSRC).digest(),
}
for hn, h in hashes.items():
    for op in ('xor', 'sub', 'add'):
        if op == 'xor':
            dec = bytes(ENC[i] ^ h[i % len(h)] for i in range(28))
        elif op == 'sub':
            dec = bytes((ENC[i] - h[i % len(h)]) & 0xff for i in range(28))
        else:
            dec = bytes((ENC[i] + h[i % len(h)]) & 0xff for i in range(28))
        for tag, txt in score(dec):
            results.append(('%s/%s/%s' % (op, hn, tag), txt))

# ---- 输出 ----
seen = set()
print('=== 命中 %d 条 ===' % len(results))
for name, txt in results:
    key = (name.split('/')[0], txt[:40])
    if key in seen:
        continue
    seen.add(key)
    print('%-40s %r' % (name, txt[:60]))
