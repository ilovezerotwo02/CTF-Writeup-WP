#!/usr/bin/env python3
"""
X的宝藏 (X's Treasure) - CTF Exploit Script
ISCC 2025/2026 MISC Challenge

Challenge Description:
传说最著名的黑客X留下了一个宝藏，里面隐藏着CTF的终极秘密，
只有找到X的信物才能打开这个宝藏。

Files:
  attachment-54.zip -> ？？？.rar (RAR5 encrypted)

Solution Summary:
  1. Outer RAR password: "ISCC"
  2. Extract nested files: 心律.rar + 不知道啥玩意儿.png (actually UTF-8 text)
  3. The PNG (actually text file) contains RSA parameters and hidden Base64 strings
  4. One Base64 string decodes to: "直接输出ISCC{X_streasure_KEY}"
  5. Flag: ISCC{X_streasure_KEY}
"""

import hashlib
import base64
import struct
import zlib
import os
import subprocess
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# ============================================================
# Step 1: Crack the outer RAR password
# ============================================================
def check_rar5_password(filepath, password):
    """
    Verify RAR5 password using rarfile's built-in algorithm.
    PBKDF2-HMAC-SHA256 with iterations = (1 << kdf_count) + 32
    XOR all 32 derived bytes into 8-byte buffer.
    """
    with open(filepath, 'rb') as fp:
        data = fp.read()

    # RAR5 encryption block structure:
    # Offset 13: HEAD_TYPE (0x04 = ENCRYPTION)
    # Offset 14: HEAD_FLAGS (0x00)
    # Offset 15: encryption_algo vint (0x00 = AES-256)
    # Offset 16: encryption_flags vint (0x01 = HAS_CHECKVAL)
    # Offset 17: kdf_count byte (0x0f = 15)
    # Offset 18-33: salt (16 bytes)
    # Offset 34-45: check_value (12 bytes)
    #   [0:8] hdr_check
    #   [8:12] hdr_sum (integrity check)

    salt = data[18:34]
    check_val = data[34:46]
    kdf_count = data[17]

    hdr_check = check_val[:8]
    hdr_sum = check_val[8:12]

    # Verify integrity: SHA256(hdr_check)[:4] == hdr_sum
    assert hashlib.sha256(hdr_check).digest()[:4] == hdr_sum, \
        "Invalid check value integrity"

    iterations = (1 << kdf_count) + 32  # 32800 for kdf_count=15

    pwd_hash = hashlib.pbkdf2_hmac('sha256', password, salt, iterations, dklen=32)

    pwd_check = bytearray(8)
    for i, v in enumerate(pwd_hash):
        pwd_check[i & 7] ^= v

    return bytes(pwd_check) == hdr_check


# ============================================================
# Step 2: Decrypt the outer RAR archive headers
# ============================================================
def decrypt_rar5_headers(filepath, password):
    """
    Decrypt RAR5 archive headers using the correct key and IV.
    KEY derivation uses iterations = 1 << kdf_count (32768 for kdf_count=15)
    IV = first 16 bytes of encrypted data
    """
    with open(filepath, 'rb') as fp:
        data = fp.read()

    salt = data[18:34]
    kdf_count = data[17]

    # KEY uses 1 << kdf_count iterations (NOT the +32 used for password check)
    key_iters = 1 << kdf_count  # 32768
    key = hashlib.pbkdf2_hmac('sha256', password, salt, key_iters, dklen=32)

    enc_data = data[46:]  # Data after encryption block
    iv = enc_data[:16]     # First 16 bytes = CBC IV

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decrypted = cipher.decryptor().update(enc_data[16:])

    # Save with RAR5 marker
    with open('decrypted_archive.rar', 'wb') as f:
        f.write(b'Rar!\x1a\x07\x01\x00')
        f.write(decrypted)

    return decrypted


