import hashlib, json, struct, itertools, sys
sys.path.insert(0, '.')
from protocol_spec import digest, Q, G, verify

rows = json.load(open('transcript.json', encoding='utf-8'))
blob = open('sealed.bin', 'rb').read()
calib = open('calibration.bin', 'rb').read()

magic = blob[:4]; mode_b = blob[4]
nonce = blob[5:13]; ctlen = struct.unpack('<H', blob[13:15])[0]
ct = blob[15:15 + ctlen]; tag = blob[15 + ctlen:]
print('magic', magic, 'mode', mode_b, 'nonce', nonce.hex(), 'ctlen', ctlen, 'tag', tag.hex())

# --- 1. recover x for each candidate mode ---
def x_from(row, mode):
    h = digest(mode, bytes.fromhex(row['msg']), row['nonce'], row['sid'])
    k = row['r'] * pow(G, -1, Q) % Q
    return (row['s'] * k - h) * pow(row['r'], -1, Q) % Q

best = None
for mode in (0, 1, 2):
    xs = [x_from(r, mode) for r in rows]
    counts = {}
    for x in xs:
        counts[x] = counts.get(x, 0) + 1
    x, c = max(counts.items(), key=lambda t: t[1])
    print(f'mode {mode}: 一致行数 {c}/{len(rows)}')
    if best is None or c > best[1]:
        best = (x, c, mode)

x, c, dmode = best
print('选定 x =', x, 'mode =', dmode, '一致', c)
viol = [i for i, r in enumerate(rows) if not verify(r, x, dmode)]
print('不满足的行 index:', viol)

# --- 2. derive key, try transcript byte variants ---
def variants():
    raw = open('transcript.json', 'rb').read()
    yield 'raw-file', raw
    yield 'compact', json.dumps(rows, separators=(',', ':'), ensure_ascii=False).encode()
    yield 'default', json.dumps(rows, ensure_ascii=False).encode()
    yield 'compact-ascii', json.dumps(rows, separators=(',', ':')).encode()
    yield 'sorted-raw', json.dumps(sorted(rows, key=lambda r: r['sid'])).encode()
    # file with trailing newline stripped/added
    yield 'raw-strip', raw.strip()

def gen_stream(key, nonce8, nbytes):
    out = bytearray()
    c = 0
    while len(out) < nbytes:
        d = hashlib.blake2s(b'ARX-8/1' + key + nonce8 + struct.pack('<I', c), digest_size=32).digest()
        u = list(struct.unpack('<8I', d))
        for rnd in range(8):
            for lane, i in enumerate((0, 2, 4, 6)):
                a = u[i]; b = u[i + 1]
                cst = (0x9E3779B9 + rnd * 0x7F4A7C15 + lane * 0x6A09E667) & 0xffffffff
                u[i] = (a + b + (((b << 7) | (b >> 25)) & 0xffffffff)) & 0xffffffff
                u[i + 1] = (b ^ (((u[i] << 11) | (u[i] >> 21)) & 0xffffffff) ^ cst) & 0xffffffff
            u = u[1:] + u[:1]
        out += struct.pack('<8I', *u)
        c += 1
    return bytes(out[:nbytes])

hdr_variants = {
    'magic..ctlen': blob[:15],
    'magic+mode': blob[:5],
    'all-but-tag': blob[:15 + ctlen],
}

for tname, tb in variants():
    th = hashlib.sha256(tb).digest()
    for hname, hdr in hdr_variants.items():
        key = hashlib.blake2s(b'BEACON/SEAL\x02' + struct.pack('<I', x) + bytes([dmode]) + th + calib[16:24], digest_size=32).digest()
        t = hashlib.blake2s(key + hdr + ct, digest_size=16).digest()
        if t == tag:
            print(f'*** 命中: transcript={tname} header={hname}')
            ks = gen_stream(key, nonce, len(ct))
            pt = bytes(a ^ b for a, b in zip(ct, ks))
            print('plaintext:', pt)
            open('flag.txt', 'wb').write(pt)
            raise SystemExit
print('未命中，需要继续调参')
