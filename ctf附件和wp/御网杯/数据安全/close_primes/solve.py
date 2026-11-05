from pathlib import Path
import math

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.number import inverse


BASE_DIR = Path(__file__).resolve().parent
TASK_DIR = BASE_DIR / "work" / "task"
PUBKEY_PATH = TASK_DIR / "pubkey.pem"
ENCRYPTED_PATH = TASK_DIR / "encrypted.bin"
OUTPUT_PATH = TASK_DIR / "recovered.png"


def fermat_factor(n: int) -> tuple[int, int]:
    a = math.isqrt(n)
    if a * a < n:
        a += 1
    while True:
        b2 = a * a - n
        b = math.isqrt(b2)
        if b * b == b2:
            return a - b, a + b
        a += 1


def main() -> None:
    pub = RSA.import_key(PUBKEY_PATH.read_bytes())
    n, e = pub.n, pub.e
    p, q = fermat_factor(n)
    phi = (p - 1) * (q - 1)
    d = inverse(e, phi)
    priv = RSA.construct((n, e, d, p, q))

    ciphertext = ENCRYPTED_PATH.read_bytes()
    block_size = pub.size_in_bytes()
    blocks = [
        ciphertext[i:i + block_size]
        for i in range(0, len(ciphertext), block_size)
    ]

    plaintext = b"".join(PKCS1_OAEP.new(priv).decrypt(block) for block in blocks)
    OUTPUT_PATH.write_bytes(plaintext)

    print(f"p = {p}")
    print(f"q = {q}")
    print(f"blocks = {len(blocks)}")
    print(f"recovered = {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
