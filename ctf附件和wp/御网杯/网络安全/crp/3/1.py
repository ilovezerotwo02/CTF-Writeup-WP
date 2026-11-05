#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import sys


CURVES = {
    "SECP256k1": {
        "p": 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
        "n": 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141,
        "gx": 55066263022277343669578718895168534326250603453777594175500187360389116729240,
        "gy": 32670510020758816978083085130507043184471273380659243275938904335757337482424,
    }
}

REQUIRED_FIELDS = {
    "curve",
    "signature1_r",
    "signature1_s",
    "signature2_r",
    "signature2_s",
    "message1",
    "message2",
    "public_key_x",
    "public_key_y",
}


def mod_inv(value: int, modulus: int) -> int:
    return pow(value, -1, modulus)


def point_add(p1, p2, p):
    if p1 is None:
        return p2
    if p2 is None:
        return p1

    x1, y1 = p1
    x2, y2 = p2

    if x1 == x2 and (y1 + y2) % p == 0:
        return None

    if p1 == p2:
        slope = (3 * x1 * x1) * mod_inv((2 * y1) % p, p) % p
    else:
        slope = (y2 - y1) * mod_inv((x2 - x1) % p, p) % p

    x3 = (slope * slope - x1 - x2) % p
    y3 = (slope * (x1 - x3) - y1) % p
    return x3, y3


def scalar_mult(k: int, point, p: int):
    result = None
    addend = point
    while k:
        if k & 1:
            result = point_add(result, addend, p)
        addend = point_add(addend, addend, p)
        k >>= 1
    return result


def hash_message(message_hex: str) -> int:
    return int.from_bytes(hashlib.sha256(bytes.fromhex(message_hex)).digest(), "big")


def recover_private_key(challenge: dict) -> dict:
    curve_name = challenge["curve"]
    if curve_name not in CURVES:
        raise ValueError(f"unsupported curve: {curve_name}")

    curve = CURVES[curve_name]
    n = curve["n"]
    p = curve["p"]
    g = (curve["gx"], curve["gy"])

    r1 = int(challenge["signature1_r"])
    r2 = int(challenge["signature2_r"])
    s1 = int(challenge["signature1_s"])
    s2 = int(challenge["signature2_s"])

    if r1 != r2:
        raise ValueError("nonce reuse not detected: signature1_r != signature2_r")

    z1 = hash_message(challenge["message1"])
    z2 = hash_message(challenge["message2"])

    k = ((z1 - z2) * mod_inv((s1 - s2) % n, n)) % n
    d = ((s1 * k - z1) * mod_inv(r1, n)) % n

    public_key = scalar_mult(d, g, p)
    expected_public_key = (int(challenge["public_key_x"]), int(challenge["public_key_y"]))
    public_key_ok = public_key == expected_public_key

    return {
        "curve": curve_name,
        "k": k,
        "private_key": d,
        "private_key_hex": f"{d:064x}",
        "public_key_ok": public_key_ok,
        "flag": f"flag{{ecdsa_nonce_reuse_{d:064x}}}",
    }


def looks_like_challenge_file(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return isinstance(data, dict) and REQUIRED_FIELDS.issubset(data.keys())


def iter_challenge_files(target: Path):
    if target.is_file():
        if target.suffix.lower() == ".json" and looks_like_challenge_file(target):
            yield target
        else:
            raise ValueError(f"unsupported or invalid challenge file: {target}")
        return

    if not target.is_dir():
        raise ValueError(f"path not found: {target}")

    challenge_jsons = sorted(target.rglob("challenge.json"))
    other_jsons = sorted(p for p in target.rglob("*.json") if p.name != "challenge.json")

    files = [p for p in challenge_jsons if looks_like_challenge_file(p)]
    files.extend(p for p in other_jsons if looks_like_challenge_file(p))

    if not files:
        raise ValueError(
            "no valid challenge json found under: "
            f"{target} (expected fields: {', '.join(sorted(REQUIRED_FIELDS))})"
        )
    yield from files


def main():
    parser = argparse.ArgumentParser(description="Recover ECDSA private key from nonce reuse.")
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="challenge.json path or directory containing challenge.json files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON results",
    )
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    results = []

    try:
        challenge_files = list(iter_challenge_files(target))
    except ValueError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        print("[!] Put a valid challenge .json in the directory, or pass its path explicitly.", file=sys.stderr)
        raise SystemExit(1)

    for challenge_file in challenge_files:
        challenge = json.loads(challenge_file.read_text(encoding="utf-8"))
        result = recover_private_key(challenge)
        result["file"] = str(challenge_file)
        results.append(result)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    for result in results:
        print(f"[+] file: {result['file']}")
        print(f"    curve: {result['curve']}")
        print(f"    k: {result['k']}")
        print(f"    private_key: {result['private_key']}")
        print(f"    private_key_hex: {result['private_key_hex']}")
        print(f"    public_key_ok: {result['public_key_ok']}")
        print(f"    flag: {result['flag']}")


if __name__ == "__main__":
    main()
