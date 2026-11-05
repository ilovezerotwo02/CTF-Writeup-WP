from __future__ import annotations

from Crypto.Cipher import Blowfish


DEFAULT_KEY_HEX = "d1db19c8a2e38c60c1518b0301c8d7ea"
DEFAULT_CT_HEX = (
    "bdd6d58928d8b2427410d6a9a41f5ad6"
    "3c1ad4bfd555cc714d1615bb8931b48f"
    "7ff81240b075048ae644fe513b1120d7"
)


def from_hex(text: str) -> bytes:
    cleaned = "".join(text.split())
    return bytes.fromhex(cleaned)


def blowfish_ecb_decrypt(key: bytes, ciphertext: bytes) -> bytes:
    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    return cipher.decrypt(ciphertext)


def decode_flag(key_hex: str = DEFAULT_KEY_HEX, ct_hex: str = DEFAULT_CT_HEX) -> str:
    key = from_hex(key_hex)
    ciphertext = from_hex(ct_hex)
    plaintext = blowfish_ecb_decrypt(key, ciphertext)
    return plaintext.rstrip(b"\x00").decode("utf-8")


def show_material() -> None:
    print("algorithm : Blowfish-ECB")
    print(f"key(hex): {DEFAULT_KEY_HEX}")
    print(f"ct(hex): {DEFAULT_CT_HEX}")


def main() -> None:
    show_material()
    flag = decode_flag()
    print(f"flag: {flag}")


if __name__ == "__main__":
    main()
