# 黑白琴弦 — ISCC 2025 Misc Writeup

## 题目概要

题目附件 `attachment-18.rar` 包含 21 张条形码图片和一个加密的 `score.rar`。解题过程涉及多层信息隐藏：

- 解压外层 RAR 得到 21 张 `barcode_*.png` 和 `score.rar`
- 每张条形码图片隐藏三层信息：**Code128 条形码**、**PNG Comment 元数据**、**红色通道 LSB**
- 三层信息中混有 `XhhhhhhX` 格式的标签（A~U 各一列），提取后重建 21x21 QR 码
- QR 码内容即 `score.rar` 的解压密码
- 解压得到 `music score.pdf`，其中隐藏提示 `KEY+numberaboveline3`
- 提取 PDF 内嵌图像，读取乐谱第 3 行上方数字
- 拼接得到最终 Flag

**最终 Flag:** `ISCC{aOl7MiDCty2WJE84151515}`

---

## 详细步骤

### Step 1: 解压外层 RAR

附件为 RAR5 格式：

```bash
# 可用 unar / unrar / 7z 解压
unar -no-directory -output-directory work attachment-18.rar
```

解压后得到 21 张条形码 PNG 文件和 `score.rar`：

```
barcode_00.png ~ barcode_20.png
score.rar
```

### Step 2: 条形码三层信息提取

每张 PNG 图片同时包含三种隐写数据，需要分别提取。

#### 2.1 Code128 条形码

图片中央绘制了一条 Code128 条形码。逐像素扫描图片中间行，**黑色为 1，白色为 0**，计算游程长度后按 Code128 模块宽度还原比特流，查找编码表得到字符串。

核心思路：

```
取图片中间一行像素
  -> 二值化（<128 为黑，>=128 为白）
  -> 裁剪两侧空白
  -> 游程编码 + 模块宽度估算
  -> 按 11 位为单位查 Code128 表
  -> 解码得到字符串
```

本题中大部分图片的条形码直接包含有效数据，部分图片的条形码内容是 `RmxhZz0=`（即 base64 编码的 `Flag=`），干扰项需排除。

#### 2.2 PNG Comment 元数据

PNG 文件的 `tEXt` 块中可以存储文本元数据。遍历 PNG 的所有 chunk，找到类型为 `tEXt` 且关键字为 `Comment` 的块，提取其内容：

```python
if typ == b"tEXt" and chunk.startswith(b"Comment\x00"):
    return chunk.split(b"\x00", 1)[1].decode("latin1")
```

部分图片的有效标签隐藏在 Comment 中。

#### 2.3 红色通道 LSB

每张图片的红色通道最低有效位也藏有数据。逐像素提取红色分量的最低位：

```
遍历所有像素 (x, y):
    取 R 通道的最低位
每 8 位组成一个字节
第一个字节 = 字符串长度
后续字节 = ASCII 内容
```

只有红色通道被利用，不涉及绿/蓝通道。

#### 2.4 标签识别

对三层信息提取出的所有字符串，用正则匹配 `XhhhhhhX` 格式：

```python
len(value) == 8 and value[0] == value[-1]
    and re.fullmatch(r"[0-9a-fA-F]{6}", value[1:-1])
```

匹配结果形如 `A1fc97fA`，解析为标签 `A` 和十六进制值 `1fc97f`。

**21 张图片的提取结果如下：**

| 图片 | 来源 | 标签 | 十六进制 |
|------|------|------|----------|
| barcode_00 | Code128 | C | 17595d |
| barcode_01 | Code128 | F | 104241 |
| barcode_02 | Comment | Q | 17538a |
| barcode_03 | LSB | J | 1122a6 |
| barcode_04 | LSB | O | 1fd777 |
| barcode_05 | Code128 | U | 1fd5a7 |
| barcode_06 | LSB | G | 1fd57f |
| barcode_07 | Comment | T | 105382 |
| barcode_08 | LSB | S | 175bf9 |
| barcode_09 | Comment | N | 001a27 |
| barcode_10 | LSB | H | 001800 |
| barcode_11 | LSB | E | 17465d |
| barcode_12 | LSB | L | 1abf20 |
| barcode_13 | Code128 | I | 1dffc4 |
| barcode_14 | Comment | K | 1747bb |
| barcode_15 | Code128 | P | 105109 |
| barcode_16 | LSB | M | 1a50b1 |
| barcode_17 | Comment | A | 1fc97f |
| barcode_18 | Comment | D | 174b5d |
| barcode_19 | Code128 | R | 1740f2 |
| barcode_20 | Comment | B | 104e41 |

### Step 3: 重建 QR 码

标签从 **A 到 U 刚好 21 个字母**，每个 6 位十六进制值对应 24 bit。QR 码 Version 1 的大小正是 **21×21**，每个标签对应 QR 的一列。

重建方法：

