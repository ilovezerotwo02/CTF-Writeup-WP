---
title: "exam_system"
ctf: "unknown"
date: 2026-05-31
category: forensics
difficulty: easy
points: 300
flag_format: "flag{...}"
author: "Codex"
---

# exam_system

## 题目概述

题目给了一个 SQLite 数据库备份和一份《安全审计规范》。解题思路是先按照规范校验 `idcard` 和 `phone`，找出所有“幽灵账户”，排除这些用户的访问日志后，再对剩余日志按最小违规类型编号进行判定，最后将升序排列后的 `日志ID-类型编号` 字符串做 MD5，得到最终 flag。

### 第一步：阅读规范并确定校验规则

审计规范里有两层关键规则：

- 幽灵账户：`idcard` 或 `phone` 任一校验不通过的用户。
- 违规类型：
  - `1`：用户状态为 `inactive` 但仍有访问记录
  - `2`：访问时间不在 `09:00:00-18:00:00` 内
  - `3`：用户角色对该 API 没有访问权限
- 若同一条日志同时命中多种违规类型，只记录最小的类型编号。

其中身份证需要做这几项校验：

- 格式必须是 `17 位数字 + 1 位数字或 X`
- 出生日期字段必须能解析为合法日期 `YYYYMMDD`
- 最后一位校验码要满足加权校验规则，权重为 `7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2`

手机号校验规则是：

- 必须恰好为 11 位数字
- 前 3 位必须属于题目给定的合法号段集合

### 第二步：编写脚本遍历数据库

下面这段脚本可以从数据库直接算出最终结果：

```python
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
    0: "1", 1: "0", 2: "X", 3: "9", 4: "8", 5: "7",
    6: "6", 7: "5", 8: "4", 9: "3", 10: "2",
}


def find_db_path() -> Path:
    for candidate in DB_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not locate exam_system.db")


def valid_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"\d{11}", phone)) and phone[:3] in PHONE_PREFIXES


def valid_idcard(idcard: str) -> bool:
    if not re.fullmatch(r"\d{17}[\dX]", idcard):
        return False
    try:
        dt.datetime.strptime(idcard[6:14], "%Y%m%d")
    except ValueError:
        return False
    total = sum(int(n) * w for n, w in zip(idcard[:17], IDCARD_WEIGHTS))
    return IDCARD_CHECKSUM[total % 11] == idcard[-1]


conn = sqlite3.connect(find_db_path())
cur = conn.cursor()

users = {
    row[0]: {
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
    types = []

    if user["status"] == "inactive":
        types.append(1)
    if access_time.split()[1] < "09:00:00" or access_time.split()[1] > "18:00:00":
        types.append(2)
    if permissions.get((user["role_id"], api_endpoint), 0) != 1:
        types.append(3)

    if types:
        violations.append(f"{log_id}-{min(types)}")

joined = ",".join(violations)
print("ghost users:", sorted(ghost_users))
print("violations:", joined)
print("flag{" + hashlib.md5(joined.encode()).hexdigest() + "}")
```

脚本跑出的关键结果如下：

- 幽灵账户用户 ID：
  `3,12,16,31,34,40,43,44,63,68,72,78,80,85,88,92,112,128,132,133,134,151,160,165,172,179,186,188,192,195`
- 排除幽灵账户后的违规记录：
  `14728-3,24311-1,30736-1,38039-2,40118-2,41610-1,47445-3,60354-2,76513-1`

## 最终答案

```text
flag{15cb6dceb13da3077c6df3f86d219e9d}
```
