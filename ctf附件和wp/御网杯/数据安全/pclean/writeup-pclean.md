---
title: "pclean"
ctf: "未知赛事"
date: 2026-05-31
category: misc
difficulty: easy
points: 150
flag_format: "flag{...}"
author: "Codex"
---

# pclean

## Summary

题目给了一个 SQLite 数据库和一份字段规范文档，要求筛出所有不符合规范的脏数据，并按示例 `csv` 格式提交到校验平台。核心就是把 5 个字段的校验规则准确翻译成脚本，然后导出所有脏记录。

## Solution

### Step 1: 提炼字段校验规则

规范文档里的规则如下：

- `username` 只能由大小写字母、数字和下划线组成
- `name` 只能由中文字符组成
- `phone` 必须是 11 位数字，且前三位必须属于题目给定号段
- `email` 必须包含且只包含一个 `@`，`@` 前后都要有内容，并且域名部分要带后缀
- `gender` 只能是 `男` 或 `女`

平台示例文件可从 `/api/download_example_file` 下载，格式为：

```csv
id,username,name,phone,email,gender
2,tomcatKingkk,,13672726827,@126.com,b
3,sk8uDpbRABFy28Xw153V,晏修真,1381520457e,sk8uDpbRABFy28Xw153V@126,p
```

这说明提交内容不是“错误字段列表”，而是“整行脏数据”。

### Step 2: 导出脏数据并提交

下面脚本会读取 `user_data.db`，筛出所有不符合规范的记录，并生成 UTF-8 编码的 `dirty_data.csv`：

```python
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


def is_dirty(row):
    _, username, name, phone, email, gender = row
    return not (
        USERNAME_RE.fullmatch(username or "")
        and NAME_RE.fullmatch(name or "")
        and re.fullmatch(r"\d{11}", phone or "")
        and phone[:3] in PREFIXES
        and EMAIL_RE.fullmatch(email or "")
        and gender in VALID_GENDERS
    )


base_dir = Path("D:/桌面/yuwang/数据安全/pclean/unzipped2/pclean的附件")
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

print(len(dirty_rows))
print(out_path)
```

实际跑出来脏数据一共 `934` 条，上传后平台返回 `100.000%`。

## Flag

```text
flag{9d4c2f88e16b70a5c39f1e27bd84c610}
```
