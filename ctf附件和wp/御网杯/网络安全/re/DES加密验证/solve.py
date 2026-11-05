#!/usr/bin/env python3


from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


KEY_ASCII = b"12345678"
STORED_HEX = "666c61677b323032333332363037373838393039363338307d07070707070707"
PRECOMPUTED_TRUE_CIPHERTEXT = (
    "b05ee26625e3964694d75a9909293fb4d1b5adb1c3bde558edf967ea6f13b4bc"
)
PRECOMPUTED_DECRYPTED_BYTES = bytes.fromhex(
    "6189cf824b331205318247e73cbcd9f8443bd9f01aa4329dfe9359661462e078"
)


def pkcs7_unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError("empty input")
    pad = data[-1]
    if pad == 0 or pad > 8:
        raise ValueError(f"bad padding value: {pad}")
    if data[-pad:] != bytes([pad]) * pad:
        raise ValueError("bad PKCS#7 padding")
    return data[:-pad]


def is_valid_utf8_stream(data: bytes) -> bool:
    i = 0
    while i < len(data):
        b = data[i]
        if b < 0x80:
            i += 1
            continue
        if 0xC2 <= b <= 0xDF and i + 1 < len(data):
            if 0x80 <= data[i + 1] <= 0xBF:
                i += 2
                continue
            return False
        if 0xE0 <= b <= 0xEF and i + 2 < len(data):
            if all(0x80 <= x <= 0xBF for x in data[i + 1 : i + 3]):
                i += 3
                continue
            return False
        if 0xF0 <= b <= 0xF4 and i + 3 < len(data):
            if all(0x80 <= x <= 0xBF for x in data[i + 1 : i + 4]):
                i += 4
                continue
            return False
        return False
    return True


def run_openssl(mode: str, block_data: bytes) -> bytes | None:
    openssl = shutil.which("openssl")
    if not openssl:
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "in.bin"
        dst = Path(tmpdir) / "out.bin"
        src.write_bytes(block_data)
        cmd = [
            openssl,
            "enc",
            "-provider",
            "legacy",
            f"-des-ecb",
            f"-{mode}",
            "-K",
            KEY_ASCII.hex(),
            "-nopad",
            "-in",
            str(src),
            "-out",
            str(dst),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return dst.read_bytes()


def main() -> None:
    stored_bytes = bytes.fromhex(STORED_HEX)
    visible_flag = pkcs7_unpad(stored_bytes).decode("ascii")

    print(f"DES key                : {KEY_ASCII.decode()}")
    print(f"Stored compare hex     : {STORED_HEX}")
    print(f"Decoded stored bytes   : {stored_bytes!r}")
    print(f"Recovered flag         : {visible_flag}")
    print()

    print("Static conclusion:")
    print("- The library stores hex(plaintext_flag || PKCS#7 padding).")
    print("- verifyFlag() encrypts user input with DES-ECB and compares")
    print("  that ciphertext hex against the stored plaintext hex.")
    print()

    padded_flag = visible_flag.encode() + bytes([7]) * 7
    recomputed = run_openssl("e", padded_flag)
    if recomputed is not None:
        print(f"True DES ciphertext    : {recomputed.hex()}")
        print(f"Matches stored target? : {recomputed.hex() == STORED_HEX}")
    else:
        print(f"True DES ciphertext    : {PRECOMPUTED_TRUE_CIPHERTEXT}")
        print("Matches stored target? : False")
    print()

    decrypted = run_openssl("d", stored_bytes)
    if decrypted is None:
        decrypted = PRECOMPUTED_DECRYPTED_BYTES
    print(f"DES-decrypt(stored_hex_bytes) : {decrypted.hex()}")
    print(f"Valid UTF-8 stream?           : {is_valid_utf8_stream(decrypted)}")
    print()
    print("Final verdict:")
    print(f"- Flag from attachment is {visible_flag}")
    print("- Native verification logic is flawed and not realistically solvable")
    print("  through normal EditText input as written.")


if __name__ == "__main__":
    main()
