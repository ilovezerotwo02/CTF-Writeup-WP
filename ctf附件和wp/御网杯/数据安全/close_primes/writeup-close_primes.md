---
title: "close_primes"
ctf: "未知赛事"
date: 2026-05-31
category: crypto
difficulty: easy
points: 300
flag_format: "flag{...}"
author: "Codex"
---

# close_primes

## Summary

题目给了 RSA 公钥和加密后的二进制文件。由于密钥生成时选取的两个素数过于接近，可以直接用 Fermat 分解恢复私钥，再按块做 RSA-OAEP 解密得到原始 PNG 图片。

## Solution

### Step 1: Fermat 分解近邻素数

模数 `n = p * q` 中，`p` 和 `q` 非常接近，因此 `n` 几乎是一个完全平方数。设：

- `a = ceil(sqrt(n))`
- `b^2 = a^2 - n`

如果 `b^2` 是完全平方数，那么：

- `p = a - b`
- `q = a + b`

这题里从 `a = ceil(sqrt(n))` 开始第一次检查就成功，说明两个素数只相差 `11253473181757133448`。

### Step 2: 逐块 OAEP 解密图片

公钥长度是 1024 位，所以密文按 128 字节一块存储。`encrypted.bin` 长度是 `23168` 字节，正好是 `181` 个 RSA 密文块。恢复私钥后，对每个块做 `RSA-OAEP` 解密并拼接，得到 PNG 图片，图中直接给出 flag。

```python
from pathlib import Path
import math

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.number import inverse


BASE_DIR = Path(__file__).resolve().parent
TASK_DIR = BASE_DIR / "work" / "task"
PUBKEY_PATH = TASK_DIR / "pubkey.pem"
ENCRYPTED_PATH = TASK_DIR / "encrypted.bin"
OUTPUT_PATH = TASK_DIR / "recovered.png"


def fermat_factor(n: int) -> tuple[int, int]:
    a = math.isqrt(n)
    if a * a < n:
        a += 1
    while True:
        b2 = a * a - n
        b = math.isqrt(b2)
        if b * b == b2:
            return a - b, a + b
        a += 1


def main() -> None:
    pub = RSA.import_key(PUBKEY_PATH.read_bytes())
    n, e = pub.n, pub.e
    p, q = fermat_factor(n)
    phi = (p - 1) * (q - 1)
    d = inverse(e, phi)
    priv = RSA.construct((n, e, d, p, q))

    ciphertext = ENCRYPTED_PATH.read_bytes()
    block_size = pub.size_in_bytes()
    blocks = [
        ciphertext[i:i + block_size]
        for i in range(0, len(ciphertext), block_size)
    ]

    plaintext = b"".join(PKCS1_OAEP.new(priv).decrypt(block) for block in blocks)
    OUTPUT_PATH.write_bytes(plaintext)

    print(f"p = {p}")
    print(f"q = {q}")
    print(f"blocks = {len(blocks)}")
    print(f"recovered = {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
```

## Flag

```text
flag{08358491-2221-4363-9d77-a2df241f5891}
```