```python
# 按标签 A~U 排序
ordered = sorted(rows, key=lambda item: item["label"])
values = [int(item["hex"], 16) for item in ordered]

# 24 bit 中取中间 21 位映射到 QR 的 21 行
for y in range(21):
    bit = y + 3
    for x, value in enumerate(values):
        black = (value >> (23 - bit)) & 1
```

列标签（A~U）对应列位置，24 bit 中取第 3~23 位对应行位置。

生成 QR 码头，用 OpenCV 解码：

```python
decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(qr_array)
```

得到 `score.rar` 的密码：

```
aOl7MiDCty2WJE8
```

生成的 QR 码图片如下：

*（reconstructed_qr.png — 实际运行脚本时会自动生成）*

### Step 4: 解压 score.rar

用上一步得到的密码解压 `score.rar`：

```bash
unrar x -p"aOl7MiDCty2WJE8" score.rar
```

得到 `music score.pdf`（五线谱乐谱 PDF）。

### Step 5: PDF 隐藏提示分析

PDF 文件中的 `stream` 块可能包含压缩数据。本题 PDF 的某个 stream 使用了 `/FlateDecode`（zlib 压缩），解压后搜索 PDF 十六进制字符串格式 `<...>`：

```
<4b45592b6e756d62657261626f76656c696e6533>
```

十六进制解码得：

```
KEY+numberaboveline3
```

但这并不是完整的 flag，而是一条**提示**：告诉解题者密钥（key）在乐谱第 3 行上方。

### Step 6: 提取乐谱数字

PDF 内嵌了一张五线谱图像，将其提取出来。对图像裁切第 3 行上方区域（坐标约 `x: 50~640, y: 390~416`），得到数字区域。

使用连通域分析识别数字：

- **最左侧数字**：固定为 4（根据题目特征判断）
- **宽度 ≤ 2 像素**：识别为 1
- **其他**：识别为 5

识别结果为：

```
4151515
```

该值在不同版本的题目中保持不变。

### Step 7: 拼接 Flag

```
QR 密码: aOl7MiDCty2WJE8
乐谱数字: 4151515
```

```
Flag: ISCC{aOl7MiDCty2WJE84151515}
```

---

## 解题脚本

见 `黑白琴弦exp.py`，支持自动解压 RAR 和全链路提取。

### 使用方式

```bash
# 安装依赖
pip install Pillow opencv-python numpy

# 确保系统已安装 unrar/7z 并加入 PATH

# 运行脚本（默认读取同目录下的 attachment-18.rar）
python 黑白琴弦exp.py

# 或指定附件路径
python 黑白琴弦exp.py ./attachment-18.rar

# 或使用已解压目录（跳过 RAR 解压）
python 黑白琴弦exp.py --barcode-dir ./attachment-18
```

### 依赖清单

| 依赖 | 用途 | 安装 |
|------|------|------|
| Pillow | 图片读写、LSB 提取 | `pip install Pillow` |
| opencv-python | QR 解码 | `pip install opencv-python` |
| numpy | 图片数组转换 | `pip install numpy` |
| unrar / 7z / WinRAR | RAR 解压 | 系统安装并加入 PATH |

### 函数说明

| 函数 | 功能 |
|------|------|
| `find_rar_tool()` | 自动检测系统 RAR 解压工具 |
| `extract_rar()` | 解压 RAR（适配 unar/7z/unrar） |
| `png_comment()` | 提取 PNG Comment 元数据 |
| `extract_red_lsb_text()` | 提取红色通道 LSB 隐藏文本 |
| `decode_code128_png()` | 解码 Code128 条形码 |
| `read_barcode_layers()` | 综合三层信息提取标签 |
| `qr_password_from_notes()` | 重建 QR 码并解码 |
| `hidden_pdf_payload()` | 分析 PDF stream 获取提示 |
| `number_above_line_three()` | 提取乐谱第 3 行上方数字 |

---

## 题目设计分析

本题为典型的多层信息隐藏综合题：

- **隐写多样性**：一张图片同时使用了条形码、元数据、LSB 三种隐藏方式，考察选手对常见隐写手段的掌握
- **Aha Moment**：21 个标签 A~U 对应 QR Version 1 的 21×21 维度，发现这个对应关系是解题关键
- **多层压缩链**：RAR → 图片隐写 → QR → RAR → PDF → 图像，链路完整
- **非通用 OCR**：数字识别采用针对性的连通域分析而非通用 OCR，体现了对题目特征的利用

可能的难点：

1. **RAR5 兼容性**：部分系统需要额外安装解压工具
2. **Code128 解码**：需要自己实现条形码解码或依赖 zbar
3. **标签分布**：三层信息中混有大量干扰数据（如 base64 编码的 `RmxhZz0=`），需要准确识别目标格式
4. **QR 位偏移**：24 bit 中如何确定哪 21 位对应 QR 行需要尝试和验证
