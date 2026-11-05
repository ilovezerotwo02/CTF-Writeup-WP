#!/usr/bin/env python3
"""Cross-check: verify combined cipher against step-by-step implementation."""
import struct

COMBINED_PERM = [5, 1, 0, 3, 6, 7, 4, 2]
COMBINED_ADD = [8, 14, 23, 8, 5, 11, 23, 4]

def encrypt_block_combined(block):
    assert len(block) == 8
    result = [0] * 8
    for i in range(8):
        result[COMBINED_PERM[i]] = (block[i] + COMBINED_ADD[i]) & 0xFF
    return bytes(result)

# Step-by-step implementation matching the C++ code exactly
PERMS = {
    "R":  (0,5,2,1,4,7,6,3),
    "L":  (2,1,6,3,0,5,4,7),
    "U":  (0,1,6,2,4,5,7,3),
    "D":  (1,5,2,3,0,4,6,7),
    "F":  (0,1,2,3,6,4,7,5),
    "B":  (1,3,0,2,4,5,6,7),
}
ADDS = {
    "R":  (0,1,0,1,0,1,0,1),
    "L":  (2,0,2,0,2,0,2,0),
    "U":  (0,0,3,3,0,0,3,3),
    "D":  (4,4,0,0,4,4,0,0),
    "F":  (0,0,0,0,5,5,5,5),
    "B":  (6,6,6,6,0,0,0,0),
}
INV_PERMS = {}
for name, perm in PERMS.items():
    inv = [0]*8
    for old, new in enumerate(perm):
        inv[new] = old
    INV_PERMS[name] = tuple(inv)

PRIMED_ADDS = {
    "R":  (0,7,0,7,0,7,0,7),
    "L":  (8,0,8,0,8,0,8,0),
    "U":  (0,0,9,9,0,0,9,9),
    "D":  (10,10,0,0,10,10,0,0),
    "F":  (0,0,0,0,11,11,11,11),
    "B":  (12,12,12,12,0,0,0,0),
}

def apply_move(block, perm, add):
    """block -> add -> permute"""
    tmp = [(block[i] + add[i]) & 0xFF for i in range(8)]
    result = [0] * 8
    for old, new in enumerate(perm):
        result[new] = tmp[old]
    return bytes(result)

def encrypt_stepwise(data, key_sequence):
    padded = data + bytes([8]*8)  # pkcs7 padded to 16 bytes
    result = b""
    for blk_start in range(0, 16, 8):
        block = padded[blk_start:blk_start+8]
        for move_name in key_sequence:
            if move_name.endswith("'"):
                base = move_name[0]
                block = apply_move(block, INV_PERMS[base], PRIMED_ADDS[base])
            else:
                block = apply_move(block, PERMS[move_name], ADDS[move_name])
        result += block
    return result

# Test with "ZVYHMYFA"
password = "ZVYHMYFA"
data = password.encode('latin-1')

# Combined
c1 = encrypt_block_combined(data)
c2 = encrypt_block_combined(bytes([8]*8))
combined = c1 + c2

# Stepwise
key_seq = ["R", "U", "F", "R'", "D", "D"]
stepwise = encrypt_stepwise(data, key_seq)

print(f"Combined: {combined.hex()}")
print(f"Stepwise: {stepwise.hex()}")
print(f"Match: {combined == stepwise}")

# Show the permutation pipeline
print("\n--- Encryption details ---")
block = list(data)
print(f"Input block:  {[hex(b) for b in block]}")

for move_name in key_seq:
    if move_name.endswith("'"):
        base = move_name[0]
        block = list(apply_move(bytes(block), INV_PERMS[base], PRIMED_ADDS[base]))
        print(f"After {move_name}: {[hex(b) for b in block]}")
    else:
        block = list(apply_move(bytes(block), PERMS[move_name], ADDS[move_name]))
        print(f"After {move_name}:  {[hex(b) for b in block]}")

# Also verify by decrypting
C1 = combined[:8]
C2 = combined[8:]

# Decryption: reverse combined perm/add
# a[i] = (c[perm[i]] - add[i]) mod 256
def decrypt_block(enc):
    result = [0]*8
    for i in range(8):
        result[i] = (enc[COMBINED_PERM[i]] - COMBINED_ADD[i]) & 0xFF
    return bytes(result)

decrypted = decrypt_block(C1)
print(f"\nDecrypted C1: {decrypted}")
print(f"Original:     {data}")
print(f"Match: {decrypted == data}")
