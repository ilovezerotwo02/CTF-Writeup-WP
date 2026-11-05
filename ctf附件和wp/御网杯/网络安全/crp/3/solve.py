from __future__ import annotations

import hashlib
import struct
import sys
from itertools import cycle, product
from pathlib import Path
from string import printable

from Crypto.Cipher import AES

CT = Path("ciphertext.bin").read_bytes()
assert len(CT) == 80 and len(CT) % 16 == 0
BLOCKS = [CT[i : i + 16] for i in range(0, len(CT), 16)]

print("=== Ciphertext Blocks ===")
for i, b in enumerate(BLOCKS):
    print(f"  [{i}] {b.hex()}")

# ── 1. XOR-based approaches ──────────────────────────────────────────
print("\n=== XOR Analysis ===")

# Check if it's simple XOR with repeating key (independent per byte position across blocks)
# If plaintext is ASCII (high bit = 0), then ciphertext byte XOR plaintext byte = key byte
# For each byte position j, all plaintext[j] in different blocks share the same key byte
# So C[i][j] XOR P[i][j] = K[j] for all i
# If P[i][j] is always printable ASCII (0x20-0x7e), there should be a consistent K[j]

# Try XOR-based approach: if all 5 blocks share the same XOR key
# Then for each byte position, the key byte must make all 5 plaintext bytes printable
# This is similar to multi-byte XOR cracking

def score_text(text: bytes) -> float:
    """Score text as likelihood of being English/flag text"""
    s = 0.0
    for b in text:
        ch = chr(b)
        if ch in 'flag{}_0123456789abcdefABCDEF':
            s += 3.0
        elif ch.isalpha():
            s += 1.5
        elif ch.isdigit():
            s += 1.0
        elif ch in ' -.,!?':
            s += 0.5
        elif 0x20 <= b <= 0x7e:
            s += 0.1
        else:
            s -= 2.0
    return s


def crack_xor_ecb() -> bytes | None:
    """Try to find the XOR key byte-by-byte by assuming printable plaintext"""
    key = bytearray(16)
    for pos in range(16):
        best_score = -1e9
        best_kb = 0
        for k in range(256):
            ok = True
            score = 0.0
            for blk in BLOCKS:
                pb = blk[pos] ^ k
                ch = chr(pb)
                if pb < 0x20 or pb > 0x7e:
                    if pb not in (0x00, 0x0a, 0x0d):  # allow null, newline, CR in padding
                        ok = False
                        break
                else:
                    score += 1.0
                    if ch in 'flag{}_0123456789abcdefABCDEF':
                        score += 2.0
                    elif ch.isalpha():
                        score += 0.5
            if ok and score > best_score:
                best_score = score
                best_kb = k
        key[pos] = best_kb
        print(f"  pos {pos:02d}: key_byte=0x{best_kb:02x}, best_score={best_score:.1f}")
    plaintext = bytes(CT[i] ^ key[i % 16] for i in range(len(CT)))
    print(f"  Plaintext: {plaintext}")
    return bytes(key)


print("\n--- Method: XOR with fixed 16-byte key (all printable) ---")
key = crack_xor_ecb()


# ── 2. Try AES-ECB with common keys ─────────────────────────────────
print("\n=== AES-ECB Decryption Attempts ===")

def try_aes_key(key_bytes: bytes, label: str) -> bool:
    try:
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        pt = cipher.decrypt(CT)
        if b'flag{' in pt.lower() or b'FLAG{' in pt:
            print(f"  [{label}] FOUND: {pt}")
            return True
        # Check if mostly printable
        printable_count = sum(1 for b in pt if 0x20 <= b <= 0x7e or b in (0x0a, 0x0d, 0x00))
        if printable_count >= 60:  # 75% printable
            print(f"  [{label}] Mostly printable: {pt}")
    except Exception:
        pass
    return False

# Common CTF keys
candidates = []
# From challenge hints
for s in ["otp_10", "otp10", "OTP_10", "ECB Pattern Leakage", "ecb_pattern_leakage",
          "ECBPatternLeakage", "flag", "password", "1234567890123456"]:
    candidates.append((hashlib.md5(s.encode()).digest(), f"MD5({s})"))
    candidates.append((hashlib.sha256(s.encode()).digest()[:16], f"SHA256({s})[:16]"))
    candidates.append((s.encode().ljust(16, b'\x00')[:16], f"'{s}' padded"))

# Zero key, all-ones, etc.
candidates.append((b'\x00' * 16, "all zeros"))
candidates.append((b'\xff' * 16, "all 0xff"))
candidates.append((b'\x01' * 16, "all 0x01"))
candidates.append((bytes(range(16)), "0..15"))
candidates.append((b'AES_ECB_KEY_1234'[:16], "generic"))

# Try first block as key (self-decrypt, unlikely but try)
candidates.append((BLOCKS[0], "block0 as key"))

for k, label in candidates:
    if try_aes_key(k, label):
        break


# ── 3. XOR block analysis: what if each block XOR same key? ─────────
print("\n=== XOR Between Blocks (crib drag) ===")
# If it's XOR with same key: C0 XOR C1 = P0 XOR P1
# This gives us XOR of two plaintexts
for i in range(len(BLOCKS)):
    for j in range(i + 1, len(BLOCKS)):
        xor_diff = bytes(a ^ b for a, b in zip(BLOCKS[i], BLOCKS[j]))
        print(f"  Block{i} XOR Block{j}: {xor_diff.hex()}")

# ── 4. Check if it's repeating-key XOR (not ECB blocks) ─────────────
print("\n=== Repeating-Key XOR Analysis (keysize 1-32) ===")

def hamming(a: bytes, b: bytes) -> int:
    return sum(bin(x ^ y).count('1') for x, y in zip(a, b))

# Find likely key sizes
key_sizes = []
for ks in range(1, 33):
    if len(CT) >= ks * 4:
        chunks = [CT[i:i+ks] for i in range(0, len(CT) - ks * 2, ks)]
        if len(chunks) >= 2:
            dist = sum(hamming(chunks[i], chunks[i+1]) for i in range(0, len(chunks)-1, 2))
            norm_dist = dist / (len(chunks) // 2) / ks
            key_sizes.append((ks, norm_dist))

key_sizes.sort(key=lambda x: x[1])
print(f"  Top key sizes by normalized Hamming distance:")
for ks, dist in key_sizes[:8]:
    print(f"    size={ks:2d}, norm_dist={dist:.3f}")


# ── 5. Try decrypting with specific hex patterns ────────────────────
print("\n=== Additional Checks ===")

# Check if it's base64-like encoded before encryption
# Check for any obvious structure
for blk in BLOCKS:
    # Check if first/last bytes show patterns
    pass

# Print summary
print("\n=== Summary ===")
print(f"Ciphertext: {CT.hex()}")
print(f"Number of blocks: {len(BLOCKS)}")
print(f"Unique blocks: {len(set(b for b in BLOCKS))}")
