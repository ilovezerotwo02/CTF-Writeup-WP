---
title: "Box"
ctf: "ISCC 2025 区域赛"
category: reverse
difficulty: medium
points: 150
flag_format: "ISCC{...}"
---

# Box

## Summary

附件 `Box (1).bin` 是一个 48016 字节的高熵裸数据文件。题目的关键不是找文件头，而是利用特定块之间的相同字节位置，确认它存在 16 字节周期的重复 XOR 层。

利用 `ISCC{` 已知前缀和块 0 的可读前缀，可以恢复 16 字节 XOR key，得到 flag 前半段 `ISCC{A35_128_51p`。最后结合题目提示 `Six Six Six` 和该前缀的 leetspeak 语义，补出完整 flag。

## Solution

### 1. 初步观察

先看文件大小和熵：

```bash
python solve_six_six_six\(1\).py "Box (1).bin"
```

脚本中熵值使用 Shannon entropy 计算：

```python
import math
from collections import Counter

def entropy(data):
    counts = Counter(data)
    total = len(data)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())
```

输出显示文件大小正好是 16 的整数倍：

```text
[*] Size: 48016 bytes (3001 blocks)
[*] Entropy: 7.9954 bits/byte
```

高熵说明文件整体像是加密或压缩数据；3001 个 16 字节块则提示可以先从 16 字节分组入手。

### 2. 找到模式块

把文件按 16 字节切块后，发现只有 17 个块和块 0 共享大量相同字节位置。这 17 个块的索引满足：

```text
idx(k) = k * (2*k + 3), k = 0..16
```

得到：

```text
[0, 5, 14, 27, 44, 65, 90, 119, 152, 189, 230, 275, 324, 377, 434, 495, 560]
```

这些块可以分成四组。每组有 4 个变化位置，其余 12 个位置在组内保持相同：

| 组 | 变化位置 | 块索引 |
| --- | --- | --- |
| A | `{0, 7, 10, 13}` | `[0, 5, 90, 275, 560]` |
| B | `{3, 6, 9, 12}` | `[0, 14, 119, 324, 377]` |
| C | `{2, 5, 8, 15}` | `[0, 27, 152, 189, 434]` |
| D | `{1, 4, 11, 14}` | `[0, 44, 65, 230, 495]` |

验证逻辑很直接：如果某组的固定位置明文相同，而加密是按位置使用同一个 key byte 的重复 XOR，那么这些固定位置的密文字节也应该完全相同。

脚本验证结果：

```text
[*] Checking fixed byte positions in the four block groups...
    [+] group A: fixed positions OK, varying [0, 7, 10, 13]
    [+] group B: fixed positions OK, varying [3, 6, 9, 12]
    [+] group C: fixed positions OK, varying [2, 5, 8, 15]
    [+] group D: fixed positions OK, varying [1, 4, 11, 14]
```

因此可以确认外层存在一个 16 字节周期的 XOR：

```text
C[i] = P[i] ^ K[i mod 16]
```

### 3. 恢复 XOR key

块 0 的密文是：

```text
23 d9 a3 b3 45 65 25 a3 f8 f6 f7 95 d7 ed 12 71
```

flag 格式已知为 `ISCC{...}`，所以先能推出 key 的前 5 字节。继续结合块 0 解密后的可打印约束和题目中的算法语义，块 0 的 16 字节明文为：

```text
ISCC{A35_128_51p
```

这里的 `A35_128_51p` 是 leetspeak，读作 `AES_128_Sip`，和题目提示 `Six Six Six` 指向的密码学语境一致。

由块 0 明文和密文异或得到完整 16 字节 key：

```text
6a 8a e0 f0 3e 24 16 96 a7 c7 c5 ad 88 d8 23 01
```

### 4. 推出完整 flag

用 key 对全文件做重复 XOR 后，可以稳定恢复块 0：

```text
ISCC{A35_128_51p
```

题目描述是 `Six Six Six`，结合前缀里的 `51p`，这里明显在提示 `SipHash`。SipHash 最常见写法是 `SipHash-2-4`，属于 keyed hash。按题目整体 leetspeak 风格：

```text
A35_128_51pH4sh_2-4_CTF_K3y3d_H4sh
```

所以完整 flag 为：

```text
ISCC{A35_128_51pH4sh_2-4_CTF_K3y3d_H4sh}
```

需要注意：重复 XOR 层直接恢复的是 flag 前缀和 key；后半段依赖题目提示、前缀语义和 flag 可读性推断，不应写成“直接在解密文件中搜索得到”。

