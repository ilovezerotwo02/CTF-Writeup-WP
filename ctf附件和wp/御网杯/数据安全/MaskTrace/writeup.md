---
title: "MaskTrace"
ctf: "Unknown / standalone challenge"
date: 2026-05-31
category: misc
difficulty: easy
points: 300
flag_format: "flag{...}"
author: "Codex"
---

# MaskTrace

## Summary

题目给了一份 `user_export.sql` 和字段脱敏规范，要求只保留 `status=active` 的记录，逐字段做合法性校验与脱敏，导出指定表头的 UTF-8 CSV，再上传到校验平台拿 flag。核心就是把 SQL 导入内存后按规范实现一套严格的数据清洗流水线。

## Solution

### Step 1: 按规范实现脱敏与校验

先读取 `payload/MaskTrace附件/脱敏规范.md`，再把 `payload/MaskTrace附件/user_export.sql` 直接导入内存 SQLite。

关键规则：

- 只导出 `status='active'`，并按 `id ASC` 排序。
- `password` 做原文 MD5。
- `idcard` 要校验 18 位格式、真实生日和身份证校验位。
- `phone` / `bankcard` 先归一化后再判合法性。
- `birthday` 按参考日 `2026-05-01` 计算十年年龄段。
- 非法字段不丢行，直接写成 `INVALID`。

官方 `example.csv` 只给了前 40 行样例；用它对照本地脚本前缀输出，可以快速确认规则实现是否一致。

### Step 2: 生成 CSV 并提交

完整复现命令如下。脚本文件是 `solve_masktrace.py`，会生成 `masktrace_answer.csv`。

```bash
python solve_masktrace.py --compare example.csv
python solve_masktrace.py --fetch-captcha
# 观察 captcha.png 中的验证码
python solve_masktrace.py --submit --captcha 06J7
```

本次实际校验结果：

```text
{"filename":"masktrace_answer.csv","flag":"flag{eb463fa3858c3be11675e96664e615dc}\n","position":0,"reason":"上传成功","score":"100.000%","state":1}
```

## Flag

```text
flag{eb463fa3858c3be11675e96664e615dc}
```
