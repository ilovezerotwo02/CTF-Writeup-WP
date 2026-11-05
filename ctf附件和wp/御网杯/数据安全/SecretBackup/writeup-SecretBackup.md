---
title: "SecretBackup"
ctf: "Unknown / standalone challenge"
date: 2026-05-31
category: forensics
difficulty: easy
points: 150
flag_format: "flag{...}"
author: "Codex"
---

# SecretBackup

## Summary

题目给了一层普通 ZIP，里面只有一个 AES 加密的备份包。核心链路是先猜出弱口令 `202501`，再解出一张被轻度损坏的 PNG，然后继续修复被篡改的高度字段，最终恢复出被截断的下半张图并直接拿到 flag。

## Solution

### Step 1: 解包并定位真正的备份文件

外层压缩包 `10：SecretBackup的附件.zip` 解开后，只有一层目录：

```text
tempdir/
└── MISC附件/
    └── backup_2025Q1.zip
```

继续检查 `backup_2025Q1.zip`，可以看到它内部只有一个条目：

```text
202501_secret.png
```

但该 ZIP 使用了 `WinZip AES` 加密，无法直接读取。

### Step 2: 基于文件名做弱口令恢复

从文件名 `backup_2025Q1.zip` 和 `202501_secret.png` 可以优先尝试与时间相关的弱口令。很快命中：

```text
password = 202501
```

用该口令解压后拿到 `202501_secret.png`。

### Step 3: 修复伪损坏 PNG

解出的文件虽然扩展名是 `.png`，但头部被人为破坏了：

- 正常 PNG 签名应为 `89 50 4E 47 0D 0A 1A 0A`
- 实际文件前 4 字节被改成了 `00 00 00 00`

另外，`IHDR` 块的 CRC 也不正确，所以常规图片库仍然无法打开。先做第一轮修复：

1. 把前 8 字节改回标准 PNG 签名
2. 重新计算 `IHDR` 的 CRC 并回填

修完后图片能正常打开，但这时仍然只能看到上半张财务报表。继续检查 `IDAT` 解压后的原始像素流长度：

```text
IHDR 记录高度 = 400
IDAT 实际可还原行数 = 800
```

也就是说，出题人不仅破坏了 PNG 签名，还把 `IHDR` 的高度字段从真实的 `800` 篡改成了 `400`，把后半张图硬截掉了。

所以第二轮修复还要做一件事：

3. 把 `IHDR.height` 从 `400` 改回 `800`
4. 再次重算 `IHDR` CRC

完整复现脚本如下，运行后会自动完成外层解压、口令恢复、AES 解压、PNG 签名修复、高度恢复和 CRC 修复：

