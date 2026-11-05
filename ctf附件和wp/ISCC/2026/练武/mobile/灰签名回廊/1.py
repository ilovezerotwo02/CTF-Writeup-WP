#!/usr/bin/env python3
import hashlib, itertools, multiprocessing, re, struct, sys, zipfile
from pathlib import Path

def rol64(x, b):
    x &= 0xffffffffffffffff
    return ((x << b) & 0xffffffffffffffff) | (x >> (64 - b))

def compute_chain(part, seed, data):
    prime = 0x100000001B3
    v = (seed ^ ((part * prime) & 0xffffffffffffffff)) & 0xffffffffffffffff
    for bb in data:
        v = rol64(((v ^ bb) * prime) & 0xffffffffffffffff, 13)
    v = (v ^ (v >> 33)) & 0xffffffffffffffff
    v = (v * 0xFF51AFD7ED558CCD) & 0xffffffffffffffff
    v = (v ^ (v >> 33)) & 0xffffffffffffffff
    return v

def rc4_stream(key, n):
    s = list(range(256)); j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) & 0xff
        s[i], s[j] = s[j], s[i]
    i = j = 0; out = []
    for _ in range(n):
        i = (i + 1) & 0xff; j = (j + s[i]) & 0xff
        s[i], s[j] = s[j], s[i]
        out.append(s[(s[i] + s[j]) & 0xff])
    return bytes(out)

def read_u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]

def read_u64(buf, off):
    return struct.unpack_from("<Q", buf, off)[0]

def read_lv(buf, off):
    size = read_u32(buf, off)
    off += 4
    return buf[off:off + size], off + size

def extract_v2_cert_sha256(apk_data):
    eocd = apk_data.rfind(b"PK\x05\x06")
    if eocd < 0: raise ValueError("EOCD not found")
    central_dir_off = read_u32(apk_data, eocd + 16)
    if apk_data[central_dir_off - 16:central_dir_off] != b"APK Sig Block 42":
        raise ValueError("APK Signing Block没有找到")
    size2 = read_u64(apk_data, central_dir_off - 24)
    block_start = central_dir_off - size2 - 8
    off = block_start + 8
    end = central_dir_off - 24
    v2_block = None
    while off < end:
        pair_size = read_u64(apk_data, off)
        off += 8
        pair_id = read_u32(apk_data, off)
        off += 4
        value = apk_data[off:off + pair_size - 4]
        off += pair_size - 4
        if pair_id == 0x7109871A:
            v2_block = value; break
    if v2_block is None: raise ValueError("APKv2签名block没有找到")
    signers, _ = read_lv(v2_block, 0)
    signer, _ = read_lv(signers, 0)
    signed_data, off = read_lv(signer, 0)
    _digests, off = read_lv(signed_data, 0)
    certs, off = read_lv(signed_data, off)
    cert, _ = read_lv(certs, 0)
    return hashlib.sha256(cert).digest()

def extract_target_hash(apk_path):
    with zipfile.ZipFile(apk_path) as z:
        for name in z.namelist():
            if name.endswith(".dex"):
                for m in re.findall(rb"[0-9a-f]{64}", z.read(name)):
                    h = m.decode()
                    if h != "0" * 64: return h
    return None

WD = None
def init_wd(*a): global WD; WD = a

def worker(fc):
    prefix, target, charset, ks = WD
    base = hashlib.sha256(); base.update(prefix)
    s0 = ord("_")
    for c2 in charset:
        for c3 in charset:
            sf = bytes([s0, ord(fc), ord(c2), ord(c3)])
            d0, d1, d2, d3 = [sf[i] ^ ks[i] for i in range(4)]
            v = (((d2 ^ (d1 << 3) ^ (d0 << 6)) << 12) ^ (d3 << 9)) & 0x3ff0000
            if v != 0x1a00000: continue
            st = base.copy(); st.update(sf)
            for t in itertools.product(charset, repeat=3):
                h = st.copy(); h.update("".join(t).encode() + b"}")
                if h.hexdigest() == target: return (prefix + sf + "".join(t).encode() + b"}").decode()
    return None

def solve(apk_path):
    import sys
    sig = extract_v2_cert_sha256(Path(apk_path).read_bytes())
    target = extract_target_hash(apk_path)
    print(f"sig_哈希 = {sig.hex()}", file=sys.stderr)
    print(f"目标 = {target}", file=sys.stderr)
    fill = bytes([100, 111, 65, 94, 127, 75, 52])
    p1 = bytes(((b ^ 7) - 1) & 0xff for b in fill)
    np1 = bytes(fill[i] ^ sig[i % 4] for i in range(7))
    f2 = bytes([109^23, 65^23, 125^23, 78^23])
    f3 = bytes([0^23^90, 1^33^90, 2^45^90, 3^32^90])
    f4 = b"FK"
    p2 = bytes([f2[0]^0x25, f2[1]^0x15, f2[2]^0x58, f2[3]^0x31, f2[0]^0x29])
    p3 = bytes([(0x93-f3[0])&0xff^0x19, (0xE2-f3[1])&0xff^0x19,
                (0xE9-f3[2])&0xff^0x19, (0xC2-f3[3])&0xff^0x19,
                (0xCC-f3[0])&0xff^0x19])
    prefix = b"ISCC{" + p1 + p2 + p3
    print(f"prefix = {prefix}", file=sys.stderr)
    chain = compute_chain(3, compute_chain(2, compute_chain(1, 1597463007, np1), f2), f3)
    low = chain & 0xffffffff
    key = bytearray(14)
    for i, ch in enumerate(b"Secu"): key[i] = ((low >> (8*i)) & 0xff) ^ ch
    key[4:8] = f2; key[8:12] = f3
    key[12] = f4[0] ^ 0x46; key[13] = f4[1] ^ 0x4b
    ks = rc4_stream(bytes(key), 4)
    print(f"链 = {hex(chain)}", file=sys.stderr)
    print(f"ks = {ks.hex()}", file=sys.stderr)
    charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    with multiprocessing.Pool(initializer=init_wd,
            initargs=(prefix, target, charset, ks)) as pool:
        for r in pool.imap_unordered(worker, charset, 1):
            if r: pool.terminate(); return r

if __name__ == "__main__":
    import os
    path = sys.argv[1] if len(sys.argv) > 1 else "attachment-68.apk"
    if not os.path.exists(path):
        path = "attachment.apk"
    if not os.path.exists(path):
        for f in os.listdir("."):
            if f.endswith(".apk"):
                path = f; break
    print(solve(path))
