---
title: "TracePurge"
ctf: "Unknown"
date: 2026-05-31
category: forensics
difficulty: easy
points: 300
flag_format: "flag{...}"
author: "OpenAI Codex"
---

# TracePurge

## Summary

题目给了外部泄露样本、内部导出日志、外发检测日志和客户索引。核心是先定位真正发生外传的导出任务，再按题面规则把样本映射到唯一客户主体，最后生成 `response_plan.csv` 并上传校验。

## Solution

### Step 1: 定位对应的内部导出任务

把 `export_log.csv` 和 `transfer_log.csv` 关联后，只需要关注 `status=success` 且 `event=external_upload` 的任务。

- `EX20260508003 / CRM-20260508-D3` 虽然是 `external_upload`，但导出状态是 `failed`
- `EX20260508004 / CRM-20260508-D4` 是 `success + external_upload`
- `leak_sample.csv` 中绝大多数样本的 `batch_tag` 也都是 `CRM-20260508-D4`，共有 1540 行

因此本次事件对应的内部导出任务就是：

```text
export_id = EX20260508004
operator  = ops_chen
batch_tag = CRM-20260508-D4
```

### Step 2: 按题面规则匹配客户主体并生成提交文件

匹配规则：

1. 若样本行 `email` 非空，计算 `sha256(lower(strip(email)))`，优先匹配 `customer_index.csv.email_hash`
2. 若邮箱为空或哈希未命中，再用 `name + phone_mask` 兜底
3. 只保留能够唯一匹配到的主体
4. 只保留 `batch_tag == CRM-20260508-D4` 的样本
5. 同一 `subject_id` 若出现多次，只保留 `leak_id` 最小的一行
6. `erase_requested == true` -> `PURGE`
7. 否则若 `risk == high` -> `NOTIFY`
8. 其他 -> `MONITOR`

最终生成 `1200` 行提交数据。

```python
import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(r"D:\桌面\yuwang\数据安全\TracePurge\tempdir\tracepurge\inner\TracePurge附件")

def read_csv(name):
    with (BASE / name).open("r", encoding="utf-8", newline="") as fh:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(fh)]

def sha256_hex(value):
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()

def action_for(row):
    if row["erase_requested"] == "true":
        return "PURGE"
    if row["risk"] == "high":
        return "NOTIFY"
    return "MONITOR"

export_rows = read_csv("export_log.csv")
transfer_rows = read_csv("transfer_log.csv")
leak_rows = read_csv("leak_sample.csv")
customer_rows = read_csv("customer_index.csv")

email_map = defaultdict(list)
name_phone_map = defaultdict(list)
for row in customer_rows:
    if row["email_hash"]:
        email_map[row["email_hash"]].append(row)
    name_phone_map[(row["name"], row["phone_mask"])].append(row)

matched_rows = []
for row in leak_rows:
    subject = None
    if row["email"]:
        hits = email_map.get(sha256_hex(row["email"]), [])
        if len(hits) == 1:
            subject = hits[0]
    if subject is None:
        hits = name_phone_map.get((row["name"], row["phone_mask"]), [])
        if len(hits) == 1:
            subject = hits[0]
    if subject is not None:
        matched_rows.append({
            "leak_id": row["leak_id"],
            "batch_tag": row["batch_tag"],
            "subject_id": subject["subject_id"],
            "action": action_for(subject),
        })

leak_count_by_batch = Counter(row["batch_tag"] for row in leak_rows)
matched_count_by_batch = Counter(row["batch_tag"] for row in matched_rows)

transfers_by_export = defaultdict(list)
for row in transfer_rows:
    transfers_by_export[(row["export_id"], row["operator"])].append(row)

candidates = []
for export in export_rows:
    key = (export["export_id"], export["operator"])
    for transfer in transfers_by_export.get(key, []):
        if export["status"] == "success" and transfer["event"] == "external_upload":
            candidates.append({
                "export_id": export["export_id"],
                "operator": export["operator"],
                "batch_tag": export["batch_tag"],
                "sample_count": leak_count_by_batch[export["batch_tag"]],
                "matched_count": matched_count_by_batch[export["batch_tag"]],
            })

chosen = sorted(candidates, key=lambda x: (x["sample_count"], x["matched_count"]), reverse=True)[0]

dedup = {}
for row in sorted(
    [r for r in matched_rows if r["batch_tag"] == chosen["batch_tag"]],
    key=lambda x: (x["subject_id"], x["leak_id"])
):
    dedup.setdefault(row["subject_id"], row)

response_rows = sorted(
    [{
        "leak_id": row["leak_id"],
        "subject_id": row["subject_id"],
        "export_id": chosen["export_id"],
        "operator": chosen["operator"],
        "action": row["action"],
    } for row in dedup.values()],
    key=lambda x: (x["leak_id"], x["subject_id"])
)

out = BASE.parent.parent.parent / "response_plan.csv"
with out.open("w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=["leak_id", "subject_id", "export_id", "operator", "action"])
    writer.writeheader()
    writer.writerows(response_rows)

print(out)
print("rows =", len(response_rows))
```

### Step 3: 上传校验平台拿 flag

将生成的 `response_plan.csv` 上传到平台，返回满分：

```text
score = 100.000%
flag  = flag{040ae9835b39f202ec65245e1c483004}
```

## Flag

```text
flag{040ae9835b39f202ec65245e1c483004}
```
