# Jammed — Misc Writeup

## 题目信息

- **题目名称**：Jammed
- **题目类型**：Misc / 图片信息还原 / 打字机编码
- **难度**：中等
- **关键线索**：1984 年、Correcting Selectric II、两张记录、原始序号 01～24、末尾两位片段

**最终 Flag：**

```text
flag{y0u_f0und_th3_treasure_f8427e}
```

## 一、附件分析

解压题目附件 `Jammed.zip`，得到：

```text
Jammed.zip
├── page1.png
├── page2.png
├── sha256.txt
└── treasure.zip
```

题目说明，原始每一条记录的结构是：

```text
两位序号/五位流水码/两位片段
```

序号应为 `01`～`24`，将**原始顺序**下的 24 个末尾两位片段拼接，即为 48 字符的压缩包密码。

两张 PNG 都像打字机打印出来的记录，但是同一位置的字符并不一致，有的字符甚至变成了标点符号。题面特意给出 **Correcting Selectric II**，说明这里重点不是普通的凯撒移位或 ROT，而是利用电动打字机的字球选择机制恢复字符。

另一个关键点是：`treasure.zip` 采用 **WinZip AES-256** 加密，压缩包内的文件名为 `flag.txt`。最终需要拿密码实际解密，而不能只凭字符串长得像就判断成功。

## 二、整理两张记录

第一张记录的序号也遭到了字符替换，先根据它应该恰好对应 `01`～`24` 这一约束，得到序号数字与打出字符之间的关系：

| 原数字 | 第一张纸上对应的字符 |
|:---:|:---:|
| 0 | `h` |
| 1 | `x` |
| 2 | `n` |
| 3 | `u` |
| 4 | `l` |
| 5 | `e` |
| 6 | `k` |
| 7 | `d` |
| 8 | `c` |
| 9 | `b` |

例如，第一张纸上的 `hx/l;tb-/-g` 可以还原序号为 `01`；第二张纸上相应的是 `01/17z99/91`。至此，两份记录可以按原始序号对齐，而不是按图片上的上下行位置一一对应。

**注意：** 流水码和末尾片段中的 `/`、`,`、`;` 等符号都可能是故障打印出的字符，所以不要对整行直接使用 `split('/')` 分段。应按固定字段宽度切片，即 `line[:2]`、`line[3:8]`、`line[9:11]`。

## 三、利用 Selectric 字球位置恢复字符

Selectric 字球的字符选择可以理解成两个维度：**Tilt（倾斜行）** 与 **Rotate（旋转列）**。题目的两张记录保留了互补的倾斜控制信息，旋转列则基本保持不变。

根据字符之间的对应规律，可以整理出本题使用的四行、每行 11 个位置的字符表：

```text
旋转列   0 1 2 3 4 5 6 7 8 9 10
Tilt 0   9 0 6 5 2 z 4 8 7 3  1
Tilt 1   b h k e n t l c d u  x
Tilt 2   w s i ' . ! o a r v  m
Tilt 3   - y q p = j / , ; f  g
```

给两张纸相同位置的字符分别记作 `a`、`b`。查表获得它们的行列：

- 第一张纸上 `a` 的倾斜行 `ta`，可提供原始 Tilt 的**高位**。
- 第二张纸上 `b` 的倾斜行 `tb`，可提供原始 Tilt 的**低位**。
- 两者应具有相同的 Rotate 列 `r`。

于是原始字符所在的行、列分别为：

```text
original_tilt = (ta // 2) * 2 + (tb % 2)
original_rotate = r
original_char = ROWS[original_tilt][original_rotate]
```

### 还原示例

以序号 `01` 为例，两页最后两个字符分别为：

```text
page1: -g
page2: 91
```

查表发现：

```text
'-' = Tilt 3, Rotate 0
'9' = Tilt 0, Rotate 0
  -> 原始 Tilt 2, Rotate 0 = 'w'

'g' = Tilt 3, Rotate 10
'1' = Tilt 0, Rotate 10
  -> 原始 Tilt 2, Rotate 10 = 'm'
```

因此第 `01` 条的原始末尾片段为 `wm`。

按照同样的方法处理剩余记录即可。过程中有一个需要注意的扫描件字形歧义：**第 22 条第二张纸末尾片段的首位，`1` 与小写 `l` 非常相似**。按旋转列一致性将该位置解释为 `l` 后，可恢复片段 `l2`，且最终密码通过了加密压缩包验证。

## 四、还原 24 个原始片段

