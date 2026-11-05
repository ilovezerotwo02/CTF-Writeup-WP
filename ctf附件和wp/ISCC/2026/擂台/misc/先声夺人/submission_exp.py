from __future__ import annotations

import hashlib
import json
import zlib
from itertools import count
from pathlib import Path

from Cryptodome.Cipher import AES


ZERO_WIDTH_DIGITS = {
    0x200B: "0",
    0x200C: "1",
    0x200D: "2",
    0xFEFF: "3",
}


def collect_hidden_digits(text: str) -> str:
    return "".join(ZERO_WIDTH_DIGITS[ord(ch)] for ch in text if ord(ch) in ZERO_WIDTH_DIGITS)


def decode_base4_stream(digits: str) -> bytes:
    groups = (digits[i:i + 4] for i in range(0, len(digits), 4))
    return bytes(int(group, 4) for group in groups if len(group) == 4)


def unpack_config(path: str = "challenge.txt") -> dict:
    source = Path(path).read_text(encoding="utf-8")
    digit_stream = collect_hidden_digits(source)
    raw_bytes = decode_base4_stream(digit_stream)
    return json.loads(zlib.decompress(raw_bytes[4:]))


def leading_zero_bits_ok(digest: bytes, wanted_bits: int) -> bool:
    zero_bytes, tail_bits = divmod(wanted_bits, 8)
    if any(digest[index] != 0 for index in range(zero_bytes)):
        return False
    if tail_bits == 0:
        return True
    return digest[zero_bytes] < (1 << (8 - tail_bits))


def mine_pow_value(nonce: str, difficulty_bits: int) -> tuple[int, str]:
    prefix = nonce.encode("utf-8")
    for counter in count():
        digest = hashlib.sha256(prefix + str(counter).encode("utf-8")).digest()
        if leading_zero_bits_ok(digest, difficulty_bits):
            return counter, digest.hex()


def pkcs7_unpad(block: bytes) -> bytes:
    pad = block[-1]
    if pad == 0 or pad > 16 or block[-pad:] != bytes([pad]) * pad:
        raise ValueError("invalid pkcs7 padding")
    return block[:-pad]


def recover_flag(config: dict, counter: int) -> tuple[str, str]:
    nonce = config["nonce"].encode("utf-8")
    key = hashlib.pbkdf2_hmac(
        "sha256",
        str(counter).encode("utf-8"),
        nonce,
        config["key_derivation"]["iterations"],
        dklen=config["key_derivation"]["dklen"],
    )
    iv = bytes.fromhex(config["encrypted_flag"]["iv"])
    ciphertext = bytes.fromhex(config["encrypted_flag"]["ciphertext"])
    plaintext = AES.new(key, AES.MODE_CBC, iv).decrypt(ciphertext)
    return key.hex(), pkcs7_unpad(plaintext).decode("utf-8")


def main() -> None:
    config = unpack_config()
    counter, digest_hex = mine_pow_value(config["nonce"], config["difficulty_bits"])
    key_hex, flag = recover_flag(config, counter)

    print("[config]")
    print(json.dumps(config, ensure_ascii=False, indent=2))
    print()
    print("[pow]")
    print(f"counter = {counter}")
    print(f"sha256  = {digest_hex}")
    print()
    print("[decrypt]")
    print(f"key  = {key_hex}")
    print(f"flag = {flag}")


if __name__ == "__main__":
    main()
