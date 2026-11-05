from collections import defaultdict
from itertools import product
from pathlib import Path
import sys


SBOX = [
    0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
    0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
    0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
    0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
    0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
    0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
    0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
    0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
    0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
    0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
    0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
    0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
    0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
    0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
    0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
    0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16,
]

INV_SBOX = [0] * 256
for i, x in enumerate(SBOX):
    INV_SBOX[x] = i

RCON = [0, 1, 2, 4, 8, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36]


def xtime(value: int) -> int:
    value <<= 1
    if value & 0x100:
        value ^= 0x11B
    return value & 0xFF


def gmul(a: int, b: int) -> int:
    result = 0
    while b:
        if b & 1:
            result ^= a
        a = xtime(a)
        b >>= 1
    return result


def xor_word(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def rot_word(word: bytes) -> bytes:
    return word[1:] + word[:1]


def sub_word(word: bytes) -> bytes:
    return bytes(SBOX[x] for x in word)


def add_round_key(state: list[int], round_key: bytes) -> list[int]:
    return [x ^ y for x, y in zip(state, round_key)]


def inv_shift_rows(state: list[int]) -> list[int]:
    out = [0] * 16
    for row in range(4):
        for col in range(4):
            out[4 * col + row] = state[4 * ((col - row) % 4) + row]
    return out


def inv_sub_bytes(state: list[int]) -> list[int]:
    return [INV_SBOX[x] for x in state]


def inv_mix_columns(state: list[int]) -> list[int]:
    out = [0] * 16
    for col in range(4):
        a = state[4 * col : 4 * col + 4]
        out[4 * col + 0] = gmul(14, a[0]) ^ gmul(11, a[1]) ^ gmul(13, a[2]) ^ gmul(9, a[3])
        out[4 * col + 1] = gmul(9, a[0]) ^ gmul(14, a[1]) ^ gmul(11, a[2]) ^ gmul(13, a[3])
        out[4 * col + 2] = gmul(13, a[0]) ^ gmul(9, a[1]) ^ gmul(14, a[2]) ^ gmul(11, a[3])
        out[4 * col + 3] = gmul(11, a[0]) ^ gmul(13, a[1]) ^ gmul(9, a[2]) ^ gmul(14, a[3])
    return out


def expand_key(master_key: bytes) -> list[bytes]:
    words = [master_key[i : i + 4] for i in range(0, 16, 4)]
    for i in range(4, 44):
        temp = words[i - 1]
        if i % 4 == 0:
            temp = bytearray(sub_word(rot_word(temp)))
            temp[0] ^= RCON[i // 4]
            temp = bytes(temp)
        words.append(xor_word(words[i - 4], temp))
    return [b"".join(words[4 * r : 4 * r + 4]) for r in range(11)]


def invert_round10_key(round10_key: bytes) -> bytes:
    words = [None] * 44
    for i in range(4):
        words[40 + i] = round10_key[4 * i : 4 * i + 4]

    for i in range(43, 3, -1):
        temp = words[i - 1]
        if i % 4 == 0:
            temp = bytearray(sub_word(rot_word(temp)))
            temp[0] ^= RCON[i // 4]
            temp = bytes(temp)
        words[i - 4] = xor_word(words[i], temp)
    return b"".join(words[:4])


def aes_decrypt_block(ciphertext: bytes, master_key: bytes) -> bytes:
    round_keys = expand_key(master_key)
    state = list(ciphertext)
    state = add_round_key(state, round_keys[10])
    for round_index in range(9, 0, -1):
        state = inv_shift_rows(state)
        state = inv_sub_bytes(state)
        state = add_round_key(state, round_keys[round_index])
        state = inv_mix_columns(state)
    state = inv_shift_rows(state)
    state = inv_sub_bytes(state)
    state = add_round_key(state, round_keys[0])
    return bytes(state)


def pair_key_diff_map(correct_byte: int, faulty_byte: int) -> dict[int, list[int]]:
    mapping = defaultdict(list)
    for key_guess in range(256):
        delta = INV_SBOX[correct_byte ^ key_guess] ^ INV_SBOX[faulty_byte ^ key_guess]
        mapping[delta].append(key_guess)
    return mapping


def build_fault_patterns() -> list[tuple[int, int, int, int]]:
    patterns = []
    for e in range(1, 256):
        patterns.extend(
            [
                (gmul(2, e), e, e, gmul(3, e)),
                (gmul(3, e), gmul(2, e), e, e),
                (e, gmul(3, e), gmul(2, e), e),
                (e, e, gmul(3, e), gmul(2, e)),
            ]
        )
    return list(dict.fromkeys(patterns))


def collect_useful_faults(correct: bytes, blocks: list[bytes], column_positions: dict[int, list[int]]) -> dict[int, list[tuple[int, bytes]]]:
    useful = {i: [] for i in range(4)}
    for block_index, faulty in enumerate(blocks[1:], 1):
        diff_positions = [i for i, (a, b) in enumerate(zip(correct, faulty)) if a != b]
        if len(diff_positions) != 4:
            continue
        for column, positions in column_positions.items():
            if sorted(diff_positions) == sorted(positions):
                useful[column].append((block_index, faulty))
                break
    return useful


def recover_last_round_key(blocks: list[bytes]) -> bytes:
    correct = blocks[0]

    # 这里的顺序不是升序，而是“最后一轮 ShiftRows 之前”的行序。
    # 这样后面套 MixColumns 故障模式时，字节顺序正好对齐。
    column_positions = {
        0: [0, 13, 10, 7],
        1: [4, 1, 14, 11],
        2: [8, 5, 2, 15],
        3: [12, 9, 6, 3],
    }

    fault_patterns = build_fault_patterns()
    useful_faults = collect_useful_faults(correct, blocks, column_positions)

    print("[+] useful single-byte fault groups:")
    for column in range(4):
        print(f"    column {column}: {[index for index, _ in useful_faults[column]]}")

    round10_key = [None] * 16
    for column, faults in useful_faults.items():
        if len(faults) < 2:
            raise RuntimeError(f"not enough usable faults for column {column}")

        positions = column_positions[column]
        candidates = None
        for _, faulty in faults:
            diff_maps = [pair_key_diff_map(correct[pos], faulty[pos]) for pos in positions]
            current = set()

            for pattern in fault_patterns:
                choice_lists = [diff_maps[i].get(pattern[i], []) for i in range(4)]
                if all(choice_lists):
                    current.update(product(*choice_lists))

            candidates = current if candidates is None else candidates & current

        if not candidates or len(candidates) != 1:
            raise RuntimeError(f"ambiguous candidates for column {column}: {0 if not candidates else len(candidates)}")

        column_key_bytes = next(iter(candidates))
        for pos, key_byte in zip(positions, column_key_bytes):
            round10_key[pos] = key_byte

    return bytes(round10_key)


def solve(path: Path) -> None:
    data = path.read_bytes()
    if len(data) % 16 != 0:
        raise SystemExit("input length is not a multiple of 16")

    blocks = [data[i : i + 16] for i in range(0, len(data), 16)]
    print("[+] blocks:", len(blocks))
    print("[+] correct ciphertext:", blocks[0].hex())

    round10_key = recover_last_round_key(blocks)
    master_key = invert_round10_key(round10_key)
    plaintext = aes_decrypt_block(blocks[0], master_key)

    assert expand_key(master_key)[10] == round10_key

    print("[+] round10 key:", round10_key.hex())
    print("[+] master key:", master_key.hex())
    print("[+] decrypt(correct):", plaintext.hex())
    print(f"[+] flag: flag{{{master_key.hex()}}}")


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Box.bin")
    solve(path)


if __name__ == "__main__":
    main()
