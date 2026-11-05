---
title: "ECDSA nonce 重用"
ctf: "Unknown / local challenge set"
date: 2026-05-30
category: crypto
difficulty: medium
points: 300
flag_format: "flag{ecdsa_nonce_reuse_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx}"
author: "Codex"
---

# ECDSA nonce 重用

## Summary

两条不同消息使用了相同的 ECDSA nonce `k`，因此签名里的相同 `r` 直接泄露了 `k` 和私钥 `d`。附件足以恢复出真实私钥，并且可以用题目给出的公钥坐标完成校验。

## Solution

### Step 1: 利用重复 `r` 恢复 `k` 和私钥

ECDSA 在同一条曲线、同一个私钥下，如果两条不同消息错误地复用了同一个 nonce `k`，则两条签名满足：

```text
s1 = k^(-1) * (z1 + r*d) mod n
s2 = k^(-1) * (z2 + r*d) mod n
```

两式相减可得：

```text
k = (z1 - z2) * (s1 - s2)^(-1) mod n
d = (s1*k - z1) * r^(-1) mod n
```

这里的 `z1`、`z2` 不能直接用消息字节转整数，而要按照 ECDSA 习惯取 `SHA-256(message)` 的整数值。下面这份脚本从附件 `challenge.json` 出发，直接恢复私钥并验证公钥：

```python
#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec


SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def sha256_int(message_hex: str) -> int:
    message = bytes.fromhex(message_hex)
    return int.from_bytes(hashlib.sha256(message).digest(), "big")


data = json.loads(Path("challenge.json").read_text(encoding="utf-8"))
r = data["signature1_r"]
s1 = data["signature1_s"]
s2 = data["signature2_s"]
z1 = sha256_int(data["message1"])
z2 = sha256_int(data["message2"])

k = ((z1 - z2) * pow((s1 - s2) % SECP256K1_N, -1, SECP256K1_N)) % SECP256K1_N
d = ((s1 * k - z1) * pow(r, -1, SECP256K1_N)) % SECP256K1_N

priv = ec.derive_private_key(d, ec.SECP256K1())
pub = priv.public_key().public_numbers()

print("k =", k)
print("d =", d)
print("d_hex =", format(d, "064x"))
print("pubkey_match =", pub.x == data["public_key_x"] and pub.y == data["public_key_y"])
```

脚本输出的关键结果为：

```text
k = 107301833240331738304591658175235458020727888611563794588942039992482252284246
d = 18025492364864427567577218399246070016863871601206401586909453174203515796157
d_hex = 27da112f7d3f0567c8d95827b4eff200766b7550acf4849c312bb4849741fabd
pubkey_match = True
```

### Step 2: 逻辑核验

这道题的核心漏洞链路是自洽的，附件确实足以恢复私钥，且恢复出的私钥可以反推出与题目完全一致的公钥，所以“解出私钥”这一部分没有问题。

但题面没有明确说明最终 flag 后缀的生成规则。已知私钥十六进制是：

```text
27da112f7d3f0567c8d95827b4eff200766b7550acf4849c312bb4849741fabd
```

而 flag 格式要求：

```text
flag{ecdsa_nonce_reuse_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx}
```

如果把题意严格理解为“恢复私钥后直接拼进 flag”，那么最直接、最不引入额外假设的提交值就是：

```text
flag{ecdsa_nonce_reuse_27da112f7d3f0567c8d95827b4eff200766b7550acf4849c312bb4849741fabd}
```

如果平台端额外要求把私钥压缩成 32 个十六进制字符，那么题面漏掉了这一条映射规则。此时常见实现会有几种：

- `md5(str(private_key))`
- `md5(private_key_hex)`
- 直接取私钥十六进制的前 32 位或后 32 位

其中，若按很多教学题里最常见的“对数值答案做 `md5(str(x))`”规则，则候选 flag 为：

```text
flag{ecdsa_nonce_reuse_dd3fb4bb99a6a2c22b52cc7076609480}
```

若按“对十六进制私钥做 MD5”，则是：

```text
flag{ecdsa_nonce_reuse_8d7620f2bb7ed5c40bc11144f464d109}
```

## Flag

```text
附件能唯一恢复出的核心答案：
27da112f7d3f0567c8d95827b4eff200766b7550acf4849c312bb4849741fabd

不加额外假设时最直接的 flag：
flag{ecdsa_nonce_reuse_27da112f7d3f0567c8d95827b4eff200766b7550acf4849c312bb4849741fabd}

若平台强制 32 位十六进制后缀，则更常见的候选是：
flag{ecdsa_nonce_reuse_dd3fb4bb99a6a2c22b52cc7076609480}
```