| 序号 | 第一张纸 | 第二张纸 | 还原片段 |
|:---:|:---:|:---:|:---:|
| 01 | `-g` | `91` | `wm` |
| 02 | `,x` | `81` | `a1` |
| 03 | `-x` | `91` | `w1` |
| 04 | `hu` | `03` | `03` |
| 05 | `xb` | `x9` | `x9` |
| 06 | `xq` | `16` | `1i` |
| 07 | `ek` | `ek` | `ek` |
| 08 | `ef` | `5u` | `5f` |
| 09 | `qc` | `k8` | `q8` |
| 10 | `cb` | `89` | `89` |
| 11 | `xq` | `16` | `1i` |
| 12 | `,p` | `8e` | `ap` |
| 13 | `ju` | `t3` | `j3` |
| 14 | `/-` | `49` | `ow` |
| 15 | `hu` | `03` | `03` |
| 16 | `ke` | `k5` | `k5` |
| 17 | `qn` | `62` | `i2` |
| 18 | `;h` | `70` | `r0` |
| 19 | `n,` | `28` | `2a` |
| 20 | `px` | `e1` | `p1` |
| 21 | `uu` | `3u` | `3u` |
| 22 | `ln` | `12` | `l2` |
| 23 | `cd` | `8d` | `8d` |
| 24 | `cl` | `c4` | `c4` |

按 `01` 至 `24` 顺序直接拼接第四列，得到 **48 字符密码**：

```text
wma1w103x91iek5fq8891iapj3ow03k5i2r02ap13ul28dc4
```

## 五、解压并验证 Flag

使用 7-Zip 测试或解压：

```bash
7z t treasure.zip -pwma1w103x91iek5fq8891iapj3ow03k5i2r02ap13ul28dc4
7z x treasure.zip -pwma1w103x91iek5fq8891iapj3ow03k5i2r02ap13ul28dc4
cat flag.txt
```

解压后得到：

```text
flag{y0u_f0und_th3_treasure_f8427e}
```

本次还进行了独立的 **WinZip AES-256 解密检验**：由密码经过 PBKDF2 派生出的两字节密码验证值与文件头一致，密文的 **HMAC-SHA1（截取前 10 字节）** 也与压缩包附带的认证码一致，解密所得确实是上述 35 字节的 `flag.txt`。

### 关于题面 SHA-256 的异常

附件 `sha256.txt` 给出的值是：

```text
cfde9ebf5fb607b0c8d54abd707fa622fd8a246032d8b06d528e684f6238dcab
```

但对**实际成功解密的 48 字符密码**计算 SHA-256，得到：

```text
0193fddd8eb9518d1c897b1804083891f715056031670b78decfe5f89b35c163
```

两者**不相等**。因此这里不能声称密码通过了题面 SHA-256 校验；可以确认的是，它通过了压缩包内实际的 AES 密码校验和 HMAC 完整性检验，并正确解出了 Flag。题目哈希与有效解压密码的差异尚未确定原因。

## 六、总结

这道题的主要难点有两个。首先，两张图片上的记录不能直接拼接：第一张的序号发生了替换，且两张纸的同一字符可能被不同方式错误打印。其次，不能把它当作普通单表替换密码，而要根据 Selectric 的 Tilt/Rotate 结构，利用两份记录的互补信息还原字符位置。

最后通过 24 条记录恢复出 48 位密码，使用 AES 的实际解密和完整性校验确认结果。

**Flag：** `flag{y0u_f0und_th3_treasure_f8427e}`

## 附录：完整复现脚本

以下脚本已实际运行验证。将它保存为 `Jammed_solve.py`，并与原始附件 `Jammed.zip` 放在同一目录：

```bash
pip install cryptography
python Jammed_solve.py
```

脚本内包含手工转录并按序号排列的两页记录、解码过程、SHA-256 对照及 WinZip AES-256/HMAC 验证，运行后会直接输出 Flag，并生成 `Jammed_flag.txt`。


