import argparse
import csv
import hashlib
import ipaddress
import re
import sqlite3
import time
from datetime import date, datetime
from pathlib import Path


HEADER = [
    "id",
    "username",
    "password",
    "name",
    "idcard",
    "phone",
    "email",
    "bankcard",
    "address",
    "ip",
    "birthday",
]

PHONE_PREFIXES = {
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
IDCARD_CHECK_MAP = "10X98765432"
EMAIL_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9_%+\-]*(?:\.[a-z0-9_%+\-]+)*)?@"
    r"[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?)+$"
)
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]+")
REFERENCE_DAY = date(2026, 5, 1)
BASE_DIR = Path(__file__).resolve().parent


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    if path.exists():
        return path.resolve()
    return BASE_DIR / path


def clean_text(value: str) -> str:
    return value.strip()


def mask_like_username(value: str) -> str:
    value = clean_text(value)
    if len(value) <= 1:
        return "*" * len(value)
    if len(value) == 2:
        return value[0] + "*"
    return value[0] + ("*" * (len(value) - 2)) + value[-1]


def md5_lower(value: str) -> str:
    return hashlib.md5(clean_text(value).encode("utf-8")).hexdigest()


def mask_name(value: str) -> str:
    value = clean_text(value)
    if len(value) < 2 or not CHINESE_RE.fullmatch(value):
        return "INVALID"
    if len(value) == 2:
        return value[0] + "*"
    return value[0] + ("*" * (len(value) - 2)) + value[-1]


def valid_idcard(value: str) -> bool:
    if not re.fullmatch(r"\d{17}[\dX]", value):
        return False
    try:
        datetime.strptime(value[6:14], "%Y%m%d")
    except ValueError:
        return False
    checksum = sum(int(num) * weight for num, weight in zip(value[:17], IDCARD_WEIGHTS))
    return IDCARD_CHECK_MAP[checksum % 11] == value[-1]


def mask_idcard(value: str) -> str:
    value = clean_text(value).upper()
    if not valid_idcard(value):
        return "INVALID"
    return "******" + value[6:10] + "********"


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", clean_text(value))
    if digits.startswith("0086") and len(digits) == 15:
        digits = digits[4:]
    elif digits.startswith("86") and len(digits) == 13:
        digits = digits[2:]
    return digits


def mask_phone(value: str) -> str:
    digits = normalize_phone(value)
    if len(digits) != 11 or not digits.isdigit() or digits[:3] not in PHONE_PREFIXES:
        return "INVALID"
    return digits[:3] + "****" + digits[7:]


def mask_email(value: str) -> str:
    value = clean_text(value).lower()
    if not EMAIL_RE.fullmatch(value):
        return "INVALID"
    local, domain = value.split("@", 1)
    return f"{mask_like_username(local)}@{domain}"


def normalize_bankcard(value: str) -> str:
    return re.sub(r"\D", "", clean_text(value))


def mask_bankcard(value: str) -> str:
    digits = normalize_bankcard(value)
    if not digits.isdigit() or not 16 <= len(digits) <= 19:
        return "INVALID"
    return digits[:6] + ("*" * (len(digits) - 10)) + digits[-4:]


def mask_address(value: str) -> str:
    value = clean_text(value)
    idx = value.find("号")
    if idx == -1:
        return "INVALID"
    return value[:idx] + "***"


def mask_ip(value: str) -> str:
    value = clean_text(value)
    try:
        ip = ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        return "INVALID"
    parts = str(ip).split(".")
    return ".".join(parts[:3] + ["*"])


