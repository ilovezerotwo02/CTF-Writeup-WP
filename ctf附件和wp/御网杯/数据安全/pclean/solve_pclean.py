import csv
import re
import sqlite3
from pathlib import Path


PREFIXES = {
    "130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
    "140", "145", "146", "147", "148", "149", "150", "151", "152", "153",
    "155", "156", "157", "158", "159", "166", "167", "171", "172", "173",
    "174", "175", "176", "177", "178", "180", "181", "182", "183", "184",
    "185", "186", "187", "188", "189", "190", "191", "193", "195", "196",
    "198", "199",
}
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
NAME_RE = re.compile(r"^[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]+$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_GENDERS = {"男", "女"}
HEADERS = ["id", "username", "name", "phone", "email", "gender"]


def is_dirty(row: tuple[int, str, str, str, str, str]) -> bool:
    _, username, name, phone, email, gender = row
    return not (
        USERNAME_RE.fullmatch(username or "")
        and NAME_RE.fullmatch(name or "")
        and re.fullmatch(r"\d{11}", phone or "")
        and phone[:3] in PREFIXES
        and EMAIL_RE.fullmatch(email or "")
        and gender in VALID_GENDERS
    )


def main() -> None:
    base_dir = Path(__file__).resolve().parent / "unzipped2" / "pclean的附件"
    db_path = base_dir / "user_data.db"
    out_path = base_dir / "dirty_data.csv"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id, username, name, phone, email, gender "
        "FROM insurance_users ORDER BY id"
    ).fetchall()
    conn.close()

    dirty_rows = [row for row in rows if is_dirty(row)]

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)
        writer.writerows(dirty_rows)

    print(f"dirty rows: {len(dirty_rows)}")
    print(out_path)


if __name__ == "__main__":
    main()
