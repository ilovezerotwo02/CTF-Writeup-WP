---
title: "peach_garden_xor"
ctf: "unknown"
date: 2026-05-31
category: crypto
difficulty: easy
points: 150
flag_format: "flag{...}"
author: "Codex"
---

# peach_garden_xor

## Summary

题目给了一份 `task.docx.enc`，实际是对 DOCX/ZIP 文件做了 4 字节循环 XOR。利用 DOCX 固定文件头 `PK\x03\x04` 可以直接反推出 XOR 密钥，解密后在 `word/document.xml` 末尾拿到经过 `ROT13` 的 flag。

## Solution

### Step 1: 利用 ZIP 文件头恢复 XOR 密钥

DOCX 本质上是 ZIP。加密文件前 4 字节为：

```text
51 7E 7F AD
```

而正常 DOCX/ZIP 的前 4 字节固定为：

```text
50 4B 03 04
```

两者异或即可得到 4 字节循环密钥：

```text
01 35 7c a9
```

### Step 2: 解密 DOCX 并提取隐藏内容

用该密钥循环异或整个 `task.docx.enc` 后，可以得到合法的 DOCX。继续解压 DOCX，检查 `word/document.xml`，在正文末尾能找到一段候选字符串：

```text
synt{nq213351-9510-46p0-8622-9pqrn9s634q2}
```

`synt` 是 `flag` 的 `ROT13` 结果，因此把整串再做一次 `ROT13` 即可得到最终 flag。

```python
import codecs
import io
import re
import zipfile
from pathlib import Path


ZIP_HEADER = b"PK\x03\x04"


def find_task_zip(base: Path) -> Path:
    matches = sorted(base.rglob("task.zip"))
    if not matches:
        raise FileNotFoundError("task.zip not found under challenge directory")
    return matches[0]


def decrypt_docx(enc_data: bytes) -> tuple[bytes, bytes]:
    key = bytes(c ^ p for c, p in zip(enc_data[:4], ZIP_HEADER))
    dec = bytes(b ^ key[i % len(key)] for i, b in enumerate(enc_data))
    return key, dec


def recover_flag(docx_data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_data)) as docx:
        document_xml = docx.read("word/document.xml").decode("utf-8", errors="ignore")

    match = re.search(r"synt\{[a-z0-9\-]+\}", document_xml, re.IGNORECASE)
    if not match:
        raise ValueError("flag candidate not found in word/document.xml")

    return codecs.decode(match.group(0), "rot_13")


def main() -> None:
    base = Path(__file__).resolve().parent
    task_zip = find_task_zip(base)

    with zipfile.ZipFile(task_zip) as archive:
        enc_name = next(name for name in archive.namelist() if name.endswith(".enc"))
        enc_data = archive.read(enc_name)

    key, docx_data = decrypt_docx(enc_data)
    flag = recover_flag(docx_data)

    print(f"task.zip: {task_zip}")
    print(f"xor key: {key.hex()}")
    print(f"flag: {flag}")


if __name__ == "__main__":
    main()
```

运行结果：

```text
xor key: 01357ca9
flag: flag{ad213351-9510-46c0-8622-9cdea9f634d2}
```

## Flag

```text
flag{ad213351-9510-46c0-8622-9cdea9f634d2}
```