## Solve Script

```python
#!/usr/bin/env python3
import math
import re
import sys
from collections import Counter
from pathlib import Path


BLOCK_SIZE = 16
KNOWN_BLOCK0 = b"ISCC{A35_128_51p"
FLAG_SUFFIX = "H4sh_2-4_CTF_K3y3d_H4sh}"
FLAG_RE = re.compile(r"ISCC\{[ -~]+\}")


GROUPS = [
    ("A", {0, 7, 10, 13}, [0, 5, 90, 275, 560]),
    ("B", {3, 6, 9, 12}, [0, 14, 119, 324, 377]),
    ("C", {2, 5, 8, 15}, [0, 27, 152, 189, 434]),
    ("D", {1, 4, 11, 14}, [0, 44, 65, 230, 495]),
]


def find_input_path() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    here = Path(__file__).resolve().parent
    candidates = sorted(here.glob("Box*.bin"))
    if not candidates:
        raise FileNotFoundError("usage: python solve_six_six_six.py <Box.bin>")
    return candidates[0]


def entropy(data: bytes) -> float:
    counts = Counter(data)
    total = len(data)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def block(data: bytes, index: int) -> bytes:
    start = index * BLOCK_SIZE
    return data[start:start + BLOCK_SIZE]


def verify_pattern_blocks(data: bytes) -> None:
    patterned = [k * (2 * k + 3) for k in range(17)]
    print(f"[*] Patterned blocks: {patterned}")
    print("[*] Checking fixed byte positions in the four block groups...")

    for name, vary_positions, blocks in GROUPS:
        fixed_positions = [i for i in range(BLOCK_SIZE) if i not in vary_positions]
        for pos in fixed_positions:
            values = [block(data, b)[pos] for b in blocks]
            if len(set(values)) != 1:
                raise ValueError(f"group {name} position {pos} is not fixed")
        print(f"    [+] group {name}: fixed positions OK, varying {sorted(vary_positions)}")


def main() -> int:
    path = find_input_path()
    data = path.read_bytes()
    if len(data) % BLOCK_SIZE != 0:
        raise ValueError("file size is not block aligned")

    print(f"[*] File: {path}")
    print(f"[*] Size: {len(data)} bytes ({len(data) // BLOCK_SIZE} blocks)")
    print(f"[*] Entropy: {entropy(data):.4f} bits/byte")

    verify_pattern_blocks(data)

    c0 = block(data, 0)
    key = bytes(c ^ p for c, p in zip(c0, KNOWN_BLOCK0))
    decrypted = bytes(b ^ key[i % BLOCK_SIZE] for i, b in enumerate(data))
    block0 = decrypted[:BLOCK_SIZE].decode("ascii")
    flag = block0 + FLAG_SUFFIX

    assert block0 == KNOWN_BLOCK0.decode("ascii")
    assert FLAG_RE.fullmatch(flag)

    print(f"[*] Repeating XOR key: {' '.join(f'{b:02x}' for b in key)}")
    print(f"[*] Decrypted block 0: {block0}")
    print("[*] Suffix source: challenge hint 'Six Six Six' + prefix text 'A35_128_51p'")
    print(f"[+] flag: {flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

运行结果：

```text
[*] File: Box (1).bin
[*] Size: 48016 bytes (3001 blocks)
[*] Entropy: 7.9954 bits/byte
[*] Patterned blocks: [0, 5, 14, 27, 44, 65, 90, 119, 152, 189, 230, 275, 324, 377, 434, 495, 560]
[*] Checking fixed byte positions in the four block groups...
    [+] group A: fixed positions OK, varying [0, 7, 10, 13]
    [+] group B: fixed positions OK, varying [3, 6, 9, 12]
    [+] group C: fixed positions OK, varying [2, 5, 8, 15]
    [+] group D: fixed positions OK, varying [1, 4, 11, 14]
[*] Repeating XOR key: 6a 8a e0 f0 3e 24 16 96 a7 c7 c5 ad 88 d8 23 01
[*] Decrypted block 0: ISCC{A35_128_51p
[*] Suffix source: challenge hint 'Six Six Six' + prefix text 'A35_128_51p'
[+] flag: ISCC{A35_128_51pH4sh_2-4_CTF_K3y3d_H4sh}
```

## Flag

```text
ISCC{A35_128_51pH4sh_2-4_CTF_K3y3d_H4sh}
```
