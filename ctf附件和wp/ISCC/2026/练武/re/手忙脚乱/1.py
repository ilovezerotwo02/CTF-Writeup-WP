#!/usr/bin/env python3
import struct, glob, sys
from pathlib import Path

# ------------------------------------------------------------
# 常量定义：后缀 → (标识, 字节数, 种子)
# ------------------------------------------------------------
SIGS = {
    'k6':  ('CT_K6',  6,  0x5555),  'k3':  ('CT_K3',  3,  0x6666),
    'ma':  ('CT_MASK1',24, 0x3333), 'tg':  ('CT_TARGET',24,0x1111),
    'mb':  ('CT_MASK2',24, 0x4444), 'tt':  ('CT_TARGET_T',24,0x2222),
}

# ------------------------------------------------------------
# PE 解析器
# ------------------------------------------------------------
class PeMap:
    @staticmethod
    def _u2(d,o): return struct.unpack_from('<H',d,o)[0]
    @staticmethod
    def _u4(d,o): return struct.unpack_from('<I',d,o)[0]
    @staticmethod
    def _i2(d,o): return struct.unpack_from('<h',d,o)[0]

    def __init__(self, raw):
        self.raw = raw
        self.sec, self.sp, self.sn = self._hdr()
        self.names = self._walk()

    def _hdr(self):
        p = self._u4(self.raw, 0x3C)
        assert self.raw[p:p+4] == b'PE\x00\x00'
        n  = self._u2(self.raw, p+6)
        sp = self._u4(self.raw, p+12)
        sn = self._u4(self.raw, p+16)
        os = self._u2(self.raw, p+20)
        st = p + 24 + os
        rr = []
        for i in range(n):
            o = st + i*40
            rr.append((
                self.raw[o:o+8].split(b'\x00',1)[0].decode('ascii','replace'),
                self._u4(self.raw, o+12), self._u4(self.raw, o+8),
                self._u4(self.raw, o+20), self._u4(self.raw, o+16),
            ))
        return rr, sp, sn

    def _rva(self, x):
        for _,va,vs,rp,rs in self.sec:
            if va <= x < va + max(vs, rs):
                return rp + (x - va)
        raise RuntimeError(f'unmapped 0x{x:08X}')

    def _walk(self):
        h = {}; i = 0
        while i < self.sn:
            o = self.sp + i*18
            c = self.raw[o:o+8]
            if c[:4] == b'\x00\x00\x00\x00':
                so = self._u4(c,4)
                e  = self.raw.index(b'\x00', self.sp + self.sn*18 + so)
                nm = self.raw[self.sp+self.sn*18+so:e].decode('ascii','replace')
            else:
                nm = c.rstrip(b'\x00').decode('ascii','replace')
            v  = self._u4(self.raw, o+8)
            si = self._i2(self.raw, o+12)
            ax = self.raw[o+17]
            if si > 0:
                h[nm] = self.sec[si-1][1] + v
            i += 1 + ax
        return h

    def locate(self):
        off = {}
        for tag,(pfx,_,_) in SIGS.items():
            for name,rva in self.names.items():
                if tag == 'tg' and name.endswith('CT_TARGET_T'): continue
                if name.endswith(pfx):
                    off[tag] = self._rva(rva)
                    break
        return off

# ------------------------------------------------------------
# 密码运算
# ------------------------------------------------------------
def _rr(x, n):
    n &= 7
    return ((x>>n) | ((x<<(8-n))&0xFF)) & 0xFF

def dec(data, seed):
    s = (seed ^ 0xA3B1C2D3) & 0xFFFFFFFF
    a = 0; m = 0; r = s
    out = bytearray()
    for b in data:
        x = (r + a) & 0xFFFFFFFF
        a = (a - 0x61C88647) & 0xFFFFFFFF
        r = x
        r = (((r<<13)&0xFFFFFFFF) ^ x) & 0xFFFFFFFF
        r = (r ^ (r>>17)) & 0xFFFFFFFF
        r = (r ^ ((r<<5)&0xFFFFFFFF)) & 0xFFFFFFFF
        k = (m + r*7) & 0xFFFFFFFF
        m = (m + 0x0B) & 0xFFFFFFFF
        v = b ^ (k & 0xFF)
        v = _rr(v, r>>27)
        out.append((v ^ r) & 0xFF)
    return bytes(out)

def _co(k):
    return sorted(range(len(k)), key=lambda i: (k[i], i))

def ce(d, k):
    n = len(k)
    o = _co(k)
    r = len(d)//n
    return bytes(d[rr*n+c] for c in o for rr in range(r))

def cd(d, k):
    n = len(k)
    r = len(d)//n
    o = _co(k)
    c = [b'']*n
    p = 0
    for e in o:
        c[e] = d[p:p+r]
        p += r
    return bytes(c[e][rr] for rr in range(r) for e in range(n))

def gt(key, sd):
    t = list(range(0x20, 0x7F))
    s = sd & 0xFFFFFFFF
    for c in key:
        s = (s*0x83 + c) & 0xFFFFFFFF
    for i in range(94, 0, -1):
        s = (s*0x41C64E6D + 0x3039) & 0xFFFFFFFF
        j = s % (i+1)
        t[i], t[j] = t[j], t[i]
    return bytes(t)

def revp2(ct, key):
    t0 = gt(key, 0x1234)
    t1 = gt(key, 0x8888)
    bs = [(c>>b)&1 for c in key for b in range(7,-1,-1)]
    n  = len(ct)
    ops = []
    pos = 0
    for b in bs:
        ops.append(('x', pos, b))
        pos += 1
        if pos == n:
            ops.append(('y',))
            pos = 0
    cur = bytearray(ct)
    for op in reversed(ops):
        if op[0] == 'y':
            cur = bytearray(cd(bytes(cur), key))
        else:
            _, idx, bit = op
            cur[idx] = (t1 if bit else t0).index(cur[idx]) + 0x20
    return bytes(cur)

# ------------------------------------------------------------
# 入口
# ------------------------------------------------------------
def go(fn):
    raw = Path(fn).read_bytes()
    pm = PeMap(raw)
    off = pm.locate()

    dd = {}
    for tag,(_,ln,sd) in SIGS.items():
        dd[tag] = dec(raw[off[tag]:off[tag]+ln], sd)

    k1 = ce(dd['k6'], dd['k3'])
    s1 = cd(revp2(bytes(x^y for x,y in zip(dd['tg'],dd['ma'])), dd['k6']), k1)
    s2 = cd(revp2(bytes(x^y for x,y in zip(dd['mb'],dd['tt'])), dd['k6']), k1)
    return s1.decode('latin1'), s2.decode('latin1')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        tgt = sys.argv[1]
    else:
        hit = glob.glob('attachment*.exe') or glob.glob('*.exe')
        if not hit:
            print('no exe found, drag file onto this script')
            sys.exit(1)
        tgt = hit[0]
    a,b = go(tgt)
    print('stage1:', a)
    print('flag: ISCC{' + b + '}')
