
MASK = (1 << 64) - 1
M1 = 0xBF58476D1CE4E5B9
M2 = 0x94D049BB133111EB
GOLDEN = 0x9E3779B97F4A7C15

CIPHER = bytes.fromhex(
    "add2af6a65a3a80f20457b8c5a76a27a"
    "b63c5011cf4ec16940dcb8268b5f4bb3"
    "b7e4cd92"
)


def splitmix_final(x: int) -> int:
    x &= MASK
    x = (x ^ (x >> 30)) & MASK
    x = (x * M1) & MASK
    x = (x ^ (x >> 27)) & MASK
    x = (x * M2) & MASK
    x = (x ^ (x >> 31)) & MASK
    return x


def invert_xor_shift(y: int, s: int) -> int:
    result = 0
    for i in range(63, -1, -1):
        bit = (y >> i) & 1
        if i + s < 64:
            bit ^= (result >> (i + s)) & 1
        result |= bit << i
    return result & MASK


def inv_splitmix(z: int) -> int:
    z = invert_xor_shift(z, 31)
    z = (z * pow(M2, -1, 1 << 64)) & MASK
    z = invert_xor_shift(z, 27)
    z = (z * pow(M1, -1, 1 << 64)) & MASK
    z = invert_xor_shift(z, 30)
    return z


def decrypt_with_r10(cipher: bytes, r10: int) -> bytes:
    out = bytearray(len(cipher))
    for i in range(len(cipher)):
        blk = i >> 3
        z = splitmix_final((blk * GOLDEN + r10) & MASK)
        out[i] = cipher[i] ^ ((z >> ((i & 7) * 8)) & 0xFF)
    return bytes(out)


def main() -> None:
    for t in (0, 1, 0x123456789ABCDEF0, 0xDEADBEEFCAFEBABE):
        assert inv_splitmix(splitmix_final(t)) == t

    # 真 flag 使用全角括号（与 8 条 decoy 一致）
    known = "HTUCTF｛".encode()  # 9 bytes: 48 54 55 43 54 46 EF BD 9B
    ks = bytes(c ^ p for c, p in zip(CIPHER[:8], known[:8]))
    z0 = int.from_bytes(ks, "little")
    r10 = inv_splitmix(z0)
    pt = decrypt_with_r10(CIPHER, r10)
    flag = pt.decode("utf-8")
    assert flag.startswith("HTUCTF｛") and flag.endswith("｝")
    print(flag)
    print("r10 =", hex(r10))


if __name__ == "__main__":
    main()
