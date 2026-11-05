---
title: "BabyRSA8"
ctf: "Unknown"
date: 2026-05-30
category: crypto
difficulty: easy
points: 150
flag_format: "flag{...}"
author: "Codex"
---

# BabyRSA8

## 题目概述

题目给了一个非常基础的 RSA 加密脚本，参数里公钥指数是 `e = 3`，而且没有使用任何 padding。由于明文 flag 很短，满足 `m^3 < n`，所以密文其实没有发生模 `n` 回绕，直接就是整数意义下的 `m^3`。因此这题不需要分解 `n`，只需要把 `c` 开整数三次方即可。

## 核心思路

原始加密关系为：

`c = m^e mod n`

题目里 `e = 3`，于是得到：

`c = m^3 mod n`

如果明文足够短，使得：

`m^3 < n`

那么模运算不会真正生效，式子就会退化成：

`c = m^3`

接下来只需要：

- 求出 `c` 的精确整数三次方根
- 把得到的整数转回字节串
- 解码得到 flag

## 脚本说明

本地使用的解题脚本是 [BabyRSA1.py](D:/桌面/yuwang/crp/1/BabyRSA1.py)，它的结构和作用如下：

- `load_values()`
  从 [output.txt](D:/桌面/yuwang/crp/1/output.txt) 读取 `n`、`e`、`c`
- `exact_cuberoot()`
  使用整数牛顿迭代求 `c` 的精确三次方根，并检查是否为完整立方
- `decode_integer()`
  把恢复出的整数转成字节串，再按 `utf-8` 解码
- `recover_flag()`
  先检查 `e == 3`，再恢复明文，并验证这条“小指数直接开根”的攻击条件成立

```python
from pathlib import Path


DATA_FILE = Path(__file__).with_name("output.txt")


def load_values(path: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = int(value.strip())
    return result


def exact_cuberoot(value: int) -> int:
    guess = 1 << ((value.bit_length() + 2) // 3)
    while True:
        updated = (2 * guess + value // (guess * guess)) // 3
        if updated >= guess:
            break
        guess = updated
    while (guess + 1) ** 3 <= value:
        guess += 1
    while guess**3 > value:
        guess -= 1
    if guess**3 != value:
        raise ValueError("ciphertext is not a perfect cube")
    return guess


def decode_integer(value: int) -> str:
    size = (value.bit_length() + 7) // 8
    return value.to_bytes(size, "big").decode("utf-8")


def recover_flag() -> str:
    values = load_values(DATA_FILE)
    n = values["n"]
    e = values["e"]
    c = values["c"]
    if e != 3:
        raise ValueError(f"unexpected public exponent: {e}")
    message = exact_cuberoot(c)
    if pow(message, e) >= n:
        raise ValueError("small-exponent shortcut does not apply")
    return decode_integer(message)


if __name__ == "__main__":
    print(recover_flag())
```

## 运行结果

直接运行 [BabyRSA1.py](D:/桌面/yuwang/crp/1/BabyRSA1.py)：

```text
flag{07f7b9e5cd7961b237aa0eed1b317aa8}
```

这说明脚本成功从密文中恢复了原始明文。之所以可行，是因为这题本质上就是未填充 RSA 在小指数 `e = 3` 下的经典漏洞利用。

## 总结

这题的关键不是分解模数，而是识别出：

- `e` 很小
- 没有 padding
- 明文很短

三者组合后，`c` 实际上就是 `m^3`，所以直接开三次方即可拿到 flag。这也是 textbook RSA 在 CTF 里最常见的入门考点之一。

## Flag

```text
flag{07f7b9e5cd7961b237aa0eed1b317aa8}
```
