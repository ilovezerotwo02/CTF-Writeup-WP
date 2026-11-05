

MASK = 0xffffffff


def decode_byte(b):
    """Decode .rodata constants: reverse of the simple XOR+SUB encoding"""
    return (((b - 0x13) & 0xff) ^ 0x5a) & 0xff


def gf(a, b):
    """GF(2^8) multiplication with AES irreducible poly 0x1b"""
    a &= 0xff
    b &= 0xff
    res = 0
    while b:
        if b & 1:
            res ^= a
        hi = a & 0x80
        a = (a << 1) & 0xff
        if hi:
            a ^= 0x1b
        b >>= 1
    return res


def f1(a, b):
    """C1 XOR C3, then rotate left by 3 bytes"""
    d = bytearray(a)
    for i in range(min(len(a), len(b), 16)):
        d[i] ^= b[i]
    return bytes(d[3:] + d[:3])


def f2(src1, src2):
    """
    4x4 GF(2^8) matrix multiplication
    src2 acts as the matrix (row-major), src1 as the operand
    Final row permutation: [2, 3, 0, 1]
    """
    tmp = [0] * 16
    for row in range(4):
        for col in range(4):
            v = src2[row * 4 + col]
            for k in range(4):
                tmp[row * 4 + k] ^= gf(v, src1[col * 4 + k])
    order = [2, 3, 0, 1]
    out = []
    for r in order:
        out += tmp[r * 4:r * 4 + 4]
    return bytes(out)


AES_SBOX = bytes.fromhex(
    "637c777bf26b6fc53001672bfed7ab76ca82c97dfa5947f0add4a2af9ca472c0"
    "b7fd9326363ff7cc34a5e5f171d8311504c723c31896059a071280e2eb27b275"
    "09832c1a1b6e5aa0523bd6b329e32f8453d100ed20fcb15b6acbbe394a4c58cf"
    "d0efaafb434d338545f9027f503c9fa851a3408f929d38f5bcb6da2110fff3d2"
    "cd0c13ec5f974417c4a77e3d645d197360814fdc222a908846eeb814de5e0bdb"
    "e0323a0a4906245cc2d3ac629195e479e7c8376d8dd54ea96c56f4ea657aae08"
    "ba78252e1ca6b4c6e8dd741f4bbd8b8a703eb5664803f60e613557b986c11d9e"
    "e1f8981169d98e949b1e87e9ce5528df8ca1890dbfe6426841992d0fb054bb16"
)


def f3(a, b, c):
    """XOR three inputs, apply AES S-box, then prefix XOR"""
    out = bytearray(16)
    for i in range(16):
        out[i] = AES_SBOX[a[i] ^ b[i] ^ c[i]]
    for i in range(1, 16):
        out[i] ^= out[i - 1]
    return bytes(out)


def tea_decrypt(v0, v1, k, rounds=16):
    """TEA decryption with 16 rounds"""
    delta = 0x9e3779b9
    s = (delta * rounds) & MASK
    for _ in range(rounds):
        v1 = (v1 - ((((v0 << 4) & MASK) + k[2])
               ^ ((v0 + s) & MASK)
               ^ (((v0 >> 5) + k[3]) & MASK))) & MASK
        v0 = (v0 - ((((v1 << 4) & MASK) + k[0])
               ^ ((v1 + s) & MASK)
               ^ (((v1 >> 5) + k[1]) & MASK))) & MASK
        s = (s - delta) & MASK
    return v0, v1


def gf_inv(a):
    """GF(2^8) multiplicative inverse"""
    if a == 0:
        raise ZeroDivisionError
    for x in range(1, 256):
        if gf(a, x) == 1:
            return x
    raise ValueError("no inverse")


def invert_mat4(M):
    """Invert a 4x4 matrix in GF(2^8) using Gauss-Jordan elimination"""
    A = [[M[r * 4 + c] for c in range(4)] for r in range(4)]
    inv = [[1 if i == j else 0 for j in range(4)] for i in range(4)]

    for col in range(4):
        pivot = None
        for r in range(col, 4):
            if A[r][col]:
                pivot = r
                break
        if pivot is None:
            raise ValueError("singular matrix")
        if pivot != col:
            A[col], A[pivot] = A[pivot], A[col]
            inv[col], inv[pivot] = inv[pivot], inv[col]

        inv_pivot = gf_inv(A[col][col])
        for j in range(4):
            A[col][j] = gf(A[col][j], inv_pivot)
            inv[col][j] = gf(inv[col][j], inv_pivot)

        for r in range(4):
            if r == col:
                continue
            factor = A[r][col]
            if factor:
                for j in range(4):
                    A[r][j] ^= gf(factor, A[col][j])
                    inv[r][j] ^= gf(factor, inv[col][j])

    return inv


