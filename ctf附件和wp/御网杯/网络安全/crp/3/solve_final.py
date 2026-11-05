from __future__ import annotations

from pathlib import Path
import hashlib
import itertools
import struct

CT = Path("ciphertext.bin").read_bytes()
BLOCKS = [CT[i:i+16] for i in range(0, len(CT), 16)]

# ===================================================================
# APPROACH 1: XOR with key derived from "otp_10" (length 10 hinted)
# ===================================================================
print("=== XOR with 10-byte keys derived from 'otp_10' ===")

# The filename "otp_10" has 6 chars. Maybe the 10 means key length 10?
# Try many derivations of a 10-byte key from "otp_10"
bases = [
    b'otp_10otp_',      # repeat to 10
    b'OTP_10OTP_',      # uppercase repeat
    b'otp_10\0\0\0\0',  # null pad
    b'otp_10    ',      # space pad
    b'otp_10____',      # underscore pad
    b'otpotpotpot',     # o-t-p repeated
    b'OTPOTPOTPOT',     # O-T-P repeated
    b'10otp10otp',      # 10 first
    b'0123456789',      # digits
    b'otp10otp10',      # no underscore
    b'OTP10OTP10',
]

# Also try MD5/SHA of "otp_10" truncated to 10
for h in [hashlib.md5, hashlib.sha1, hashlib.sha256]:
    bases.append(h(b'otp_10').digest()[:10])
    bases.append(h(b'OTP_10').digest()[:10])

for key in bases:
    pt = bytes(CT[i] ^ key[i % len(key)] for i in range(len(CT)))
    if b'flag' in pt.lower():
        print(f"  FOUND key={key!r}: {pt}")
    # Check if at least 70% printable
    printable = sum(1 for b in pt if 0x20 <= b <= 0x7e)
    if printable >= 70:
        print(f"  Mostly printable key={key!r}: {pt}")

# ===================================================================
# APPROACH 2: What if it's AES-ECB with key = various forms of "otp_10"?
# ===================================================================
print("\n=== AES-ECB with exhaustive 'otp_10' key variants ===")
from Crypto.Cipher import AES

# Generate ALL plausible 16-byte keys from "otp_10"
key_candidates = set()

# Direct padding variants
for pad_char in [b'\x00', b'\x01', b'\x10', b' ', b'_', b'\xff']:
    key_candidates.add(b'otp_10'.ljust(16, pad_char))
    key_candidates.add(b'OTP_10'.ljust(16, pad_char))
    key_candidates.add(b'otp10'.ljust(16, pad_char))
    key_candidates.add(b'OTP10'.ljust(16, pad_char))