def parse_birthday(value: str) -> date | None:
    value = clean_text(value)
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def mask_birthday(value: str) -> str:
    birthday = parse_birthday(value)
    if birthday is None or birthday > REFERENCE_DAY:
        return "INVALID"
    age = REFERENCE_DAY.year - birthday.year
    if (REFERENCE_DAY.month, REFERENCE_DAY.day) < (birthday.month, birthday.day):
        age -= 1
    if age < 0:
        return "INVALID"
    lower = (age // 10) * 10
    return f"{lower}-{lower + 9}"


def load_active_rows(sql_path: Path) -> list[sqlite3.Row]:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(sql_path.read_text(encoding="utf-8"))
    rows = conn.execute(
        """
        SELECT id, username, password, name, idcard, phone, email, bankcard, address, ip, birthday
        FROM user_export
        WHERE status = 'active'
        ORDER BY id ASC
        """
    ).fetchall()
    conn.close()
    return rows


def transform_row(row: sqlite3.Row) -> list[str]:
    return [
        str(row["id"]),
        mask_like_username(row["username"]),
        md5_lower(row["password"]),
        mask_name(row["name"]),
        mask_idcard(row["idcard"]),
        mask_phone(row["phone"]),
        mask_email(row["email"]),
        mask_bankcard(row["bankcard"]),
        mask_address(row["address"]),
        mask_ip(row["ip"]),
        mask_birthday(row["birthday"]),
    ]


def write_csv(rows: list[list[str]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(rows)


def compare_csv(expected_path: Path, actual_path: Path) -> int:
    with expected_path.open(encoding="utf-8", newline="") as expected_handle:
        expected_rows = list(csv.reader(expected_handle))
    with actual_path.open(encoding="utf-8", newline="") as actual_handle:
        actual_rows = list(csv.reader(actual_handle))

    mismatches = 0
    limit = min(len(expected_rows), len(actual_rows))
    for index in range(limit):
        if expected_rows[index] != actual_rows[index]:
            mismatches += 1
            print(f"Line {index + 1} mismatch")
            print("  expected:", expected_rows[index])
            print("  actual  :", actual_rows[index])
    if len(expected_rows) != len(actual_rows):
        print(f"Row count differs: expected {len(expected_rows)}, actual {len(actual_rows)}")
    return mismatches


def fetch_captcha(base_url: str, save_path: Path) -> str:
    import requests

    session = requests.Session()
    session.get(f"{base_url}/api/captcha", timeout=30)
    response = session.get(f"{base_url}/api/captcha?ts={int(time.time() * 1000)}", timeout=30)
    response.raise_for_status()
    save_path.write_bytes(response.content)
    return session.cookies.get("session", "")


def submit_csv(base_url: str, csv_path: Path, captcha: str, session_cookie: str) -> dict:
    import requests

    session = requests.Session()
    if session_cookie:
        session.cookies.set("session", session_cookie)

    with csv_path.open("rb") as handle:
        response = session.post(
            f"{base_url}/api/upload",
            files={"file": (csv_path.name, handle, "text/csv")},
            data={"captcha": captcha},
            timeout=60,
        )
    response.raise_for_status()
    payload = response.json()
    if payload.get("state") == -1:
        raise RuntimeError(payload.get("reason", "upload failed"))

    key = payload["key"]
    for _ in range(180):
        status = session.get(f"{base_url}/api/status/{key}", timeout=30)
        status.raise_for_status()
        result = status.json()
        if result.get("state") == 1:
            return result
        time.sleep(2)
    raise TimeoutError("submission did not finish within the polling window")


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve the MaskTrace data masking challenge.")
    parser.add_argument("--sql", default=r"payload\MaskTrace附件\user_export.sql", help="Path to user_export.sql")
    parser.add_argument("--output", default="masktrace_answer.csv", help="Path to the output CSV file")
    parser.add_argument(
        "--compare",
        default="",
        help="Optional path to a reference CSV for comparison",
    )
    parser.add_argument(
        "--base-url",
        default="http://120.27.146.76:40197",
        help="Checker platform base URL",
    )
    parser.add_argument(
        "--fetch-captcha",
        action="store_true",
        help="Fetch a fresh captcha image and save its session cookie",
    )
    parser.add_argument(
        "--captcha-path",
        default="captcha.png",
        help="Where to save the fetched captcha image",
    )
    parser.add_argument(
        "--session-cookie-path",
        default="session_cookie.txt",
        help="Where to save or load the checker session cookie",
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Submit the generated CSV to the checker platform",
    )
    parser.add_argument(
        "--captcha",
        default="",
        help="Captcha text used when submitting the CSV",
    )
    args = parser.parse_args()

    sql_path = resolve_path(args.sql)
    output_path = resolve_path(args.output)
    captcha_path = resolve_path(args.captcha_path)
    session_cookie_path = resolve_path(args.session_cookie_path)

    rows = [transform_row(row) for row in load_active_rows(sql_path)]
    write_csv(rows, output_path)
    print(f"Wrote {len(rows)} active rows to {output_path}")

    if args.compare:
        mismatches = compare_csv(resolve_path(args.compare), output_path)
        if mismatches:
            print(f"Comparison finished with {mismatches} mismatches")
        else:
            print("Comparison finished with no mismatches")

    if args.fetch_captcha:
        session_cookie = fetch_captcha(args.base_url, captcha_path)
        session_cookie_path.write_text(session_cookie, encoding="utf-8")
        print(f"Saved captcha image to {captcha_path}")
        print(f"Saved session cookie to {session_cookie_path}")

    if args.submit:
        if not args.captcha:
            raise SystemExit("--submit requires --captcha")
        session_cookie = ""
        if session_cookie_path.exists():
            session_cookie = session_cookie_path.read_text(encoding="utf-8").strip()
        result = submit_csv(args.base_url, output_path, args.captcha, session_cookie)
        print(result)


if __name__ == "__main__":
    main()