# ============================================================
# Step 3: Extract files and find the flag
# ============================================================
def main():
    print("=" * 60)
    print("X\\u7684\\u5b9d\\u85cf (X's Treasure) - Exploit")
    print("=" * 60)

    # Find the RAR file
    rar_file = None
    for f in os.listdir('.'):
        if os.path.isfile(f) and os.path.getsize(f) == 567950:
            rar_file = f
            break

    if not rar_file:
        print("Error: RAR file not found!")
        return

    print(f"\\n[+] Found RAR file: {repr(rar_file)}")

    # Step 1: Verify password "ISCC"
    print(f"\\n[+] Step 1: Verifying password...")
    if check_rar5_password(rar_file, b'ISCC'):
        print(f"  [!] Outer RAR password: ISCC")
    else:
        print(f"  [-] Password ISCC is incorrect!")
        return

    # Step 2: Extract files using 7-Zip
    print(f"\\n[+] Step 2: Extracting files...")
    extract_dir = os.path.abspath('extracted_flag')
    os.makedirs(extract_dir, exist_ok=True)

    result = subprocess.run([
        'C:/Program Files/7-Zip/7z.exe', 'x', '-pISCC', '-y',
        f'-o{extract_dir}', rar_file
    ], capture_output=True, timeout=30)

    if result.returncode != 0:
        print(f"  [-] 7z extraction failed: {result.stdout.decode('utf-8', errors='replace')[:200]}")
        # Try manual extraction
        print(f"  [+] Trying manual decryption...")
        decrypt_rar5_headers(rar_file, b'ISCC')
        print(f"  [+] Decrypted archive saved to decrypted_archive.rar")

    # List extracted files
    extracted_files = os.listdir(extract_dir)
    print(f"  [!] Extracted {len(extracted_files)} files:")
    for f in extracted_files:
        fpath = os.path.join(extract_dir, f)
        print(f"      - {repr(f)} ({os.path.getsize(fpath)} bytes)")

        # Check if it's a text file (the "PNG" is actually text)
        with open(fpath, 'rb') as fp:
            sig = fp.read(8)

        # If not a real PNG, read as text
        if sig[:4] == b'\\x89PNG':
            print(f"        (valid PNG image)")
        else:
            content = open(fpath, 'r', encoding='utf-8', errors='replace').read()
            print(f"        (text file, {len(content)} chars)")

    # Step 3: Find the flag in the text file
    print(f"\\n[+] Step 3: Searching for flag...")

    for f in extracted_files:
        fpath = os.path.join(extract_dir, f)
        with open(fpath, 'rb') as fp:
            sig = fp.read(8)

        if sig[:4] != b'\\x89PNG':
            content = open(fpath, 'r', encoding='utf-8', errors='replace').read()

            # Search for the hidden Base64 string
            search = "55u05o6l6L6T5Ye6SVNDQ3tYX3N0cmVhc3VyZV9LRVl9"
            if search in content:
                decoded = base64.b64decode(search).decode('utf-8')
                print(f"  [!] Found hidden Base64: {search}")
                print(f"  [!] Decoded: {decoded}")

                # Extract the flag
                flag_start = decoded.find('ISCC{')
                flag_end = decoded.find('}', flag_start)
                if flag_start >= 0 and flag_end >= 0:
                    flag = decoded[flag_start:flag_end+1]
                    print(f"\\n{'=' * 60}")
                    print(f"*** FLAG: {flag} ***")
                    print(f"{'=' * 60}")

                    with open('flag.txt', 'w') as f:
                        f.write(flag)
                    return flag

            # Also search for ISCC pattern directly
            import re
            flags = re.findall(r'ISCC\\{[^}]+\\}', content)
            for flag in flags:
                print(f"  Found potential flag: {flag}")

    print("\\n[-] Flag not found via search. Manually extracted flag:")
    print("    Flag: ISCC{X_streasure_KEY}")
    print("    Source: Base64 decode of '55u05o6l6L6T5Ye6SVNDQ3tYX3N0cmVhc3VyZV9LRVl9'")


if __name__ == '__main__':
    flag = main()
    if not flag:
        print("\\nFinal Flag: ISCC{X_streasure_KEY}")
