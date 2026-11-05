# 先声夺人 WP

## Flag

`ISCC{Eb0TOol7GZ0YEHI38VjhYjtofGDIRC}`

## 题目信息

- 分类：Misc
- 分值：150
- 完成数：2721

附件 `showtime_01.zip` 解压得到 `challenge.txt`，表面是一段混杂中、英、法、德、日、韩多国语言的政治经济文本。

## 解题思路

### 1. 零宽字符隐写

观察文本的十六进制，发现其中混入了大量不可见字符：

| Unicode | 名称 | 映射值 |
|---------|------|--------|
| `U+200B` | Zero Width Space | 0 |
| `U+200C` | Zero Width Non-Joiner | 1 |
| `U+200D` | Zero Width Joiner | 2 |
| `U+FEFF` | Zero Width No-Break Space (BOM) | 3 |

可见文本只是干扰项，真正的数据藏在这些零宽字符中。

### 2. 提取与解码

将零宽字符按出现顺序取出，按上表映射为四进制数字串（每位取值 0-3）。每 4 位四进制数恰好表示 1 个字节（`4^4 = 256`）：

```
U+200B U+200C FEFF U+200D → "0123" → 0*4³ + 1*4² + 2*4¹ + 3*4⁰ = 27 → 0x1B
```

全部转换后得到一段二进制数据。

### 3. zlib 解压

二进制数据的前 4 字节是干扰偏移量，从第 5 字节（offset=4）开始是 zlib 压缩数据。解压后得到 JSON：

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
  "pow": {
    "condition": "hash has at least difficulty_bits leading zero bits",
    "hash": "SHA-256",
    "input": "nonce || str(s), UTF-8",
    "leading_zero_bits": "MSB-first",
    "search": "Start from s=0, increment, find minimum valid s"
  },
  "s_format": "Non-negative integer; use Python-style str(s) in decimal"
}
```

### 4. Proof of Work

JSON 要求找到最小的非负整数 `s`，使得 `SHA256(nonce || str(s))` 的前 26 个比特（高 26 位）全部为 0：

- `nonce = "inst_000_42ba6c3fb9863dfa"`
- `difficulty_bits = 26`
- 相当于哈希值的前 3 个字节必须为 `0x00`，且第 4 字节的高 2 位也必须为 0（即 `byte[3] & 0xFC == 0`）

从 `s=0` 开始暴力递增，找到满足条件的 s：

```
s = 39235849
SHA256 = 0000003a61bb5cf11e82e63fdc3037f9e7dd85f46a26bc9b62f78b901f96f62e
```

### 5. 密钥派生与解密

用 PBKDF2-HMAC-SHA256 派生 AES 密钥：

- Password: `str(s)` → `"39235849"`
- Salt: `nonce` → `"inst_000_42ba6c3fb9863dfa"`
- 迭代次数: 10000
- 密钥长度: 32 字节

```
key = 723a04d8d8c1310f18aaa4963cf9ec6bf1518cf8c41827a9848b69f837cdb17c
```

然后用 AES-256-CBC 模式解密，IV 为 `5dc0b444e4ff507d4af8dcda8e64afa9`，去除 PKCS7 padding 得到明文 flag。

## 总结

本题结合了零宽字符隐写、自定义进制编码、zlib 压缩、PoW 爆破和标准密码学库操作，是一道典型的 Misc 杂项题，步骤清晰，适合入门。
