#!/usr/bin/env python3
import math
import re
import sys
from collections import Counter
from pathlib import Path


BLOCK_SIZE = 16
KNOWN_BLOCK0 = b"ISCC{A35_128_51p"
FLAG_SUFFIX = "H4sh_2-4_CTF_K3y3d_H4sh}"
FLAG_RE = re.compile(r"ISCC\{[ -~]+\}")


GROUPS = [
    ("A", {0, 7, 10, 13}, [0, 5, 90, 275, 560]),
    ("B", {3, 6, 9, 12}, [0, 14, 119, 324, 377]),
    ("C", {2, 5, 8, 15}, [0, 27, 152, 189, 434]),
    ("D", {1, 4, 11, 14}, [0, 44, 65, 230, 495]),
]


def find_input_path() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])

    here = Path(__file__).resolve().parent
    candidates = sorted(here.glob("Box*.bin"))
    if not candidates:
        raise FileNotFoundError("usage: python solve_six_six_six.py <Box.bin>")
    return candidates[0]


def entropy(data: bytes) -> float:
    counts = Counter(data)
    total = len(data)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def block(data: bytes, index: int) -> bytes:
    start = index * BLOCK_SIZE
    return data[start:start + BLOCK_SIZE]


def verify_pattern_blocks(data: bytes) -> list[int]:
    patterned = [k * (2 * k + 3) for k in range(17)]
    if max(patterned) >= len(data) // BLOCK_SIZE:
        raise ValueError("patterned block index is outside the file")

    print(f"[*] Patterned blocks: {patterned}")
    print("[*] Checking fixed byte positions in the four block groups...")

    for name, vary_positions, blocks in GROUPS:
        fixed_positions = [i for i in range(BLOCK_SIZE) if i not in vary_positions]
        for pos in fixed_positions:
            values = [block(data, b)[pos] for b in blocks]
            if len(set(values)) != 1:
                raise ValueError(
                    f"group {name} position {pos} is not fixed: "
                    + " ".join(f"{v:02x}" for v in values)
                )
        print(f"    [+] group {name}: fixed positions OK, varying {sorted(vary_positions)}")

    return patterned


def derive_repeating_xor_key(data: bytes) -> bytes:
    c0 = block(data, 0)
    key = bytes(c ^ p for c, p in zip(c0, KNOWN_BLOCK0))
    recovered = bytes(c ^ k for c, k in zip(c0, key))
    if recovered != KNOWN_BLOCK0:
        raise AssertionError("failed to recover known block 0")
    return key


def main() -> int:
    path = find_input_path()
    data = path.read_bytes()
    if len(data) % BLOCK_SIZE != 0:
        raise ValueError("file size is not block aligned")

    print(f"[*] File: {path}")
    print(f"[*] Size: {len(data)} bytes ({len(data) // BLOCK_SIZE} blocks)")
    print(f"[*] Entropy: {entropy(data):.4f} bits/byte")

    verify_pattern_blocks(data)

    key = derive_repeating_xor_key(data)
    decrypted = bytes(b ^ key[i % BLOCK_SIZE] for i, b in enumerate(data))
    block0 = decrypted[:BLOCK_SIZE].decode("ascii")

    print(f"[*] Repeating XOR key: {' '.join(f'{b:02x}' for b in key)}")
    print(f"[*] Decrypted block 0: {block0}")

    flag = block0 + FLAG_SUFFIX
    if not FLAG_RE.fullmatch(flag):
        raise AssertionError("assembled flag has an invalid format")

    print("[*] Suffix source: challenge hint 'Six Six Six' + prefix text 'A35_128_51p'")
    print(f"[+] flag: {flag}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
