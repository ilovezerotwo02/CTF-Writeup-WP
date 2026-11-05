---
title: "ShadowMeter"
ctf: "数据安全"
date: 2026-05-31
category: forensics
difficulty: easy
points: 300
flag_format: "flag{...}"
author: ""
---

# ShadowMeter

## 解题思路

某业务系统的 Apache 访问日志和调试日志中发现了异常高频采集行为。日志中混杂着正常用户流量与 DataMeterAgent 工具的流量。通过提取 dumpio 中记录的 POST 请求体，拼接 base64 还原出 AES-256 加密的 ZIP 包，密码从管理员后台的 debug 接口调用中获取。

## 解题步骤

### 1. 定位攻击者

access.log 中观察到大量来自 `172.25.0.1` 的请求，部分带有 User-Agent `DataMeterAgent/3.4 (perf-collector)`。同时在 error.log 中发现对 `/admin/login.php` 的暴力破解：

```
username=admin_ops&password=Admin%40Pa%24%24w0rd
```

解码后为 `Admin@Pa$$w0rd`，登录成功返回 `{"token":"ops-internal-8dd18cfd"}`。

### 2. 追踪数据外传

error.log 启用了 `mod_dumpio` 的 trace7 级别日志，完整记录了 HTTP 请求和响应的原始字节。攻击者使用 `/collect/report.php` 将 70 个 base64 分片外传，每个分片包含 `app=portal&env=prod&job=SM-20260507-17&seq=N&note=...&sign=...`。

关键发现：`/admin/debug.php` 的 POST 请求体中包含加密密钥：

```
op=peek_export_keyf&token=meter_report&key=SM-20260507-17%3Ameter%3Areport
```

URL 解码后密钥为 `SM-20260507-17:meter:report`。

### 3. 还原 ZIP 包

从 error.log 提取所有 SM job 的 note 值，URL 解码后按 seq 顺序拼接，一次性 base64 解码。关键点：**不能逐块解码再拼接，而要将所有 base64 串拼接后一次性解码**，否则会因 padding 处理不当导致数据损坏。

还原后的 ZIP 大小为 10601 字节，包含 3 个文件：`export.csv`（23245 字节）、`manifest.json`、`readme.txt`。

### 4. 解密获取 Flag

使用 `7z` 或 `pyzipper` 以密码 `SM-20260507-17:meter:report` 解密。根据 `manifest.json` 中的 focus filter：

```json
{
  "app": "portal",
  "metric_name": "secure.checkpoint",
  "user_id": "ADMIN_OPS"
}
```

在 export.csv 中筛选到唯一匹配的记录，其 trace_tag 即为 flag。

## Exp

```python
import re, json, base64, io
import urllib.parse
from collections import defaultdict
import pyzipper

log_file = "error.log"

# 1. 提取 SM job 的 70 个 base64 分片
notes = defaultdict(list)
pat = re.compile(r"dumpio:  dumpio_in \(data-HEAP\): (app=.*)$")

with open(log_file, errors="replace") as f:
    for line in f:
        m = pat.search(line.rstrip("\n"))
        if not m:
            continue
        body = m[1]
        if "job=SM-20260507-17" not in body:
            continue
        qs = urllib.parse.parse_qs(body, keep_blank_values=True)
        seq = qs.get("seq", [None])[0]
        if seq and seq.isdigit():
            notes[int(seq)].append({k: v[0] for k, v in qs.items()})

# 2. 拼接并解码（关键：一次性解码而非逐块）
raw_b64 = "".join(notes[i][0]["note"] for i in sorted(notes))
zip_data = base64.b64decode(raw_b64, validate=True)

# 3. 解密 ZIP
pwd = b"SM-20260507-17:meter:report"
with pyzipper.AESZipFile(io.BytesIO(zip_data)) as zf:
    zf.setpassword(pwd)
    csv_text = zf.read("export.csv", pwd=pwd).decode()
    manifest = json.loads(zf.read("manifest.json", pwd=pwd))

# 4. 按 focus filter 定位目标记录
f = manifest["focus"]["filter"]
print(f"Filter: app={f['app']} metric={f['metric_name']} user={f['user_id']}")

for row in csv_text.strip().split("\n")[1:]:
    tid, app, uid, *_ = row.split(",")
    if app == f["app"] and uid == f["user_id"] and f["metric_name"] in row:
        tag = row.split(",")[-1].replace("tg_", "")
        print(f"Flag: flag{{{tag}}}")
        # flag{c1b50d61ac8b81fac5ab3ea499056c0a}
        break
```

## Flag

```
flag{c1b50d61ac8b81fac5ab3ea499056c0a}
```
