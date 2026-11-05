#!/usr/bin/env python3
"""
ISCC 深潮协定 (Deep Tide Protocol) — Solver

Recovers the flag from the APK by reversing:
  1. Custom base64 encoding
  2. Native LFSR mixing (8-bit LFSR, polynomial x^8 + x^5 + x^3 + x^2 + 1)
  3. Java CryptoEngine shift-accumulator transform

Usage:
  python solve.py [path/to/app-release.apk]
  (defaults to ./app-release.apk if not specified)
"""

import sys
import os
import base64
import zipfile


def extract_telemetry(apk_path: str) -> tuple[bytes, bytes, str, str]:
    """Extract telemetry.bin from APK assets and parse its contents."""
    with zipfile.ZipFile(apk_path, 'r') as zf:
        with zf.open('assets/telemetry.bin') as f:
            content = f.read().decode('utf-8').strip()

    lines = content.split('\n')
    assert len(lines) == 4, f"Expected 4 lines, got {len(lines)}"

    shifts = bytes.fromhex(lines[0])
    mask = bytes.fromhex(lines[1])
    alphabet = lines[2]
    target = lines[3]

    return shifts, mask, alphabet, target


def custom_b64_decode(s: str, alphabet: str) -> bytes:
    """Decode a custom-base64 string given a 64-char alphabet."""
    std_alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    trans = str.maketrans(alphabet, std_alpha)
    return base64.b64decode(s.translate(trans))


def inverse_lfsr_mix(data: bytes) -> bytes:
    """
    Reverse the 8-bit LFSR mix applied in libdeepseal.so.

    LFSR: x^8 + x^5 + x^3 + x^2 + 1
    Initial state = 0x5D
    For each byte i: data[i] ^= (i*7 + state_after_step_i)
    Since XOR is its own inverse, the forward and inverse are identical.
    """
    state = 0x5D
    out = bytearray(data)
    for i in range(len(out)):
        feedback = ((state >> 2) ^ (state >> 3) ^ (state >> 5) ^ state) & 1
        state = ((feedback << 7) | (state >> 1)) & 0xFF
        out[i] ^= (i * 7 + state) & 0xFF
    return bytes(out)


def inverse_transform(data: bytes, shifts: bytes, mask: bytes) -> str:
    """
    Reverse CryptoEngine.transform().

    Forward (Java):
      if 32 <= c <= 126: c = ((c-32) + shifts[i%len(shifts)]) % 95 + 32
      acc = ((c ^ mask[i%len(mask)]) + acc + i*3) & 0xFF
      out[i] = acc

    Reverse:
      c_xor_mask = (out[i] - out[i-1] - i*3) mod 256
      c_shifted = c_xor_mask ^ mask[i%len(mask)]
      orig = ((c_shifted - 32 - shifts[i%len(shifts)]) % 95) + 32
    """
    out = bytearray()
    prev_acc = 0
    for i in range(len(data)):
        acc_i = data[i]
        c_xor_mask = (acc_i - prev_acc - i * 3) & 0xFF
        c_shifted = c_xor_mask ^ mask[i % len(mask)]
        prev_acc = acc_i

        shift = shifts[i % len(shifts)]
        orig = ((c_shifted - 32 - shift) % 95) + 32
        out.append(orig)

    return out.decode('ascii')


def main():
    apk_path = sys.argv[1] if len(sys.argv) > 1 else 'app-release.apk'

    if not os.path.exists(apk_path):
        print(f"[-] APK not found: {apk_path}")
        print(f"    Usage: {sys.argv[0]} [path/to/app-release.apk]")
        sys.exit(1)

    print(f"[*] Extracting telemetry.bin from {apk_path}...")
    shifts, mask, alphabet, target = extract_telemetry(apk_path)

    print(f"    shifts ({len(shifts)}): {list(shifts)}")
    print(f"    mask ({len(mask)}):     {list(mask)}")
    print(f"    alphabet:              {alphabet}")
    print(f"    target:                {target}")

    print(f"\n[*] Custom-base64-decoding target...")
    decoded = custom_b64_decode(target, alphabet)
    print(f"    decoded ({len(decoded)} bytes): {list(decoded)}")

    print(f"\n[*] Reversing native LFSR mix...")
    after_lfsr = inverse_lfsr_mix(decoded)
    print(f"    after LFSR inverse ({len(after_lfsr)} bytes): {list(after_lfsr)}")

    print(f"\n[*] Reversing Java CryptoEngine.transform...")
    flag_inner = inverse_transform(after_lfsr, shifts, mask)

    flag = f"ISCC{{{flag_inner}}}"
    print(f"\n[+] FLAG: {flag}")
    print(f"[+] Inner: {flag_inner}")

    return flag


if __name__ == '__main__':
    main()
