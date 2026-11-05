import struct
import zlib

M32 = 0xFFFFFFFF

def clamp(x):
    return x & M32

def rotl(val, r):
    val &= M32
    r &= 31
    if r == 0:
        return val
    return ((val << r) | (val >> (32 - r))) & M32

def rotr(val, r):
    val &= M32
    r &= 31
    if r == 0:
        return val
    return ((val >> r) | (val << (32 - r))) & M32

def bitflip(data):
    out = []
    for b in data:
        lo = (b & 0x55) << 1
        hi = (b & 0xAA) >> 1
        out.append((lo | hi) & 0xFF)
    return bytes(out)

def fnv1a_64(buf):
    h = 0xCBF29CE484222325
    for byte in buf:
        h ^= byte
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h

def tea_rounds(v0, v1, k4):
    delta = 0x9E3779B9
    s = 0
    for _ in range(32):
        s = clamp(s + delta)
        term0 = ((v1 << 4) & M32) + k4[0]
        term1 = v1 + s
        term2 = (v1 >> 5) + k4[1]
        v0 = clamp(v0 + (clamp(term0 ^ term1 ^ term2)))
        term0 = ((v0 << 4) & M32) + k4[2]
        term1 = v0 + s
        term2 = (v0 >> 5) + k4[3]
        v1 = clamp(v1 + (clamp(term0 ^ term1 ^ term2)))
    return v0, v1

def jhash(s):
    h = 0
    for ch in s:
        h = clamp(h * 31 + ord(ch))
    return h

def build_tag(seq):
    video_size = 77055908
    magic_mask = 0x7D9D119A
    seed = jhash("com.example.mobile04") ^ video_size ^ magic_mask
    deriv = [0xE8C5FA02, 0x218D0108, 0x79EC04B9, 0xCD353AB8]
    k = [clamp(seed ^ d) for d in deriv]
    fp = fnv1a_64(bitflip(seq.encode()))
    lo = fp & M32
    hi = (fp >> 32) & M32
    a, b = tea_rounds(lo, hi, k)
    blob = struct.pack("<II", a, b)
    return "cw:{:s}:{:08x}".format(blob.hex(), zlib.crc32(blob) & M32)

def debase58(s):
    alpha = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = 0
    for ch in s:
        n = n * 58 + alpha.index(ch)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    pad_cnt = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad_cnt + raw

def rc6_expand(seed1, seed2, k2, px, qa):
    P = clamp(rotl(seed2, 13) ^ seed1 ^ px)
    Q = clamp(rotl(seed2, 25) ^ seed1)
    Q = clamp((Q | 1) + qa)
    L = list(struct.unpack("<4I", k2))
    S = [0] * 44
    S[0] = P
    for i in range(1, 44):
        S[i] = clamp(S[i - 1] + Q)
    A = B = i = j = 0
    for _ in range(132):
        A = S[i] = rotl(clamp(S[i] + A + B), 3)
        B = L[j] = rotl(clamp(L[j] + A + B), clamp(A + B) & 31)
        i = (i + 1) % 44
        j = (j + 1) % 4
    return S

def rc6_block(blk, S):
    w, x, y, z = struct.unpack("<4I", blk)
    y = clamp(y - S[43])
    w = clamp(w - S[42])
    for r in range(20, 0, -1):
        w, x, y, z = z, w, x, y
        u = rotl(clamp(z * clamp(2 * z + 1)), 5)
        t = rotl(clamp(x * clamp(2 * x + 1)), 5)
        y = rotr(clamp(y - S[2 * r + 1]), t & 31) ^ u
        w = rotr(clamp(w - S[2 * r]), u & 31) ^ t
    z = clamp(z - S[1])
    x = clamp(x - S[0])
    return struct.pack("<4I", w, x, y, z)

def main():
    seq = "CWJXMASFLOWSTARROSEGOALDANCEMAGI"
    tag = build_tag(seq)
    print("[+] tag =", tag)
    assert tag == "cw:b659bb46e86375f7:4c8314d0"

    s1 = 0xA2AA216A
    s2 = 0x5B74C718

    K2 = b"Vmy0s5bla5&kzFpf"
    K1 = b"WIrQW"
    TGT = "2dAvRgJZsh1EiQ5DtrJiaLL9gp81z71ZMFGecH3BN3F2"

    cipher = debase58(TGT)
    cipher = bytes(cipher[i] ^ K1[i % len(K1)] for i in range(len(cipher)))

    S = rc6_expand(s1, s2, K2, 0xE73C49EA, 0x7F9880A6)
    body = rc6_block(cipher[:16], S) + rc6_block(cipher[16:], S)
    print("[+] body =", body.decode())
    print("[+] flag = ISCC{" + body.decode() + "}")

if __name__ == "__main__":
    main()