# Repeated to 16
for base in [b'otp_10', b'OTP_10', b'otp10', b'OTP10', b'otp', b'OTP']:
    key_candidates.add((base * (16 // len(base) + 1))[:16])

# Hash variants
for s in [b'otp_10', b'OTP_10', b'otp10', b'OTP10', b'ecb', b'ECB',
          b'pattern', b'leakage', b'flag', b'crypto']:
    for h in [hashlib.md5, hashlib.sha1, hashlib.sha256, hashlib.sha512]:
        key_candidates.add(h(s).digest()[:16])

# Numeric interpretations
key_candidates.add(struct.pack('>IIII', 0, 0, 0, 10))
key_candidates.add(struct.pack('<IIII', 0, 0, 0, 10))
key_candidates.add(struct.pack('>QQ', 0, 10))
key_candidates.add(b'\x00' * 15 + b'\x10')  # "10" as last byte
key_candidates.add(b'\x00' * 14 + b'\x00\x10')
key_candidates.add(b'o' * 16)
key_candidates.add(b't' * 16)
key_candidates.add(b'p' * 16)
key_candidates.add(b'_' * 16)

# More creative: "otp" = one-time-pad, "10" = X (as in 10th attempt)
key_candidates.add(b'ONE_TIMEPAD_KEY_')
key_candidates.add(b'OneTimePadKey!!!')
key_candidates.add(b'0123456789ABCDEF')
key_candidates.add(b'key_of_otp_10_ctf')

for key in key_candidates:
    try:
        cipher = AES.new(key, AES.MODE_ECB)
        pt = cipher.decrypt(CT)
        if b'flag' in pt.lower() or b'FLAG' in pt:
            print(f"  *** AES FOUND key={key.hex()} ({key!r}): {pt}")
        printable = sum(1 for b in pt if 0x20 <= b <= 0x7e)
        if printable >= 75:
            print(f"  High printable key={key.hex()}: {pt}")
    except Exception:
        pass

# ===================================================================
# APPROACH 3: XOR with byte-position-specific keys (like Vigenere on 16-byte groups)
# ===================================================================
print("\n=== XOR: per-position key recovery with relaxed constraints ===")
# For each byte position, find key bytes that produce "flag-like" output
# Allow padding bytes (0x00-0x10) as valid in later blocks

def is_likely_flag_byte(b, block_idx, pos):
    """Check if byte could be part of flag plaintext"""
    if 0x20 <= b <= 0x7e:  # printable ASCII
        return True
    if b in (0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
             0x08, 0x09, 0x0a, 0x0d, 0x10):  # padding/newline
        # Padding more likely in later blocks and later positions
        if block_idx >= 3:  # last 2 blocks
            return True
        if block_idx == 2 and pos >= 12:  # end of middle block
            return True
    return False

for pos in range(16):
    good_keys = []
    for k in range(256):
        results = [(blk[pos] ^ k, i) for i, blk in enumerate(BLOCKS)]
        if all(is_likely_flag_byte(b, i, pos) for b, i in results):
            chars = ''.join(chr(b) if 0x20 <= b <= 0x7e else '.' for b, _ in results)
            good_keys.append((k, chars))
    if good_keys:
        print(f"  pos {pos:02d}: {len(good_keys)} valid keys")
        for k, chars in good_keys[:5]:
            print(f"    0x{k:02x} -> {chars!r}")

# ===================================================================
# APPROACH 4: What if blocks are in wrong order? Try all permutations
# ===================================================================
print("\n=== Block permutation analysis ===")
# For XOR with fixed key: the key doesn't depend on block order
# But for AES-ECB: each block encrypts independently, order matters!

# What if the blocks are scrambled? Let's try all 120 permutations
# and check if any looks meaningful when XORed with a potential key
# For each permutation, try common XOR keys

import itertools as it

# Quick check: for each permutation, see if XOR with common patterns yields "flag{"
common_xor_keys = [b'otp_10otp_10otp_', b'flagflagflagflag', b'0123456789abcdef',
                   b'otp_10\0\0\0\0\0\0\0\0\0\0']

found_any = False
for perm in it.permutations(range(5)):
    perm_ct = b''.join(BLOCKS[i] for i in perm)
    for key in common_xor_keys:
        pt = bytes(perm_ct[i] ^ key[i % len(key)] for i in range(len(perm_ct)))
        if b'flag{' in pt.lower():
            print(f"  FOUND with perm={perm}, key={key!r}: {pt}")
            found_any = True

if not found_any:
    print("  No flag found with block permutations and common XOR keys")

# ===================================================================
# APPROACH 5: What if the key is REVEALED by ECB pattern leakage?
# In ECB, CTR[i] = encrypt(P[i]). If P[i]=P[j], then C[i]=C[j].
# Here no repeats. But what if P[i] XOR P[j] = constant?
# Then C[i] XOR C[j] would be... nothing special for AES.
# ===================================================================

# ===================================================================
# APPROACH 6: The flag might be a HASH or derivation of the ciphertext
# ===================================================================
print("\n=== Flag might be derived from ciphertext ===")
print(f"  MD5(CT) = {hashlib.md5(CT).hexdigest()}")
print(f"  SHA1(CT) = {hashlib.sha1(CT).hexdigest()}")
print(f"  SHA256(CT) = {hashlib.sha256(CT).hexdigest()}")
print(f"  CT hex = {CT.hex()}")

# Common flag formats
print(f"\n  Possible flags:")
print(f"  flag{{{CT.hex()}}}")
print(f"  flag{{{hashlib.md5(CT).hexdigest()}}}")
print(f"  flag{{{hashlib.sha256(CT).hexdigest()}}}")
print(f"  flag{{ECB_l34ks_p4tt3rns}}")
print(f"  flag{{ECB_Pattern_Leakage_otp_10}}")
print(f"  flag{{0tP_3cB_p4tt3rn_l34k}}")

# ===================================================================
# APPROACH 7: XOR with key = first N bytes of plaintext readable block
# ===================================================================
print("\n=== Self-referential XOR (key = part of ciphertext) ===")
for key_start in range(0, 80, 8):
    for key_len in [4, 8, 16]:
        key = CT[key_start:key_start + key_len]
        pt = bytes(CT[i] ^ key[i % len(key)] for i in range(len(CT)))
        if b'flag{' in pt.lower():
            print(f"  FOUND: key=CT[{key_start}:{key_start+key_len}] = {key.hex()}")
            print(f"  Plaintext: {pt}")

print("\n=== Done ===")
