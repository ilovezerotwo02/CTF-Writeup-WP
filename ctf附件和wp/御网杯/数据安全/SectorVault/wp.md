# SectorVault Writeup

## 1. 题目分析

附件外层 `5：SectorVault的附件.zip` 解压后，真正材料在：

- `tempdir/DS附件/SectorVault附件.zip`
- 其中只有一个镜像：`sectorvault.img.gz`

解压后得到 `sectorvault.img`，用 `file`/`fls` 可确认它是一个 ext4 文件系统镜像，卷标为 `SectorVault`。

## 2. 镜像内关键取证点

递归列目录后，能看到下面这些关键文件：

- 已删除扫描缓存
  - `/home/audit/.cache/sectorvault/scan_cache.sqlite`
  - `/home/audit/.cache/sectorvault/scan_cache.sqlite-shm`
  - `/home/audit/.cache/sectorvault/scan_cache.sqlite-wal`
- 已删除发布包
  - `/home/audit/Downloads/release/audit_release_20260507.zip`
  - `/home/audit/Downloads/release/audit_release_draft.zip`
- 现存辅助线索
  - `/home/audit/.bash_history`
  - `/home/audit/.config/sectorvault/recent.json`
  - `/var/log/app_audit.log`
  - `/home/audit/Documents/数据分级与敏感信息识别规范.md`
  - `/home/audit/Downloads/staging/*`

其中：

- `.bash_history` 显示扫描库路径和清理动作：
  - `sqlite3 ~/.cache/sectorvault/scan_cache.sqlite 'select count(*) from findings;'`
  - `sqlite3 ~/.cache/sectorvault/scan_cache.sqlite 'select release_name from releases where status="ready";'`
  - `sectorvault-cli cleanup --cache ~/.cache/sectorvault --release ~/Downloads/release`
- `app_audit.log` 明确写出：
  - `release prepared name=audit_release_20260507.zip status=ready`
  - `scan stopped before checkpoint`

所以正确归档就是 `audit_release_20260507.zip`。

## 3. 恢复缓存并确定统计规则

从恢复出的 SQLite 可看到两张关键表：

- `findings`
- `releases`

`releases` 中最关键的一条为：

- `release_name = audit_release_20260507.zip`
- `status = ready`
- `expected_total = 23`
- `password_hint = compute from validated evidence set`

识别规范里给出统计口径：

- 只统计 `risk_level >= 3`
- 手机号：标准化后必须为合法 11 位号段
- 身份证：生日有效且校验位正确
- 银行卡：16-19 位，命中企业 BIN 白名单，并通过 Luhn
- 邮箱：只统计外部邮箱，排除 `@internal.example`
- 同一 `category + normalized_value` 去重时，只保留 `source_path` 字典序最小、`line_no` 最小的一条
- 口令格式：
  - `SV-{case_id}-{effective_total}-P{phone_count}I{idcard_count}B{bankcard_count}E{email_count}-{evidence_digest8}`

## 4. 为什么最终是 23 条

如果把所有 `risk_level >= 3` 且格式合法的数据都算上，会得到 39 条，和 `releases.expected_total = 23` 对不上。

继续结合镜像内容看 staging 目录，可以发现：

- `legacy_202604.txt` 是历史遗留样本，不属于本次 `scope=20260507`
- 同时 ready 包的计数必须与发布策略匹配

因此本次有效记录应为：

- 排除 `legacy_202604.txt`
- 保留其余 staging 文件中 `risk_level >= 3`
- 再按规范做合法性校验和去重

最后得到 23 条，分类统计为：

- `phone = 7`
- `idcard = 6`
- `bankcard = 5`
- `email = 5`

## 5. evidence_digest8 与口令

按规范将最终 23 条记录按：

- `category`
- `normalized_value`
- `source_path`
- `line_no`

升序排序，逐行拼成：

```text
category,normalized_value,source_path,line_no
```

使用 UTF-8 + LF 计算 SHA256，取前 8 位得到：

- `evidence_digest8 = 479eff20`

于是口令为：

```text
SV-SV-20260507-23-P7I6B5E5-479eff20
```

## 6. 解压正确归档并取 flag

用上面的口令解压：

- `audit_release_20260507.zip`

可得到：

- `flag.txt`
- `evidence_summary.csv`
- `README.txt`

`flag.txt` 内容为：

```text
flag{b294816b2e2d1d50ea34f79bd7e42d6c}
```

## 7. 最终答案

```text
flag{b294816b2e2d1d50ea34f79bd7e42d6c}
```