def inv_f4(cipher, matrix):
    """
    Reverse of f4: given output Y and matrix M, find X where Y = M * X
    Each row: y_row = matrix * x_row (all in GF(2^8))
    """
    inv = invert_mat4(matrix)
    out = bytearray()
    for row in range(3):
        y = cipher[row * 4:row * 4 + 4]
        x = []
        for i in range(4):
            acc = 0
            for j in range(4):
                acc ^= gf(inv[i][j], y[j])
            x.append(acc)
        out += bytes(x)
    return bytes(out)


def prng(n, seed):
    """LCG-based PRNG: generates n bytes of pseudo-random stream"""
    state = seed & ((1 << 64) - 1)
    A = 0x5851f42d4c957f2d
    C = 0x14057b7ef767814f
    out = []
    for _ in range(n):
        state = (A * state + C) & ((1 << 64) - 1)
        out.append((state >> 24) & 0xff)
    return bytes(out)


# ============================================================
# MAIN SOLVE
# ============================================================

# Read cipher files from assets
import pathlib
ASSETS = pathlib.Path("D:/桌面/wp/mobile/密码验证/resources/assets")

cipher1 = (ASSETS / "cipher1.bin").read_bytes()
cipher2 = (ASSETS / "cipher2.bin").read_bytes()
cipher3 = (ASSETS / "cipher3.bin").read_bytes()
puzzle = (ASSETS / "puzzle.bin").read_bytes()

print("=== Cipher files ===")
print(f"cipher1 ({len(cipher1)} bytes): {cipher1.hex()}")
print(f"cipher2 ({len(cipher2)} bytes): {cipher2.hex()}")
print(f"cipher3 ({len(cipher3)} bytes): {cipher3.hex()}")
print(f"puzzle  ({len(puzzle)} bytes): {puzzle.hex()}")

# Step 1: Constants from .rodata (encoded, then decoded)
raw_C1 = bytes.fromhex("5384792a17483deedb0c01b29fd0b566")
raw_C2 = bytes.fromhex("6e6d6d6d6d6e6d6d6d6d6e6d6d6d6d6e")
raw_C3 = bytes.fromhex("03f4a99a5e8b7c31224f40e5d66db7ca")

C1 = bytes(decode_byte(b) for b in raw_C1)
C2 = bytes(decode_byte(b) for b in raw_C2)
C3 = bytes(decode_byte(b) for b in raw_C3)

print(f"\n=== Decoded Constants ===")
print(f"C1 = {C1.hex()}")
print(f"C2 = {C2.hex()}")
print(f"C3 = {C3.hex()}")

# Step 2: Compute intermediate values
v128 = f1(C1, C3)
v140 = f2(v128, C2)
v158 = f3(v128, v140, C3)

print(f"\n=== Intermediate Values ===")
print(f"v128 (TEA key material) = {v128.hex()}")
print(f"v140 (GF matrix)        = {v140.hex()}")
print(f"v158 (AES-SBOX hash)    = {v158.hex()}")

# Step 3: Solve p1 (TEA decryption + XOR with v158 rotation)
key = [int.from_bytes(v128[i * 4:(i + 1) * 4], "big") for i in range(4)]

ct0 = int.from_bytes(cipher1[:4], "big")
ct1 = int.from_bytes(cipher1[4:], "big")
pt0, pt1 = tea_decrypt(ct0, ct1, key)

x = pt0.to_bytes(4, "big") + pt1.to_bytes(4, "big")
rot = bytes(v158[(i + 1) % 16] for i in range(8))
p1 = bytes(a ^ b for a, b in zip(x, rot))
print(f"\np1 (TEA decrypt + XOR) = {p1}")

# Step 4: Solve p2 (GF(2^8) matrix inversion)
p2 = inv_f4(cipher2, v140)
print(f"p2 (GF matrix solve)   = {p2}")

# Step 5: Solve p3 (LCG PRNG stream XOR)
seed = int.from_bytes(v158[:8], "big")
ks = prng(len(cipher3), seed)
p3 = bytes(a ^ b for a, b in zip(cipher3, ks))
print(f"p3 (LCG stream XOR)    = {p3}")

# Step 6: Construct flag
flag = b"ISCC{" + p1 + p2 + p3 + b"}"
print(f"\n=== FLAG ===")
print(f"ISCC{{{p1.decode()}{p2.decode()}{p3.decode()}}}")
print(f"flag = {flag.decode()}")

# Verify lengths
assert len(p1) == 8
assert len(p2) == 12
assert len(p3) == 10
assert len(flag) == 5 + 30 + 1  # ISCC{ + 30 chars + }

# Cross-constraint check: hash_pair(p1+p2)
def hash_pair(data):
    x = 0
    s = 0
    for b in data:
        x ^= b
        s = (s + b) & 0xff
    return x, s

hx, hs = hash_pair(p1 + p2)
print(f"\nhash_pair(p1+p2) = (0x{hx:02x}, 0x{hs:02x})")
print(f"p3[-2:] = {p3[-2:]} (0x{p3[-2]:02x}, 0x{p3[-1]:02x})")
