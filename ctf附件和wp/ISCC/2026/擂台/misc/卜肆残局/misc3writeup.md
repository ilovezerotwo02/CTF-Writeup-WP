# 城南旧庙怪卦摊 —— 四象破局全解析

## 0x00 题目概览

**题目背景：** 一座旧庙外摆着古怪卦摊，摊主走失，留下四件旧物：**天象**、**人言**、**地盘**、**时令**。摊上抄本凌乱，有的记位、有的记数、有的记辞、有的只记点画——暗指隐写数据的存储方式各不相同。

**附件结构（`misc3.zip` 解压后）：**

```
├── 八卦阵/
│   ├── 卦签-铜钱阵.svg       ← 洛书九宫数字排列
│   ├── 卦签-签筒布局.txt     ← 64卦签的排列顺序
│   ├── 卦签-签文图案.bmp     ← 六爻卦象位图
│   ├── 摊主杂记.txt          ← 混杂的线索与干扰项
│   ├── 时令-漏刻记录.csv     ← 时间序列数据
│   └── 心得/                  ← 解题者的四段分析笔记
│       ├── 卦签索引.md
│       ├── 卦文草稿.md
│       ├── 散钱总账.log
│       └── 百草图录.txt
├── 窥得天机.zip               ← 加密压缩包（需MD5密码）
└── 终局.7z                    ← 加密压缩包（需索引密码）
```

---

## 0x01 破局：从四件旧物中提取碎片

### 干扰项识别

深入分析附件时，会遇到多个明显的误导线索，需一一排除：

| 误导内容 | 出现位置 | 排除理由 |
|---------|---------|---------|
| `flag{meta_lovers_die_first}` | 卦文草稿.md 中 Base64 解码 | 过于刻意，不符合 Flag 格式 |
| `qian_kun_kan_li` | 摊主杂记.txt | 仅为八卦方位名称 |
| `ZG9udF91c2VfdGhlX29yZGVy` / `dont_use_the_order` | 百草图录.txt / Base64 解码 | 提示勿按直觉顺序 |
| `should_start_in_meta` | 百草图录.txt Base64 解码 | 指向 metadata 的误导 |
| `492357816` | 铜钱阵 SVG | 洛书幻方，非直接密码 |
| `ceasar+3` / `morse` | 卦签索引.md | 引导错误的解码思路 |

### 四象碎片的真实提取

#### ① 天象 —— `qW2O0z`

来源于**卦签-铜钱阵.svg**。SVG 文件中包含九宫格布局的洛书数字，从中心到四周的排列呈现出特定的字符映射。结合题面提示"有人记位，有人记数"以及洛书"戴九履一、左三右七"的方位规则，按特定方位顺序提取得到 6 字符。

**提取原理：** 将洛书九宫数字按"天道左旋"规则重新排列，取每个位置对应 ASCII 偏移量，映射到 Base64 字符集。

#### ② 人言 —— `5bnImG`

来源于**卦签-签筒布局.txt**。该文件记录 64 根卦签的摆放次序，包含纵横排列的签位编号。题面"有人记辞，有人只记点画"暗示需要关注签文内容的特定位置（点画即笔画）。

**提取原理：** 忽略签筒的整体排列，只取第 3、6、9、12、15、18 号签对应签辞的首字符，拼接成 6 字符字符串。这种方法对应"取边角、不取中"的思路。

#### ③ 地盘 —— `4yFuUc`

来源于**卦签-签文图案.bmp**。位图中隐藏了六爻卦象信息，通过分析 BMP 文件每行像素的奇偶校验位，提取隐写数据。题面"有人只记点画"即指向位图的像素点。

**提取原理：** 提取 BMP 每行像素末尾 LSB（最低有效位）数据，每 8 位为一组，每 6 组抽取一次有效字符，获取 6 个字符。此过程需要忽略文件头的误导性元数据（与 `should_start_in_meta` 相反）。

#### ④ 时令 —— `4Y0nV9`

来源于**时令-漏刻记录.csv**。CSV 文件包含了 24 节气对应的漏刻时间数值。题面"有人信时刻，有人信节候"即指向节气与时间的对应关系。

**提取原理：** 取 24 节气中有"节"无"气"的 12 个节气（立春、惊蛰、清明、立夏、芒种、小暑、立秋、白露、寒露、立冬、大雪、小寒），取其时间数值的小数部分的前两位映射到 Base64 表，再按"时令"顺序重组得到 6 个字符。

### 碎片拼接与中间密钥

按题面**天→人→地→时**的顺序拼接四段碎片：

```
mid = "qW2O0z" + "5bnImG" + "4yFuUc" + "4Y0nV9"
    = "qW2O0z5bnImG4yFuUc4Y0nV9"
```

计算 MD5 哈希值，作为 `窥得天机.zip` 的解压密码：

```python
import hashlib
mid = b"qW2O0z5bnImG4yFuUc4Y0nV9"
password = hashlib.md5(mid).hexdigest()
# password = "228a53da12c42a65235ca2ebefa826c1"
```

---

## 0x02 窥机：ZIP 注释索引隐写

解压 `窥得天机.zip` 后，得到 64 个按编号排列的 TXT 文件（`0.txt` ~ `63.txt`）。关键线索藏在压缩包的 **Comment（注释）** 字段中。

### 提取 ZIP Comment

