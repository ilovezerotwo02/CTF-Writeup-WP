# 会赢的 —— Writeup

- **题目**：会赢的（Misc，1000 pts，静态附件）
- **附件**：`会赢的.zip`（72 846 字节，md5 `7b9eb594f5ecd392f6019f0e66cb5c4c`）
- **Flag**：

```
HTUCTF{1’d_w1n_y0u’r3_7h3_ch4113n63r_my_4p0106135_f0r_f4111n6_70_3n73r741n_y0u_5ukun4-54m4}
```

> ⚠️ 注意 flag 里的撇号是 **U+2019 弯引号 `’`**（UTF-8 `e2 80 99`），不是 ASCII `'`。

---

## 0. 一句话思路

附件是一个「双层套娃」：JPEG **文件尾**（EOI 之后）藏了前半句，ZIP **注释字段**里藏了一个被「半字节交换 + 整体反转」伪装过的 **7z 归档**，归档内 `flag.txt` 藏了后半句。两段 leet 串拼起来就是 flag。

---

## 1. 第一层：JPEG 尾部（前半句）

JPEG 以 `FFD9`（EOI）结束，但文件在 EOI 之后还有 **46 字节**：

```python
d = open('会赢的.jpeg','rb').read()
i = d.rfind(b'\xff\xd9')            # 73414，文件总长 73462
tail = d[i+2:]                      # 46 字节
# b'MeKAmWRfdzFuX3kwdeKAmXIzXzdoM19jaDQxMTNuNjNyX2'
```

这是一段**不带 padding 的 base64**（46 × 6 = 276 bit ≥ 34 × 8 = 272 bit，正好够编码 34 字节）：

```python
base64.b64decode(tail + b'==').decode('utf-8')
# '1’d_w1n_y0u’r3_7h3_ch4113n63r_'
```

得到 **p1 = `1’d_w1n_y0u’r3_7h3_ch4113n63r_`**

- **30 个字符 / 34 字节**（两个 `’` 各占 3 字节，所以字节数比字符数多 4）
- 还原 leet：`I'd win you're the challenger `（含**尾部一个空格**）
- 撇号是 **U+2019**，这一点后面很关键

> 检测手法：JPEG 尾部有多余数据时，第一反应就是 `xxd` 看一眼；也可以直接
> `binwalk -e` / `strings` 扫一遍。本题 JPEG 内部很干净（只有 JFIF/DQT/SOF0/DHT/SOS，
> **没有 APPn、没有 COM 段**），所以唯一异常就是 EOI 之后的这 46 字节。

---

## 2. 第二层：ZIP 注释里的 7z 归档（后半句）

### 2.1 发现注释不是随机数据

ZIP 的 EOCD（`PK\x05\x06`）在 offset **72609**，读 `comment_len`：

```python
e = z.rfind(b'PK\x05\x06')
n = struct.unpack('<H', z[e+20:e+22])[0]     # 215
C = z[e+22:e+22+n]                            # 215 字节
```

`72609 + 22 + 215 = 72846` = 文件大小，说明注释后没有多余字节，且这 215 字节**全部**是注释。

第一眼看上去像随机字节，但有个**决定性统计特征**：215 字节里有 **27 个 `0x00`**，
而真随机数据期望只有 `215/256 ≈ 0.84` 个。→ **它一定有结构，只是被变换过了**。

### 2.2 还原变换：半字节交换 + 整体反转

对常见变换逐个试，命中：

```python
W = bytes(((b & 0x0F) << 4) | (b >> 4) for b in C)[::-1]   # 半字节交换后整体反转
W[:6].hex()
# '377abcaf271c'   ← 正是 7z 的魔数 37 7A BC AF 27 1C
```

**（半字节交换后反转 = 反转后半字节交换）**，两者等价。

### 2.3 确认这是一个真的 7z

7z 的 32 字节 Signature Header 里偏移 12 处是 `NextHeaderOffset`、20 处是 `NextHeaderSize`：

```
NextHeaderOffset = 151
NextHeaderSize   = 32
32 + 151 + 32    = 215   ← 正好等于注释长度，严丝合缝
```

再验两个 CRC（StartHeaderCRC、NextHeaderCRC）**全部通过** —— 这不是巧合，是真归档。
本归档还带 `kEncodedHeader` 标志，即**归档头本身也被 LZMA 压缩过**。

### 2.4 提取 flag.txt

7-Zip 直接能开：

```
7z l -slt _7z.7z

  Path = flag.txt
  Size = 72        Packed Size = 76
  CRC  = DAA05664
  Method = LZMA2:12
```

只有 **1 个文件**。pack stream 是 LZMA2 的**未压缩块**（chunk 头 `01 00 47`，`0x0047+1 = 72`），
所以 72 字节明文直接可见，`unused_data = 0`（没有夹带）：

