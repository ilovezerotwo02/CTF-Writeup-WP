#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec


SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def load_challenge(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_int(message_hex: str) -> int:
    message = bytes.fromhex(message_hex)
    return int.from_bytes(hashlib.sha256(message).digest(), "big")


def recover_private_key(data: dict) -> tuple[int, int]:
    r = data["signature1_r"]
    s1 = data["signature1_s"]
    s2 = data["signature2_s"]
    z1 = sha256_int(data["message1"])
    z2 = sha256_int(data["message2"])

    k = ((z1 - z2) * pow((s1 - s2) % SECP256K1_N, -1, SECP256K1_N)) % SECP256K1_N
    d = ((s1 * k - z1) * pow(r, -1, SECP256K1_N)) % SECP256K1_N
    return k, d


def verify_public_key(private_key: int, data: dict) -> bool:
    private = ec.derive_private_key(private_key, ec.SECP256K1())
    public = private.public_key().public_numbers()
    return (
        public.x == data["public_key_x"]
        and public.y == data["public_key_y"]
    )


def build_candidates(private_key: int) -> dict[str, str]:
    priv_hex = format(private_key, "064x")
    priv_dec = str(private_key)
    priv_bytes = private_key.to_bytes(32, "big")
    return {
        "private_key_hex": priv_hex,
        "flag_if_direct_hex": f"flag{{ecdsa_nonce_reuse_{priv_hex}}}",
        "flag_if_md5_dec": f"flag{{ecdsa_nonce_reuse_{hashlib.md5(priv_dec.encode()).hexdigest()}}}",
        "flag_if_md5_hex": f"flag{{ecdsa_nonce_reuse_{hashlib.md5(priv_hex.encode()).hexdigest()}}}",
        "flag_if_md5_bytes": f"flag{{ecdsa_nonce_reuse_{hashlib.md5(priv_bytes).hexdigest()}}}",
        "flag_if_first_32_hex": f"flag{{ecdsa_nonce_reuse_{priv_hex[:32]}}}",
        "flag_if_last_32_hex": f"flag{{ecdsa_nonce_reuse_{priv_hex[-32:]}}}",
    }


def main() -> None:
    challenge_path = Path(__file__).with_name("challenge.json")
    data = load_challenge(challenge_path)
    k, private_key = recover_private_key(data)

    print(f"Recovered nonce k: {k}")
    print(f"Recovered private key (dec): {private_key}")
    print(f"Recovered private key (hex): {private_key:064x}")

    ok = verify_public_key(private_key, data)
    print(f"Public key verification: {ok}")
    if not ok:
        raise SystemExit("Recovered private key does not match the provided public key.")

    print("\nFlag candidates ranked by how directly they follow from the attachment:")
    for name, value in build_candidates(private_key).items():
        print(f"{name}: {value}")


if __name__ == "__main__":
    main()
