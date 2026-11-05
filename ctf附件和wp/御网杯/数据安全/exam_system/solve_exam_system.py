import datetime as dt
import hashlib
import re
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_CANDIDATES = [
    BASE_DIR / "tempdir" / "payload" / "exam_system的附件" / "exam_system.db",
    BASE_DIR / "exam_system.db",
    Path(r"C:\temp\exam_tmp\exam_system.db"),
]

PHONE_PREFIXES = {
    "130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
    "140", "145", "146", "147", "148", "149", "150", "151", "152", "153",
    "155", "156", "157", "158", "159", "166", "167", "171", "172", "173",
    "174", "175", "176", "177", "178", "180", "181", "182", "183", "184",
    "185", "186", "187", "188", "189", "190", "191", "193", "195", "196",
    "198", "199",
}
IDCARD_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
IDCARD_CHECKSUM = {
    0: "1",
    1: "0",
    2: "X",
    3: "9",
    4: "8",
    5: "7",
    6: "6",
    7: "5",
    8: "4",
    9: "3",
    10: "2",
}


def valid_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"\d{11}", phone)) and phone[:3] in PHONE_PREFIXES


def valid_idcard(idcard: str) -> bool:
    if not re.fullmatch(r"\d{17}[\dX]", idcard):
        return False

    try:
        dt.datetime.strptime(idcard[6:14], "%Y%m%d")
    except ValueError:
        return False

    total = sum(int(num) * weight for num, weight in zip(idcard[:17], IDCARD_WEIGHTS))
    return IDCARD_CHECKSUM[total % 11] == idcard[-1]


def find_db_path() -> Path:
    for candidate in DB_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not locate exam_system.db")


def main() -> None:
    conn = sqlite3.connect(find_db_path())
    cur = conn.cursor()

    users = {
        row[0]: {
            "username": row[1],
            "idcard": row[4],
            "phone": row[5],
            "role_id": row[6],
            "status": row[7],
        }
        for row in cur.execute("SELECT * FROM users")
    }
    permissions = {
        (row[1], row[2]): row[3]
        for row in cur.execute("SELECT * FROM api_permissions")
    }

    ghost_users = {
        user_id
        for user_id, user in users.items()
        if not valid_idcard(user["idcard"]) or not valid_phone(user["phone"])
    }

    violations = []
    for log_id, user_id, api_endpoint, access_time in cur.execute(
        "SELECT id, user_id, api_endpoint, access_time FROM access_logs ORDER BY id"
    ):
        if user_id in ghost_users:
            continue

        user = users[user_id]
        violation_types = []

        if user["status"] == "inactive":
            violation_types.append(1)

        access_clock = access_time.split()[1]
        if access_clock < "09:00:00" or access_clock > "18:00:00":
            violation_types.append(2)

        if permissions.get((user["role_id"], api_endpoint), 0) != 1:
            violation_types.append(3)

        if violation_types:
            violations.append(f"{log_id}-{min(violation_types)}")

    joined = ",".join(violations)
    flag = hashlib.md5(joined.encode()).hexdigest()

    print("ghost_user_ids =", sorted(ghost_users))
    print("violations =", joined)
    print(f"flag{{{flag}}}")


if __name__ == "__main__":
    main()
