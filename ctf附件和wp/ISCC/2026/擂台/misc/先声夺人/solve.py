import hashlib
import json
import time
import zlib
from pathlib import Path

from Cryptodome.Cipher import AES
from Cryptodome.Hash import SHA256
from Cryptodome.Protocol.KDF import PBKDF2
from Cryptodome.Util.Padding import unpad


ZERO_WIDTH_MAP = {
    "\u200b": "0",
    "\u200c": "1",
    "\u200d": "2",
    "\ufeff": "3",
}


def extract_payload(path: str = "challenge.txt") -> dict:
    text = Path(path).read_text("utf-8")
    hidden = "".join(ch for ch in text if ch in ZERO_WIDTH_MAP)
    digits = "".join(ZERO_WIDTH_MAP[ch] for ch in hidden)
    data = bytes(int(digits[i:i + 4], 4) for i in range(0, len(digits), 4))
    return json.loads(zlib.decompress(data[4:]))


def has_leading_zero_bits(digest: bytes, difficulty_bits: int) -> bool:
    zero_bytes = difficulty_bits // 8
    remain_bits = difficulty_bits % 8
    if digest[:zero_bytes] != b"\x00" * zero_bytes:
        return False
    if remain_bits == 0:
        return True
    mask = (0xFF << (8 - remain_bits)) & 0xFF
    return (digest[zero_bytes] & mask) == 0


def solve_pow(nonce: str, difficulty_bits: int) -> tuple[int, str]:
    nonce_bytes = nonce.encode()
    s = 0
    while True:
        digest = hashlib.sha256(nonce_bytes + str(s).encode()).digest()
        if has_leading_zero_bits(digest, difficulty_bits):
            return s, digest.hex()
        s += 1


def decrypt_flag(payload: dict, s_value: int) -> str:
    nonce = payload["nonce"].encode()
    key = PBKDF2(
        str(s_value).encode(),
        nonce,
        dkLen=payload["key_derivation"]["dklen"],
        count=payload["key_derivation"]["iterations"],
        hmac_hash_module=SHA256,
    )
    iv = bytes.fromhex(payload["encrypted_flag"]["iv"])
    ciphertext = bytes.fromhex(payload["encrypted_flag"]["ciphertext"])
    plaintext = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ciphertext), 16)
    return plaintext.decode()


def main() -> None:
    payload = extract_payload()

    start = time.time()
    s_value, digest_hex = solve_pow(payload["nonce"], payload["difficulty_bits"])
    elapsed = time.time() - start

    flag = decrypt_flag(payload, s_value)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"pow_s: {s_value}")
    print(f"pow_hash: {digest_hex}")
    print(f"elapsed: {elapsed:.2f}s")
    print(f"flag: {flag}")


if __name__ == "__main__":
    main()
