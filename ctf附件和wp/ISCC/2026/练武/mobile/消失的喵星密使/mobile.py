from io import BytesIO
from base64 import b64decode
from zipfile import ZipFile
from PIL import Image
import hashlib


APK_PATH = "iscc/附件/app-release.apk"
Q = "DDFGXVGFAVVD"
TARGET_B64 = "s1iKn8YgOi8DO4p7bWHpTldoIwNL38IWGlcBbFngHRo="
SQUARE = "mh7q1au6sl5pcv20t9zedwxfnjrgi8bk4y3o"
ROW_MAP = {"A": 0, "D": 6, "F": 12, "G": 18, "V": 24, "X": 30}
COL_MAP = {"A": 0, "D": 1, "F": 2, "G": 3, "V": 4, "X": 5}
RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36]


def extract_sbox_from_apk(apk_path: str) -> bytes:
    with ZipFile(apk_path, "r") as zf:
        png_data = zf.read("assets/hint.png")

    img = Image.open(BytesIO(png_data)).convert("RGBA")
    w, h = img.size
    pixels = list(img.getdata())

    bits = []
    for y in range(h):
        for x in range(w):
            bits.append(pixels[y * w + x][2] & 1)
            if len(bits) >= 0x830:
                break
        if len(bits) >= 0x830:
            break

    raw = bytearray(0x830 // 8)
    for i, b in enumerate(bits):
        if b:
            raw[i >> 3] |= 1 << (7 - (i & 7))

    assert raw[:4] == b"MEOW"
    return bytes(raw[4:4 + 256])


def derive_key(q: str, sbox: bytes) -> bytes:
    perm = q[1::4] + q[0::4] + q[2::4] + q[3::4]
    out = []
    for i in range(32):
        a = perm[(2 * i) % len(perm)]
        b = perm[(2 * i + 1) % len(perm)]
        ch = SQUARE[ROW_MAP[a] + COL_MAP[b]]
        out.append(sbox[ord(ch)] ^ ((0x13 * i) & 0xFF))
    return bytes(out)


def sub_word(word: bytes, sbox: bytes) -> bytes:
    return bytes(sbox[b] for b in word)


def rot_word(word: bytes) -> bytes:
    return word[1:] + word[:1]


def expand_key(key: bytes, sbox: bytes) -> list[bytes]:
    words = [key[i:i + 4] for i in range(0, 32, 4)]
    for i in range(8, 60):
        temp = words[i - 1]
        if i % 8 == 0:
            temp = bytes(
                a ^ b
                for a, b in zip(
                    sub_word(rot_word(temp), sbox),
                    bytes([RCON[i // 8 - 1], 0, 0, 0]),
                )
            )
        elif i % 8 == 4:
            temp = sub_word(temp, sbox)
        words.append(bytes(a ^ b for a, b in zip(words[i - 8], temp)))
    return [b"".join(words[4 * r:4 * r + 4]) for r in range(15)]


def add_round_key(state: list[int], key: bytes) -> list[int]:
    return [a ^ b for a, b in zip(state, key)]


def gmul(a: int, b: int) -> int:
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return p


def inv_shift_rows(state: list[int]) -> list[int]:
    rows = [state[i::4] for i in range(4)]
    out = [[0] * 4 for _ in range(4)]
    for r in range(4):
        row = list(rows[r])
        row = row[-r:] + row[:-r] if r else row
        out[r] = row
    return [out[r][c] for c in range(4) for r in range(4)]


def inv_mix_single_col(col: list[int]) -> list[int]:
    a0, a1, a2, a3 = col
    return [
        gmul(a0, 14) ^ gmul(a1, 11) ^ gmul(a2, 13) ^ gmul(a3, 9),
        gmul(a0, 9) ^ gmul(a1, 14) ^ gmul(a2, 11) ^ gmul(a3, 13),
        gmul(a0, 13) ^ gmul(a1, 9) ^ gmul(a2, 14) ^ gmul(a3, 11),
        gmul(a0, 11) ^ gmul(a1, 13) ^ gmul(a2, 9) ^ gmul(a3, 14),
    ]


def inv_mix_columns(state: list[int]) -> list[int]:
    out = []
    for c in range(4):
        out.extend(inv_mix_single_col(state[4 * c:4 * c + 4]))
    return out


def decrypt_block(block: bytes, round_keys: list[bytes], inv_sbox: list[int]) -> bytes:
    state = list(add_round_key(list(block), round_keys[14]))
    for rnd in range(13, 0, -1):
        state = inv_shift_rows(state)
        state = [inv_sbox[b] for b in state]
        state = add_round_key(state, round_keys[rnd])
        state = inv_mix_columns(state)
    state = inv_shift_rows(state)
    state = [inv_sbox[b] for b in state]
    state = add_round_key(state, round_keys[0])
    return bytes(state)


def main():
    assert hashlib.md5(Q.encode()).hexdigest() == "72184e58e765a1a579b201c3e15bc0ce"

    sbox = extract_sbox_from_apk(APK_PATH)
    inv_sbox = [0] * 256
    for i, v in enumerate(sbox):
        inv_sbox[v] = i

    key = derive_key(Q, sbox)
    round_keys = expand_key(key, sbox)

    target = bytes(b ^ 0x66 for b in b64decode(TARGET_B64))
    pt1 = decrypt_block(target[:16], round_keys, inv_sbox)
    pt2 = decrypt_block(target[16:], round_keys, inv_sbox)

    inner = (pt1 + pt2).rstrip(b"\x00").decode()
    flag = f"ISCC{{{inner}}}"

    print(f"[+] q       = {Q}")
    print(f"[+] key     = {key.hex()}")
    print(f"[+] block1  = {pt1!r}")
    print(f"[+] block2  = {pt2!r}")
    print("=" * 50)
    print(f"[!!!] FLAG: {flag}")
    print("=" * 50)


if __name__ == "__main__":
    main()