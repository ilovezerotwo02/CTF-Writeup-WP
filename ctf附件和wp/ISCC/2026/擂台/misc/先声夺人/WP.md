# ShowTime 01 WP

## Flag

`ISCC{Eb0TOol7GZ0YEHI38VjhYjtofGDIRC}`

## 题目分析

附件里只有一个 `challenge.txt`，表面上是一段多语言政治经济文本。

先看十六进制，可以发现文本中混入了大量不可见字符：

- `U+200B` zero width space
- `U+200C` zero width non-joiner
- `U+200D` zero width joiner
- `U+FEFF` zero width no-break space

可见文本本身只是载体，真正的数据藏在这些零宽字符里。

## 提取隐藏数据

把四种零宽字符映射成四进制数字：

- `U+200B -> 0`
- `U+200C -> 1`
- `U+200D -> 2`
- `U+FEFF -> 3`

把所有零宽字符按顺序取出，转成四进制串，再每 4 位四进制还原成 1 个字节。

得到一段二进制数据，前 4 字节是干扰，偏移 `4` 开始是一段 `zlib` 压缩数据。解压后得到 JSON：

```json
{
  "aes": {
    "algorithm": "AES-256-CBC",
    "key_length": 32,
    "padding": "PKCS7"
  },
  "difficulty_bits": 26,
  "encrypted_flag": {
    "ciphertext": "aa228292d48f64709888c44ce7c331b04e486e566f573fef354370c5f166d8ae68e6556e9607e1da07bc79203c092372",
    "encoding": "hex",
    "iv": "5dc0b444e4ff507d4af8dcda8e64afa9"
  },
  "key_derivation": {
    "algorithm": "PBKDF2-HMAC-SHA256",
    "dklen": 32,
    "iterations": 10000,
    "password": "str(s) UTF-8",
    "salt": "nonce UTF-8"
  },
  "nonce": "inst_000_42ba6c3fb9863dfa",
  "plaintext": "UTF-8 string flag like ISCC{...}",
  "pow": {
    "condition": "hash has at least difficulty_bits leading zero bits (not exactly equal)",
    "hash": "SHA-256",
    "input": "nonce || str(s), UTF-8. Example: nonce='abc', s=123 → 'abc123'",
    "leading_zero_bits": "MSB-first: first (difficulty_bits // 8) bytes must be 0x00; if remaining bits r=difficulty_bits % 8, high r bits of next byte must be 0",
    "search": "Start from s=0, increment, find minimum valid s"
  },
  "s_format": "Non-negative integer; use Python-style str(s) in decimal, NO leading zeros, NO fixed width"
}
```

## 解题流程

JSON 已经把后续逻辑写明了：

1. 从 `s=0` 开始递增，计算 `SHA-256(nonce || str(s))`
2. 找到满足前导 `26` 个零比特的最小 `s`
3. 用 `PBKDF2-HMAC-SHA256(password=str(s), salt=nonce, iterations=10000, dkLen=32)` 派生 AES key
4. 使用 `AES-256-CBC` 和给定 `iv` 解密 `ciphertext`
5. 去掉 `PKCS7` padding，得到 flag

## 关键结果

- `nonce = inst_000_42ba6c3fb9863dfa`
- `difficulty_bits = 26`
- 最小满足条件的 `s = 39235849`
- 对应哈希：

```text
0000003a61bb5cf11e82e63fdc3037f9e7dd85f46a26bc9b62f78b901f96f62e
```

- 派生出的 key：

```text
723a04d8d8c1310f18aaa4963cf9ec6bf1518cf8c41827a9848b69f837cdb17c
```

## 最终 Flag

```text
ISCC{Eb0TOol7GZ0YEHI38VjhYjtofGDIRC}
```

## 复现

当前目录已经写好复现脚本：

```powershell
python solve.py
```

单进程 PoW 大约需要 2 到 3 分钟。