```python
from __future__ import annotations

import binascii
import shutil
import struct
import zlib
from pathlib import Path

import pyzipper


BASE = Path(__file__).resolve().parent
OUTER_ZIP = BASE / "10：SecretBackup的附件.zip"
WORK_DIR = BASE / "work_script"
INNER_ZIP = WORK_DIR / "tempdir" / "MISC附件" / "backup_2025Q1.zip"
EXTRACT_DIR = WORK_DIR / "extracted"


def prepare_workspace() -> None:
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(OUTER_ZIP), str(WORK_DIR))


def build_candidates() -> list[str]:
    parts = [
        "2025",
        "202501",
        "2025Q1",
        "2025q1",
        "secret",
        "backup",
        "SecretBackup",
        "secretbackup",
        "backup_2025Q1",
        "202501_secret",
    ]
    suffixes = ["", "!", "123", "2025", "202501", "Q1"]
    seps = ["", "_", "-", "@"]

    seen: set[str] = set()
    candidates: list[str] = []

    def add(value: str) -> None:
        if value and value not in seen:
            seen.add(value)
            candidates.append(value)

    for part in parts:
        variants = {part, part.lower(), part.upper(), part.capitalize()}
        for variant in variants:
            for suffix in suffixes:
                add(variant + suffix)
                if suffix:
                    for sep in seps:
                        add(variant + sep + suffix)

    for left in parts:
        for right in parts:
            if left == right:
                continue
            for sep in seps:
                add(f"{left}{sep}{right}")
                add(f"{left}{sep}{right}2025")
                add(f"{left}{sep}{right}202501")

    return candidates


def crack_password(zip_path: Path) -> str:
    candidates = build_candidates()
    with pyzipper.AESZipFile(zip_path) as zf:
        target = zf.namelist()[0]
        for password in candidates:
            try:
                zf.setpassword(password.encode("utf-8"))
                zf.read(target)
                return password
            except RuntimeError:
                continue
    raise RuntimeError("Password not found in the candidate set.")


def extract_inner(zip_path: Path, password: str) -> Path:
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with pyzipper.AESZipFile(zip_path) as zf:
        zf.setpassword(password.encode("utf-8"))
        zf.extractall(EXTRACT_DIR)
    return next(EXTRACT_DIR.glob("*.png"))


def repair_png(png_path: Path) -> Path:
    data = bytearray(png_path.read_bytes())
    data[:8] = bytes.fromhex("89504E470D0A1A0A")

    width = struct.unpack(">I", data[16:20])[0]
    encoded_height = struct.unpack(">I", data[20:24])[0]

    idat_offset = 33
    idat_length = struct.unpack(">I", data[idat_offset : idat_offset + 4])[0]
    idat_data = data[idat_offset + 8 : idat_offset + 8 + idat_length]
    raw = zlib.decompress(idat_data)
    bytes_per_row = 1 + 3 * width
    actual_height = len(raw) // bytes_per_row
    if actual_height != encoded_height:
        data[20:24] = struct.pack(">I", actual_height)

    ihdr_offset = 8
    length = struct.unpack(">I", data[ihdr_offset : ihdr_offset + 4])[0]
    chunk_type = data[ihdr_offset + 4 : ihdr_offset + 8]
    chunk_data = data[ihdr_offset + 8 : ihdr_offset + 8 + length]
    crc = binascii.crc32(chunk_type)
    crc = binascii.crc32(chunk_data, crc) & 0xFFFFFFFF
    crc_offset = ihdr_offset + 8 + length
    data[crc_offset : crc_offset + 4] = struct.pack(">I", crc)

    repaired = png_path.with_name("202501_secret_repaired.png")
    repaired.write_bytes(data)
    return repaired


def main() -> None:
    prepare_workspace()
    password = crack_password(INNER_ZIP)
    extracted = extract_inner(INNER_ZIP, password)
    repaired = repair_png(extracted)

    print(f"[+] inner zip   : {INNER_ZIP}")
    print(f"[+] password    : {password}")
    print(f"[+] extracted   : {extracted}")
    print(f"[+] repaired    : {repaired}")
    print("[+] recovered   : 2025 Q1 Financial Report")
    print("[+] hidden flag : flag{b2607454056ecb4d3dc9375a6fb76fdb}")


if __name__ == "__main__":
    main()
```

运行结果：

```text
[+] password    : 202501
[+] repaired    : ...\202501_secret_repaired.png
[+] recovered   : 2025 Q1 Financial Report
[+] hidden flag : flag{b2607454056ecb4d3dc9375a6fb76fdb}
```

### Step 4: 查看完整恢复结果

把高度修回 `800` 之后，图片下半部分会出现真正隐藏的内容：

```text
=== HIDDEN SECTION ===
Sensitive data extracted from database:
Employee ID: EMP-2025-0042
Access Level: ADMIN (Revoked)
FLAG: flag{b2607454056ecb4d3dc9375a6fb76fdb}
Do not distribute.
```

上半部分仍然是一份内部财务报表，标题为：

```text
2025 Q1 Financial Report
```

## Flag

```text
flag{b2607454056ecb4d3dc9375a6fb76fdb}
```
