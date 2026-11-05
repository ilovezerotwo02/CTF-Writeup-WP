#!/usr/bin/env python3
"""
ISCC{} 毛毛虫的逆袭 - Detailed solver with verification
"""

def solve_detailed():
    lcg_mul = 1103515245
    lcg_add = 12345
    lcg_mod = 1 << 32
    initial_state = 36

    ciphertext = b"*Y{4ZNrxfAYO,a_za&XG"
    assert len(ciphertext) == 20

    print("=" * 60)
    print("Fast Path (LCG) Solution")
    print("=" * 60)

    # Reversed LCG
    state = initial_state
    flag = bytearray(20)

    print(f"{'i':>3} {'state':>12} {'key_byte':>4} {'key_mod':>4} {'ct':>4} {'pt':>4} {'pt_char'}")
    print("-" * 60)

    for i in range(20):
        state = (lcg_mul * state + lcg_add) & 0xFFFFFFFF
        key_byte = (state >> 24) & 0xFF  # FIXED: SHR 24, not bits 8-15
        key_mod = key_byte % 95
        ct = ciphertext[i]
        pt = ((ct - 32) - key_mod) % 95 + 32
        flag[i] = pt
        print(f"{i:>3} {state:>12} {key_byte:>4} {key_mod:>4} {ct:>4} {pt:>4} {chr(pt):>8}")

    flag_str = flag.decode("ascii")
    print(f"\n[*] Recovered flag content: {repr(flag_str)}")
    print(f"[*] Full flag: ISCC{{{flag_str}}}")

    # Verification
    print("\n" + "=" * 60)
    print("Verification (re-encrypting)")
    print("=" * 60)
    state2 = initial_state
    encoded = bytearray(20)
    for i in range(20):
        state2 = (lcg_mul * state2 + lcg_add) & 0xFFFFFFFF
        key = ((state2 >> 24) & 0xFF) % 95
        encoded[i] = ((flag[i] - 32) + key) % 95 + 32

    assert bytes(encoded) == ciphertext, "Verification FAILED!"
    print("[+] Verification PASSED")
    print(f"    Encoded:  {bytes(encoded)}")
    print(f"    Expected: {ciphertext}")

    # Check if all chars are printable and valid
    print("\n" + "=" * 60)
    print("Char Validation")
    print("=" * 60)
    for i, c in enumerate(flag_str):
        valid = 32 <= ord(c) <= 126
        print(f"  [{i}] = {repr(c)} (0x{ord(c):02x}) {'[OK]' if valid else '[INVALID]'}")

    return flag_str


if __name__ == "__main__":
    flag_content = solve_detailed()