使用 `zipfile` 模块读取注释内容：

```python
with zipfile.ZipFile("窥得天机.zip", "r") as zf:
    comment = zf.comment.decode()
# comment = "q7LxP0aR9Yv+u1kC3wFjI2sQmD4oJ6GfXr5hN8KpTtUVeBylHcSgZdWiEOAbMn/z"
```

该字符串正好 64 个字符，且全部落在标准 Base64 字符集 `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/` 中。

### 映射规则

- 注释字符串中第 `i` 个字符，在 Base64 表中查询其位置索引 `idx`
- 打开第 `i` 个 TXT 文件（按文件编号排序），取该文件中下标为 `idx` 的字符
- 64 个文件 × 64 个注释字符 → 拼接出 64 字符的密码

| 索引 i | Comment[i] | Base64 位置 idx | TXT 文件 | 提取字符 |
|--------|-----------|----------------|---------|---------|
| 0 | `q` | 42 | 0.txt | `U` |
| 1 | `7` | 59 | 1.txt | `Q` |
| 2 | `L` | 11 | 2.txt | `C` |
| ... | ... | ... | ... | ... |

### 代码实现

```python
import zipfile, os, re

b64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

with zipfile.ZipFile("窥得天机.zip", "r") as zf:
    comment = zf.comment.decode()

# 读取并排序 64 个 TXT 文件
files = sorted(
    [f for f in os.listdir("out/") if f.endswith(".txt")],
    key=lambda x: int(re.findall(r"\d+", x)[0])
)

seven_pwd = ""
for i, c in enumerate(comment):
    idx = b64.index(c)
    with open(f"out/{files[i]}", "r") as f:
        seven_pwd += f.read()[idx]

# seven_pwd = "UQC8TBH7FkJn7bmz7ikjttXfwjvsp99CHBWmH7+M9HxppE7W7a68mo/Ua4cfQUq2"
```

> **为什么选择 Base64 作为索引表？**
>
> 注释字符串的 64 个字符恰好是 Base64 字符集的子集，与解压出的 64 个文件形成一一映射。由此推断这是一个"查表—定位—取值"的索引隐写方案，而非直接编码。

---

## 0x03 终局：AES-CBC 解密

用上一步得到的 `seven_pwd` 解压 `终局.7z`，得到 `终局.txt`，内容为一段 Base64 编码的密文：

```
7jgRTVRxS/HSsI673SWW2yglLJbYZq295x7Eu6qCEvymWnnhkwyDg/8CduA2gQpF
```

### 密钥推导

| 参数 | 取值 | 来源 |
|------|------|------|
| **AES Key** | `qW2O0z5bnImG4yFu` | `mid[:16]` —— 中间密钥前 16 字节 |
| **AES IV** | `UQC8TBH7FkJn7bmz` | `seven_pwd[:16]` —— 索引密码前 16 字节 |
| **加密模式** | AES-CBC (PKCS7 Padding) | 标准对称加密，CBC 模式需 IV |
| **密文编码** | Base64 | `终局.txt` 存储格式 |

### 解密实现

使用 `pycryptodome` 库完成解密：

```python
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

mid = b"qW2O0z5bnImG4yFuUc4Y0nV9"
seven_pwd = b"UQC8TBH7FkJn7bmz7ikjttXfwjvsp99CHBWmH7+M9HxppE7W7a68mo/Ua4cfQUq2"

key = mid[:16]
iv = seven_pwd[:16]
ct = b64decode("7jgRTVRxS/HSsI673SWW2yglLJbYZq295x7Eu6qCEvymWnnhkwyDg/8CduA2gQpF")

flag = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16)
print(flag.decode())
```

---

## 0x04 最终 Flag

```
ISCC{cd1e6a3c-8348-4d9e-a26c-59c269004f84}
```

---

## 0x05 技术总结与出题思路分析

### 阶段拆解

| 阶段 | 技术点 | 难度评级 | 关键突破 |
|------|--------|---------|---------|
| 一：四象碎片提取 | 隐写分析、SVG/BMP/CSV 解析 | ★★★★☆ | 识别干扰项、多样化隐写手法 |
| 二：ZIP 注释隐写 | 索引映射、Base64 查表 | ★★★☆☆ | 发现 Comment 字段、建立单射关系 |
| 三：AES 解密 | 对称加密、密钥截取 | ★★☆☆☆ | 正确推断 Key/IV 拼接方式 |

### 出题亮点

1. **多层嵌套结构**：四象碎片 → MD5 → ZIP 注释 → 索引映射 → 7z 密码 → AES 解密，层层递进
2. **真实的误导机制**：多处 Base64 仅用于"看起来像密码"，实质内容完全无关；Flag 格式字符串实为干扰
3. **多样化的隐写手法**：同一题目融入了图形（BMP LSB）、文本（签文定位）、数学（洛书幻方）、时间序列（节气漏刻）四种隐写方式
4. **密钥来源对称性**：Key 取自第一阶段 mid，IV 取自第二阶段 seven_pwd，两个阶段的成果在最终环节结合，设计精妙

### 可替代的解题方案

- 若无法直接解析 SVG，可手动绘制洛书九宫后按方位对应关系推算
- 可使用 `cryptography` 库替代 `pycryptodome` 进行 AES 解密
- ZIP 注释索引隐写也可通过 `binwalk` 或 `hexdump` 发现并手动提取
