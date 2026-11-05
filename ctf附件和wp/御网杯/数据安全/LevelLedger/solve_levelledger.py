from __future__ import annotations

import base64
import csv
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA


ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "tempdir" / "inner" / "LevelLedger附件"
INPUT_CSV = INPUT_DIR / "mixed_data.csv"
PRIVATE_KEY = INPUT_DIR / "leaked_private.pem"
OUTPUT_CSV = ROOT / "classified_data.csv"

RSA_BASE64_RE = re.compile(r"^[A-Za-z0-9+/=]{344}$")
DIGITISH_RE = re.compile(r"^[+\dXx\s-]+$")
TEXT_WITH_GAPS_RE = re.compile(r"[A-WYZa-wyz]")
VALID_PHONE_PREFIXES = {
    "134",
    "135",
    "136",
    "137",
    "138",
    "139",
    "147",
    "148",
    "150",
    "151",
    "152",
    "157",
    "158",
    "159",
    "172",
    "178",
    "182",
    "183",
    "184",
    "187",
    "188",
    "195",
    "198",
    "130",
    "131",
    "132",
    "140",
    "145",
    "146",
    "155",
    "156",
    "166",
    "167",
    "171",
    "175",
    "176",
    "185",
    "186",
    "196",
    "133",
    "149",
    "153",
    "173",
    "174",
    "177",
    "180",
    "181",
    "189",
    "190",
    "191",
    "193",
    "199",
}
IDCARD_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
IDCARD_CHECKMAP = "10X98765432"


def load_cipher() -> PKCS1_OAEP.PKCS1OAEP_Cipher:
    key = RSA.import_key(PRIVATE_KEY.read_bytes())
    return PKCS1_OAEP.new(key, hashAlgo=SHA256)


def maybe_decrypt(value: str, cipher: PKCS1_OAEP.PKCS1OAEP_Cipher) -> str:
    if not RSA_BASE64_RE.fullmatch(value):
        return value
    plaintext = cipher.decrypt(base64.b64decode(value))
    return plaintext.decode("utf-8")


def normalize_value(raw_value: str, cipher: PKCS1_OAEP.PKCS1OAEP_Cipher) -> str:
    value = maybe_decrypt(raw_value, cipher)
    value = unicodedata.normalize("NFKC", value).strip()
    if DIGITISH_RE.fullmatch(value):
        value = re.sub(r"[\s-]+", "", value)
        if value.startswith("+86"):
            value = value[3:]
        elif value.startswith("0086"):
            value = value[4:]
        value = value.upper()
    return value


def normalize_output_value(raw_value: str, cipher: PKCS1_OAEP.PKCS1OAEP_Cipher) -> str:
    raw_plain = unicodedata.normalize("NFKC", maybe_decrypt(raw_value, cipher)).strip()
    normalized = normalize_value(raw_value, cipher)
    if ("-" in raw_plain or any(ch.isspace() for ch in raw_plain)) and TEXT_WITH_GAPS_RE.search(raw_plain):
        return re.sub(r"[\s-]+", "", raw_plain)
    return normalized


def valid_date_yyyymmdd(date_text: str) -> bool:
    if len(date_text) != 8 or not date_text.isdigit():
        return False
    year = int(date_text[:4])
    if year < 1900 or year > 2030:
        return False
    try:
        datetime.strptime(date_text, "%Y%m%d")
    except ValueError:
        return False
    return True


def is_idcard(value: str) -> bool:
    if not re.fullmatch(r"\d{17}[\dX]", value):
        return False
    if not valid_date_yyyymmdd(value[6:14]):
        return False
    checksum = sum(int(num) * weight for num, weight in zip(value[:17], IDCARD_WEIGHTS))
    return value[-1] == IDCARD_CHECKMAP[checksum % 11]


def is_bankcard(value: str) -> bool:
    if not re.fullmatch(r"\d{16,19}", value):
        return False
    total = 0
    reverse_digits = value[::-1]
    for index, char in enumerate(reverse_digits, start=1):
        digit = int(char)
        if index % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def is_phone(value: str) -> bool:
    return len(value) == 11 and value.isdigit() and value[:3] in VALID_PHONE_PREFIXES


def is_ip(value: str) -> bool:
    if not re.fullmatch(r"[0-9.]+", value):
        return False
    parts = value.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part:
            return False
        if len(part) > 1 and part[0] == "0":
            return False
        try:
            number = int(part)
        except ValueError:
            return False
        if number < 0 or number > 255:
            return False
    return True


def classify(value: str) -> tuple[str, str]:
    if is_idcard(value):
        return "idcard", "S4"
    if is_bankcard(value):
        return "bankcard", "S4"
    if is_phone(value):
        return "phone", "S3"
    if is_ip(value):
        return "ip", "S2"
    return "normal", "S1"


def main() -> None:
    cipher = load_cipher()
    with INPUT_CSV.open("r", encoding="utf-8", newline="") as src:
        rows = list(csv.DictReader(src))

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=["data_id", "value", "category", "level"])
        writer.writeheader()
        for row in rows:
            normalized = normalize_value(row["value"], cipher)
            output_value = normalize_output_value(row["value"], cipher)
            category, level = classify(normalized)
            writer.writerow(
                {
                    "data_id": row["data_id"],
                    "value": output_value,
                    "category": category,
                    "level": level,
                }
            )


if __name__ == "__main__":
    main()
