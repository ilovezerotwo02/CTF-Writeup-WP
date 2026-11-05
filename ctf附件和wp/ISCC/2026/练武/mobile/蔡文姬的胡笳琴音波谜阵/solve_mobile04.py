from pathlib import Path
import binascii
import struct
import zlib


U32 = 0xFFFFFFFF


def u32(x):
    return x & U32


def rol(x, n):
    n &= 31
    x &= U32
    return ((x << n) | (x >> (32 - n))) & U32


def ror(x, n):
    n &= 31
    x &= U32
    return ((x >> n) | (x << (32 - n))) & U32


def java_hash(s):
    h = 0
    for ch in s:
        h = u32(31 * h + ord(ch))
    return h


def z1_d(seed):
    const = bytes.fromhex("93d27d717671f07d4f415b95a883d019")
    return [u32(seed ^ x) for x in struct.unpack("<4I", const)]


def swap_adjacent_bits(data):
    return bytes((((b & 0xAA) >> 1) | ((b & 0x55) << 1)) for b in data)


def fnv1a64(data):
    h = 0xCBF29CE484222325
    for b in data:
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def tea_c(v0, v1, key):
    delta = 0x9E3779B9
    s = 0
    for _ in range(32):
        s = u32(s + delta)
        v0 = u32(v0 + (u32((v1 << 4) + key[0]) ^ u32(v1 + s) ^ u32((v1 >> 5) + key[1])))
        v1 = u32(v1 + (u32((v0 << 4) + key[2]) ^ u32(v0 + s) ^ u32((v0 >> 5) + key[3])))
    return v0, v1


def derive_cw(sequence):
    seed = java_hash("com.example.mobile04") ^ 77055908 ^ 1248521773
    key = z1_d(seed)
    h = fnv1a64(swap_adjacent_bits(sequence.encode()))
    v0 = h & U32
    v1 = (h >> 32) & U32
    a, b = tea_c(v0, v1, key)
    blob = struct.pack("<2I", a, b)
    return f"cw:{blob.hex()}:{zlib.crc32(blob) & U32:08x}"


def crc_native(data):
    return zlib.crc32(data) & U32


def decrypt_db(cw):
    db = Path("casework/app_release/apk/assets/appview_cache.db").read_bytes()
    first = db[:16]
    enc = bytearray(db[16:])
    k = crc_native(cw.encode() + first)
    for i, b in enumerate(enc):
        enc[i] = b ^ (((k >> ((i * 8) & 0x18)) + i) & 0xFF)
    return bytes(enc), k


ALPH = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(s):
    n = 0
    for ch in s.encode():
        n = n * 58 + ALPH.index(ch)
    out = n.to_bytes((n.bit_length() + 7) // 8, "big")
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + out


def rc6_schedule(seed1, seed2):
    k2 = b"@_Y%H19#$dCqg$n2"
    L = list(struct.unpack("<4I", k2))
    s0 = rol(seed2, 13) ^ seed1 ^ 0x1DCF884C
    q = u32((rol(seed2, 25) ^ seed1) | 1)
    q = u32(q + 0x6CE9DA66)
    S = [u32(s0 + i * q) for i in range(44)]
    A = B = 0
    i = j = 0
    for _ in range(132):
        A = S[i] = rol(u32(S[i] + A + B), 3)
        B = L[j] = rol(u32(L[j] + A + B), u32(A + B))
        i = (i + 1) % 44
        j = (j + 1) % 4
    return S


def rc6_decrypt_block(block, S):
    A, B, C, D = struct.unpack("<4I", block)
    C = u32(C - S[43])
    A = u32(A - S[42])
    for i in range(20, 0, -1):
        A, B, C, D = D, A, B, C
        u = rol(u32(D * u32(2 * D + 1)), 5)
        t = rol(u32(B * u32(2 * B + 1)), 5)
        C = u32(ror(u32(C - S[2 * i + 1]), t) ^ u)
        A = u32(ror(u32(A - S[2 * i]), u) ^ t)
    D = u32(D - S[1])
    B = u32(B - S[0])
    return struct.pack("<4I", A, B, C, D)


def recover_for_sequence(sequence):
    cw = derive_cw(sequence)
    dec, dbkey = decrypt_db(cw)
    seed1 = struct.unpack_from("<I", dec, 0x80)[0] if len(dec) >= 0x84 else 0
    seed2 = struct.unpack_from("<I", dec, 0xB4)[0] if len(dec) >= 0xB8 else 0
    target = b58decode("3NKxuNQp6jAbAnuEaEq17wrV567YFnzJiGbMUy8HiTDv")
    target = target[-32:].rjust(32, b"\x00")
    k1 = b"EjEoh"
    encrypted = bytes(b ^ k1[i % len(k1)] for i, b in enumerate(target))
    S = rc6_schedule(seed1, seed2)
    plain = rc6_decrypt_block(encrypted[:16], S) + rc6_decrypt_block(encrypted[16:], S)
    return cw, dbkey, seed1, seed2, plain, dec[:64]


if __name__ == "__main__":
    notes = {
        "C": "CWJ",
        "D": "XMAS",
        "E": "FLOW",
        "F": "STAR",
        "G": "ROSE",
        "A": "GOAL",
        "B": "DANCE",
        "c": "MAGI",
    }
    candidates = {
        "twinkle_1": "CCGGAAGFFEEDDC",
        "twinkle_full": "CCGGAAGFFEEDDCCGGFFEEDDGGFFEEDDCCGGAAGFFEEDDC",
        "scale": "CDEFGABc",
    }
    for name, melody in candidates.items():
        seq = "".join(notes[n] for n in melody)
        cw, dbkey, s1, s2, plain, head = recover_for_sequence(seq)
        print(name, melody)
        print(" seq_len", len(seq), "cw", cw, "dbkey", f"{dbkey:08x}", "seeds", f"{s1:08x}", f"{s2:08x}")
        print(" plain", plain, plain.hex())
        print(" head", head[:32].hex())
        try:
            print(" flag", "ISCC{" + plain.decode("ascii") + "}")
        except UnicodeDecodeError:
            pass
        print()