```python
#!/usr/bin/env python3
"""Jammed CTF solution: reconstruct two-character fragments from two noisy Selectric pages.

Usage: put this file next to Jammed.zip, install `cryptography`, run python Jammed_solve.py.
The source rows below are manually transcribed from the provided images.
"""
import hashlib
import hmac
import io
from pathlib import Path
import struct
import zipfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# The first page has its *original* row numbers restored from the glyph remapping.
PAGE_A = """\
01/l;tb-/-g
02/h//;g/,x
03/ckbnq/-x
04/cdbbx/hu
05/qeghg/xb
06/hdjdu/xq
07/bxkgl/ek
08/eyhef/ef
09/cqlxy/qc
10//qpb-/cb
11//ck/g/xq
12/y;fcg/,p
13/htybl/ju
14/xbxey//-
15/puygc/hu
16/yxfgd/ke
17/jxty-/qn
18/ny-nn/;h
19/fxnh//n,
20/clntx/px
21/g;cxj/uu
22/fl,uf/ln
23/ppyhg/cd
24/x;hxp/cl
"""
PAGE_B = """\
01/17z99/91
02/0447x/81
03/ckbnk/91
04/8db9l/03
05/6exhx/x9
06/hdt7u/16
07/91k1l/ek
08/e0h5u/5u
09/c6l1h/k8
10/46e99/89
11/4c64x/16
12/07ucl/8e
13/hthb4/t3
14/19xeh/49
15/e3018/03
16/013x7/k5
17/t1zh9/62
18/2h92n/70
19/3x204/28
20/clntx/e1
21/x78xt/3u
22/u483u/12
23/ee0hl/8d
24/x70xe/c4
"""
# 4 tilt rows x 11 rotate columns, used to reverse the two control-bit losses.
ROWS = [
    "90652z48731",
    "bhkentlcdux",
    "wsi'.!oarvm",
    "-yqp=j/,;fg",
]
LOOKUP = {ch: (tilt, rotation) for tilt, line in enumerate(ROWS) for rotation, ch in enumerate(line)}


def snippets(text):
    d = {}
    for line in text.strip().splitlines():
        num, serial, fragment = line[:2], line[3:8], line[9:11]
        assert len(line) == 11 and line[2] == "/" and line[8] == "/", line
        d[int(num)] = fragment
    assert set(d) == set(range(1, 25))
    return d


def password():
    a, b = snippets(PAGE_A), snippets(PAGE_B)
    recovered = []
    print("num   A    B   original")
    for n in range(1, 25):
        decoded = ""
        for col, (ca, cb) in enumerate(zip(a[n], b[n])):
            # In the scan, lowercase 'l' and digit '1' look almost identical.
            # The row/rotation consistency check resolves this ambiguous glyph.
            if n == 22 and col == 0:
                assert cb == "1"
                cb = "l"
            ta, ra = LOOKUP[ca]
            tb, rb = LOOKUP[cb]
            assert ra == rb, (n, col, ca, cb)
            decoded += ROWS[2 * (ta // 2) + (tb % 2)][ra]
        print(f"{n:02d}    {a[n]}   {b[n]}    {decoded}")
        recovered.append(decoded)
    pw = "".join(recovered)
    assert len(pw) == 48
    return pw


def decrypt_aes_zip(raw_zip, password_bytes):
    """WinZip AES-256, uncompressed method 0 (this specific challenge archive)."""
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        info = archive.infolist()[0]
        assert info.filename == "flag.txt" and info.compress_type == 99
        # Vendor AE / AES-256 strength 3, original method 0 (stored).
        # AES extra-field value: version[2], vendor[2], strength[1], method[2].
        aes_extra = None
        extra = info.extra
        while extra:
            tag_id, size = struct.unpack_from("<HH", extra, 0)
            payload, extra = extra[4:4+size], extra[4+size:]
            if tag_id == 0x9901:
                aes_extra = payload
        assert aes_extra and aes_extra[4] == 3 and struct.unpack_from("<H", aes_extra, 5)[0] == 0
        local_head_offset = info.header_offset
        fn_len, ex_len = struct.unpack_from("<HH", raw_zip, local_head_offset + 26)
        start = local_head_offset + 30 + fn_len + ex_len
        body = raw_zip[start:start + info.compress_size]
    salt, verifier, ciphertext, auth = body[:16], body[16:18], body[18:-10], body[-10:]
    keys = hashlib.pbkdf2_hmac("sha1", password_bytes, salt, 1000, 66)
    assert hmac.compare_digest(verifier, keys[64:66]), "password verifier failed"
    expected_mac = hmac.new(keys[32:64], ciphertext, hashlib.sha1).digest()[:10]
    assert hmac.compare_digest(expected_mac, auth), "AES HMAC integrity check failed"
    ecb_encryptor = Cipher(algorithms.AES(keys[:32]), modes.ECB()).encryptor()
    plaintext = bytearray()
    for offset in range(0, len(ciphertext), 16):
        counter = (offset // 16 + 1).to_bytes(16, "little")
        keystream = ecb_encryptor.update(counter)
        plaintext.extend(x ^ y for x, y in zip(ciphertext[offset:offset+16], keystream))
    ecb_encryptor.finalize()
    return bytes(plaintext)


def main():
    pw = password()
    target = "cfde9ebf5fb607b0c8d54abd707fa622fd8a246032d8b06d528e684f6238dcab"
    digest = hashlib.sha256(pw.encode()).hexdigest()
    print("\npassword:", pw)
    print("SHA256    :", digest)
    print("attachment:", target)
    print("SHA256 match:", digest == target)
    with zipfile.ZipFile(Path(__file__).with_name("Jammed.zip")) as attachment:
        inner = attachment.read("treasure.zip")
    flag_data = decrypt_aes_zip(inner, pw.encode())
    print("AES password verifier & HMAC: PASS")
    print("FLAG:", flag_data.decode())
    Path(__file__).with_name("Jammed_flag.txt").write_bytes(flag_data)


if __name__ == "__main__":
    main()

```
