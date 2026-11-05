"""
ISCC 如影随形 (Like a Shadow Following the Form) - Reverse Engineering Solver

Algorithm analysis:
1. Input 16 chars (flag content inside ISCC{})
2. OHF3nw: permutation-driven transformation calling u8afi3 16 times
3. Each u8afi3 call does:
   a. Autokey Caesar cipher on all 16 chars (initial shift = a4 = col_diff)
   b. S-box substitution a5 times on the char at (row, col) only
4. Result compared with encrypted target at 0x140004000 (`;s<b/?vEiC{s"{C9`)

Key data:
- M (source):  [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
- M_target:    [10,9,12,5,2,11,6,3,1,4,14,7,13,8,0,15]
- Key string:  "iscc_{this_is_not_flag}"
- S-box:       95 bytes at 0x1400050E0 XOR 0xF5
"""

def build_sbox():
    """Build S-box from 95 bytes at 0x1400050E0 XOR 0xF5"""
    raw = [
        0xF4,0xF6,0xC4,0xC5,0xE8,0xAC,0xBC,0xF5,0xD2,0xAB,0xEC,0xE0,0xB5,0xCD,0xCF,0xC3,
        0xAF,0xD7,0xA5,0xD0,0xA9,0xFB,0xDC,0xA6,0xD5,0xA2,0xD8,0xEF,0xE7,0xA3,0xEB,0xB7,
        0xB3,0xAD,0xDD,0xC6,0xAE,0xF9,0xC1,0xB1,0xF8,0xB4,0xDE,0xA8,0xFA,0xEE,0xC0,0xEA,
        0xE5,0xD3,0xE6,0xBE,0xB0,0xA4,0xB9,0xBB,0xC7,0xFE,0xBF,0xF3,0xE1,0xDA,0xF0,0xF1,
        0xFF,0xA1,0xB8,0xE3,0xDF,0xBD,0xA7,0xFC,0xD9,0xCB,0xA0,0xBA,0xE2,0xE4,0xC8,0xD6,
        0xCE,0xE9,0xD1,0xCC,0xC2,0xDB,0xCA,0xED,0xFD,0xD4,0xF2,0xC9,0xB6,0xB2,0xF7,
    ]
    sbox = [b ^ 0xF5 for b in raw]
    inv_sbox = [0] * 95
    for i, v in enumerate(sbox):
        inv_sbox[v] = i
    return sbox, inv_sbox


def compute_params():
    """
    Compute 16 (a2, a3, a4, a5) parameter tuples for u8afi3 calls.

    OHF3nw iterates M row by row (v2=4..1).
    For each M[row][col], find same value in M_target.

    v5 tracks search row: starts at v2-4, increments per row advance.
    Final v5 = v2 - 4 + target_row

    u8afi3(a1, 4-v2, col, abs(target_col-col), abs(v5))
    """
    M = list(range(16))
    Mt = [10, 9, 12, 5, 2, 11, 6, 3, 1, 4, 14, 7, 13, 8, 0, 15]

    params = []
    for v2 in range(4, 0, -1):
        src_row = 4 - v2
        for col in range(4):
            val = M[src_row * 4 + col]
            tpos = Mt.index(val)
            trow, tcol = tpos // 4, tpos % 4

            a2 = src_row          # matrix row to modify
            a3 = col              # matrix col to modify
            a4 = abs(tcol - col)  # autokey initial shift
            a5 = abs(v2 - 4 + trow)  # s-box iterations = abs(v5)
            params.append((a2, a3, a4, a5))
    return params


def forward_autokey(chars, init_shift):
    """Forward autokey Caesar cipher on printable chars (32-126)."""
    out = list(chars)
    shift = init_shift
    for i in range(len(out)):
        if 32 <= out[i] <= 126:
            out[i] = (shift + out[i] - 32) % 95 + 32
            shift = out[i] - 32
    return out


def reverse_autokey(state, init_shift):
    """
    Reverse autokey Caesar cipher.

    Forward shift sequence depends on 'after' values of printable chars.
    We precompute shifts from current state, then reverse right-to-left.
    """
    # Precompute shift used at each printable position
    shifts = {}
    shift = init_shift
    for i, ch in enumerate(state):
        if 32 <= ch <= 126:
            shifts[i] = shift
            shift = ch - 32

    out = list(state)
    # Reverse right-to-left (left chars unaffected by right-side modifications)
    for i in range(len(out) - 1, -1, -1):
        if 32 <= out[i] <= 126:
            out[i] = (out[i] - 32 - shifts[i]) % 95 + 32
    return out


def forward_sbox(ch, iters, key_byte, sbox):
    """F^n where F(x) = (key_byte + sbox[x-32]) % 95 + 32"""
    for _ in range(iters):
        if 32 <= ch <= 126:
            ch = (key_byte + sbox[ch - 32]) % 95 + 32
    return ch


def reverse_sbox(ch, iters, key_byte, inv_sbox):
    """F^{-n}"""
    for _ in range(iters):
        if 32 <= ch <= 126:
            ch = inv_sbox[(ch - 32 - key_byte) % 95] + 32
    return ch


def run_forward(flag_content, sbox):
    """
    Run the full forward algorithm.
    Returns the 16-byte output that should match the encrypted target.
    """
    key_str = "iscc_{this_is_not_flag}"
    params = compute_params()
    state = list(flag_content)

    for a2, a3, a4, a5 in params:
        key_byte = ord(key_str[a5 % len(key_str)]) % 0x5F

        # 1. Autokey Caesar on all chars
        state = forward_autokey(state, a4)

        # 2. S-box on one char
        idx = a2 * 4 + a3
        state[idx] = forward_sbox(state[idx], a5, key_byte, sbox)

    return state


def solve():
    sbox, inv_sbox = build_sbox()
    params = compute_params()
    key_str = "iscc_{this_is_not_flag}"

    # Expected ciphertext from 0x140004000
    expected = [ord(c) for c in ";s<b/?vEiC{s\"{C9"]

    print(f"Expected ciphertext: {bytes(expected)}")
    print(f"Key string: '{key_str}' (len={len(key_str)})")
    print(f"Params (a2 row, a3 col, a4 shift, a5 iters):")
    for i, (a2, a3, a4, a5) in enumerate(params):
        kb = ord(key_str[a5 % len(key_str)]) % 0x5F
        print(f"  [{i:2d}] row={a2} col={a3} shift={a4} iter={a5} keybyte={kb}")

    # Reverse the transformations
    state = list(expected)

    for i in range(len(params) - 1, -1, -1):
        a2, a3, a4, a5 = params[i]
        key_byte = ord(key_str[a5 % len(key_str)]) % 0x5F

        # 1. Reverse S-box (on the single modified char)
        idx = a2 * 4 + a3
        state[idx] = reverse_sbox(state[idx], a5, key_byte, inv_sbox)

        # 2. Reverse autokey (all chars)
        state = reverse_autokey(state, a4)

    flag_content = bytes(state)
    flag = f"ISCC{{{flag_content.decode(errors='replace')}}}"

    print(f"\nDecoded flag content: {flag_content}")
    print(f"Flag: {flag}")

    # Verify with forward pass
    print("\n--- Verification ---")
    forward_out = run_forward(list(flag_content), sbox)
    expected_chars = bytes(expected)
    forward_bytes = bytes(forward_out)
    print(f"Forward output:    {forward_bytes}")
    print(f"Expected:          {expected_chars}")
    print(f"Match: {forward_bytes == expected_chars}")

    return flag


if __name__ == "__main__":
    solve()
