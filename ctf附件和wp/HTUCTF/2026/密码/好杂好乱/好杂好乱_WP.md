# 好杂好乱 — Writeup

**题目类别：** Crypto  
**附件：** `好杂好乱.txt`（160 个十六进制字符，单行）  
**Flag：** `HTU{b@seb@seb@se}`

## 题目分析

附件只有一行十六进制串，题目名"好杂好乱"已经暗示了套娃。先按 hex 解一层：

```
344435413443353634443336353335323439333534363437353935393541353134393441...
↓ hex
4D5A4C564D3653524935464759595A51494A55565557434F49464D57343543574B5A43574F50493D
```

解出来**还是一串十六进制文本**（`4D 5A 4C ...`），所以是两层 hex 连着：

```
4D5A4C564D3653... ↓ hex（第二次）
MZLVM6SRI5FGYYZQIJUVUWCOIFMW45CWKZCWOPI=
```

## 剥层过程

| 层 | 操作 | 结果 | 判定依据 |
|---|---|---|---|
| 1 | hex | `4D5A4C564D36...` | 仍是纯十六进制字符 |
| 2 | hex | `MZLVM6SRI5FGYYZQIJUVUWCOIFMW45CWKZCWOPI=` | 出现大写字母 + 数字 + 尾部 `=`，长度 40 |
| 3 | **base32** | `fWVzQGJlc0BiZXNAYntVVEg=` | 见下方说明 |
| 4 | base64 | `}es@bes@bes@b{UTH` | 出现 `=`，长度 % 4 == 0 |
| 5 | 字符串反转 | `HTU{b@seb@seb@se}` | 解出来是反的，翻转即得 |

### 第 3 层为什么是 base32 而不是 base64

这是本题唯一的坑。`MZLVM6SRI5FGYYZQIJUVUWCOIFMW45CWKZCWOPI=` 长度 40、含尾部 `=`，**同时满足 base64 和 base32 的长度条件**（40 % 4 == 0 且 40 % 8 == 0）。两种都试：

- 按 **base64** 解 → `b'1\x92\xd53\xa4\x91#\x91Fa\x86P \x95\x15Q`\x8e S\x16\xe3\x90\x96)\x90\x968\xf2'`，全是不可打印字节，排除；
- 按 **base32** 解 → `fWVzQGJlc0BiZXNAYntVVEg=`，干净的 base64 文本，命中。

> 经验：**长度能同时整除 4 和 8 的串，base32/base64 都要试，看输出是否可打印来定夺。**

### 第 5 层为什么要反转

第 4 层 base64 解出 `}es@bes@bes@b{UTH`——`}` 在最前面、`HTU` 在最后，明显是倒序，翻转一次得到 `HTU{b@seb@seb@se}`。

## 谜底呼应题名

`b@se` 是 `base` 的 leet 写法，出现三次，正好对应本题的三层 base 编码（base16 × 2 + base32 + base64）。若提交时 `@` 被过滤，可试语义还原版：

```
HTU{basebasebase}
```

## 复现

```bash
python solve_haozahaoluan.py
# [1] hex      -> 4D5A4C564D365352...43574F50493D
# [2] hex      -> MZLVM6SRI5FGYYZQIJUVUWCOIFMW45CWKZCWOPI=
# [3] base32   -> fWVzQGJlc0BiZXNAYntVVEg=
# [4] base64   -> }es@bes@bes@b{UTH
# [5] reverse  -> HTU{b@seb@seb@se}
```

脚本：`solve_haozahaoluan.py`（纯标准库）。
