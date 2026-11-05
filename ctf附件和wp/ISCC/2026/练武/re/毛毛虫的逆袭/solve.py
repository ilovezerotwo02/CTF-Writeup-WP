#!/usr/bin/env python3
"""
ISCC{} 毛毛虫的逆袭 - Reverse Engineering Solver

Analysis of caterpillar36.exe:
- Input format: ISCC{20_chars}
- Two verification paths (OR'd together):
  1. Fast path (LCG): Encrypts flag with LCG-based cipher, compares with "*Y{4ZNrxfAYO,a_za&XG"
  2. Slow path (SHA-256): SHA-256(flag) and SHA-256(flag[10:18]) compared against known hashes
- We reverse the fast path since it's trivially invertible.
"""

def solve():
    # LCG parameters
    lcg_mul = 1103515245
    lcg_add = 12345
    lcg_mod = 1 << 32
    initial_state = 36  # dword_14003F010

    # Expected ciphertext from the binary (at 0x14003F018)
    ciphertext = b"*Y{4ZNrxfAYO,a_za&XG"
    assert len(ciphertext) == 20

    print("[*] Ciphertext:", ciphertext)

    # Reverse the LCG encryption
    # For each char i:
    #   state = (1103515245 * state + 12345) & 0xFFFFFFFF
    #   key = ((state >> 8) & 0xFF) % 95
    #   encoded[i] = ((plain[i] - 32) + key) % 95 + 32
    #
    # Reverse:
    #   plain[i] = ((encoded[i] - 32) - key + 95) % 95 + 32

    state = initial_state
    flag = bytearray(20)

    for i in range(20):
        state = (lcg_mul * state + lcg_add) & 0xFFFFFFFF
        # FIXED: assembly uses SHR 24 (bits 24-31), not HIBYTE(bits 8-15)
        key = ((state >> 24) & 0xFF) % 95
        flag[i] = ((ciphertext[i] - 32) - key) % 95 + 32

    flag_str = flag.decode("ascii")
    print("[*] Recovered flag content:", repr(flag_str))
    print(f"[*] Full flag: ISCC{{{flag_str}}}")

    # Verify by re-encoding
    state2 = initial_state
    encoded = bytearray(20)
    for i in range(20):
        state2 = (lcg_mul * state2 + lcg_add) & 0xFFFFFFFF
        key = ((state2 >> 24) & 0xFF) % 95
        encoded[i] = ((flag[i] - 32) + key) % 95 + 32
    assert bytes(encoded) == ciphertext, "Verification failed!"
    print("[*] Verification passed!")

    # Optionally verify SHA-256 path
    import hashlib
    h1 = hashlib.sha256(flag_str.encode()).hexdigest()
    print(f"[*] SHA-256(flag content): {h1}")
    print(f"    Expected (slow path):  7c9a4772c5c1b43f5ccee4e81f46a33aa5a80ffb7d232ae5a118e80a7d558777")

    h2 = hashlib.sha256(flag_str[10:18].encode()).hexdigest()
    print(f"[*] SHA-256(flag[10:18]): {h2}")
    print(f"    Expected (slow path):  0fc7f97b5dcd75e6c999ec614bd5522338ecc8fe3a2f7954a3536187d5ccc69d")

if __name__ == "__main__":
    solve()