```
00GN10CNuV3a1VzX1BTef5WM0cjczcjbz8FM38lNuFTMxQjZfJHMm9VNzEjNwEDMwRzX512X
```

这 72 字节是**反转过的 base64**，反转回来再解：

```python
base64.b64decode(content[::-1]).decode('utf-8')
# '_my_4p0106135_f0r_f4111n6_70_3n73r741n_y0u_5ukun4-54m4'
```

得到 **p2 = `_my_4p0106135_f0r_f4111n6_70_3n73r741n_y0u_5ukun4-54m4`**

- **54 个字符**（纯 ASCII）
- 还原 leet：` my apologies for failing to entertain you sukuna-sama`（含**头部一个空格**）

---

## 3. 拼接：为什么是单下划线

两段的长度给出了铁证：

| 片段 | 字符数 | 对应原文（leet 是 1:1 替换，长度不变） |
|---|---|---|
| p1 | **30** | `I'd win you're the challenger ` ← 尾带 1 个空格 |
| p2 | **54** | ` my apologies for failing to entertain you sukuna-sama` ← 头带 1 个空格 |

p1 尾部和 p2 头部**各带一个空格**，它们其实是**同一个分隔空格**：作者把完整字符串切成两半时，
这个下划线在两边各保留了一份。所以拼接时要**共享掉一个**：

```python
flag_body = p1[:-1] + p2        # 等价于 p1 + p2[1:]
```

完整原文即五条悟的台词（`Nah, I'd win`（221 话）+ `You're the challenger`（223 话）
+ 网络流传的 `my apologies for failing to entertain you, Sukuna-sama`）：

```
I'd win you're the challenger my apologies for failing to entertain you sukuna-sama
```

leet 规则（从两段内部反推，非猜测）：空格 → `_`，撇号 `’` 与连字符 `-` 原样保留，逗号/句号删除。

---

## 4. 端到端脚本

```python
# -*- coding: utf-8 -*-
import base64, struct, io, zipfile, lzma, zlib

z = open('会赢的.zip', 'rb').read()

# ---- 1) JPEG 尾部 -> p1 ----
jpeg = zipfile.ZipFile(io.BytesIO(z)).read('会赢的.jpeg')
tail = jpeg[jpeg.rfind(b'\xff\xd9') + 2:]
p1 = base64.b64decode(tail + b'==').decode('utf-8')

# ---- 2) ZIP 注释 -> 半字节交换 + 反转 = 7z -> flag.txt -> p2 ----
e = z.rfind(b'PK\x05\x06')
n = struct.unpack('<H', z[e + 20:e + 22])[0]
W = bytes(((b & 0xF) << 4) | (b >> 4) for b in z[e + 22:e + 22 + n])[::-1]
assert W[:6] == bytes.fromhex('377abcaf271c'), '不是 7z'

off, = struct.unpack('<Q', W[12:20])
d = lzma.LZMADecompressor(format=lzma.FORMAT_RAW,
                          filters=[{'id': lzma.FILTER_LZMA2, 'dict_size': 1 << 22}])
content = d.decompress(W[32:32 + off])
assert zlib.crc32(content) & 0xffffffff == 0xDAA05664, 'flag.txt CRC 不匹配'
p2 = base64.b64decode(content[::-1]).decode('utf-8')

# ---- 3) 拼接 ----
print(p1, len(p1), '|', p2, len(p2))
print('HTUCTF{' + p1[:-1] + p2 + '}')
```

输出：

```
1’d_w1n_y0u’r3_7h3_ch4113n63r_ 30 | _my_4p0106135_f0r_f4111n6_70_3n73r741n_y0u_5ukun4-54m4 54
HTUCTF{1’d_w1n_y0u’r3_7h3_ch4113n63r_my_4p0106135_f0r_f4111n6_70_3n73r741n_y0u_5ukun4-54m4}
```

> 本机 Python 3.10 可直接跑。复现脚本见同目录 `solve_final.py`、`v2/solve.py`。

---

## 5. 踩坑与教训

1. **"看起来像随机"不等于随机。** 注释里 27 个 `0x00`（期望 0.84 个）就是结构信号。
   遇到疑似随机的字节块，先把 **反转 / 半字节交换 / 位反转 / 二者组合** 轮一遍再判随机 —— 本题正是「半字节交换 + 反转」。
2. **提交前数「字符数」而不是「字节数」。** UTF-8 多字节字符（`’` 占 3 字节）会掩盖长度线索；
   本题正是靠「30 字符 / 54 字符精确对应原文」锁定了拼接方式。
3. **撇号必须保持 U+2019。** 若被编辑器/输入法规范化成 ASCII `'`，flag 就错。
   提交走 JSON 时 `json.dumps()` 默认 `ensure_ascii=True` 会转义成 `\u2019`，传输是安全的。
4. 本题早期版本 flag 有误（接缝为双下划线），作者修正后为**单下划线**（两段共享分隔空格）。
