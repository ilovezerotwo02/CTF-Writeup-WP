# -*- coding: utf-8 -*-
"""42 - 第五轮: 修正后的文本密钥流全量滑窗搜索"""
ENC = bytes.fromhex('f8eaf9fafa9df9ebced6ee9df3d6cfc3e6f8fdcae59eccc4d9c6f1ca')

d = open('我不知道你在说什么.txt', encoding='utf-8').read()
ZW = set('\u200c\u200d\u202c\ufeff')
vis = ''.join(ch for ch in d if ch not in ZW)

streams = {
    'utf8': vis.encode('utf-8'),
    'gbk': vis.encode('gbk'),
    'cp-low': bytes(ord(c) & 0xff for c in vis),
    'cp-hi': bytes((ord(c) >> 8) & 0xff for c in vis),
}

hits = 0
for sname, sb in streams.items():
    n = len(sb)
    for opname in ('xor', 'sub', 'add'):
        for start in range(0, n - 28):
            w = sb[start:start+28]
            if opname == 'xor':
                pt = bytes(ENC[i] ^ w[i] for i in range(28))
            elif opname == 'sub':
                pt = bytes((ENC[i] - w[i]) & 0xff for i in range(28))
            else:
                pt = bytes((ENC[i] + w[i]) & 0xff for i in range(28))
            pr = sum(1 for b in pt if 32 <= b < 127)
            tag = None
            if pr >= 27:
                tag = pt.decode('latin1')
            elif pt[:1] in (b'H', b'f') or b'HTU' in pt or b'flag' in pt:
                tag = ''.join(chr(b) if 32 <= b < 127 else '.' for b in pt)
            else:
                try:
                    t = pt.decode('utf-8')
                    if sum(1 for c in t if '\u4e00' <= c <= '\u9fff') >= 6:
                        tag = 'UTF8:' + t
                except Exception:
                    pass
                if tag is None:
                    try:
                        t = pt.decode('gbk')
                        if sum(1 for c in t if '\u4e00' <= c <= '\u9fff') >= 8:
                            tag = 'GBK:' + t
                    except Exception:
                        pass
            if tag:
                hits += 1
                print('%s/%s/win%d -> %r' % (sname, opname, start, tag))
                if hits > 30:
                    raise SystemExit
print('done, hits =', hits)
