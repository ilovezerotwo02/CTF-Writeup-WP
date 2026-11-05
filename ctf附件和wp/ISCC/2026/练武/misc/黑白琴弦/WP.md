# misc2 WP：RAR + 条形码多层信息 + QR + PDF 隐藏信息

## 0. 最终答案

```text
ISCC{crYWvkGgQKRJ5bW4151515}
```

本题完整链路：

```text
attachment-18.rar
  -> 解出 21 张 barcode_*.png 和 score.rar
  -> 每张 barcode 图片有三层信息：Code128 / PNG Comment / 红色通道 LSB
  -> 从三层信息中找 XhhhhhhX 格式的数据
  -> 按 A 到 U 排序，拼出 21x21 QR
  -> QR 内容是二层 RAR 密码 crYWvkGgQKRJ5bW
  -> 解开 score.rar，得到 music score.pdf
  -> PDF stream 中隐藏 KEY+numberaboveline3
  -> 读取乐谱第 3 行上方数字 4151515
  -> 拼接 flag
```

---

## 1. 文件说明

本目录结构：

```text
misc2/
├── WP.md                  # 本题详细题解
├── attachment-18.rar      # 题目附件
├── solve.py               # 修正版解题脚本
└── requirements.txt       # Python 依赖
```

`solve.py` 默认读取同目录下的 `attachment-18.rar`，所以直接进入目录运行即可。

---

## 2. 环境准备

Python 依赖：

```bash
python3 -m pip install -r requirements.txt
```

`requirements.txt` 内容：

```text
Pillow
opencv-python
numpy
```

还需要一个能解 RAR5 的命令行工具。macOS 推荐：

```bash
brew install unar
```

也可以使用 `unrar`、`rar`、`7z`、`7zz`。本 WP 附带的 `solve.py` 已经适配了 `unar`。

---

## 3. 一键运行

```bash
cd "<WP_ROOT>/misc2"
python3 solve.py
```

预期输出：

```text
ISCC{crYWvkGgQKRJ5bW4151515}
```

如果附件不在当前目录，也可以手动传路径：

```bash
python3 solve.py ./attachment-18.rar
```

---

## 4. 第一步：确认附件类型

先看文件类型：

```bash
file attachment-18.rar
```

本题显示为：

```text
RAR archive data, v5
```

说明这是 RAR5 压缩包。

可以先解压看看：

```bash
unar -no-directory -output-directory work attachment-18.rar
```

会得到：

```text
barcode_00.png
barcode_01.png
...
barcode_20.png
score.rar
```

也就是说外层 RAR 里有 21 张条形码图片和一个二层压缩包。

---

## 5. 原脚本需要改哪些地方

题目给的脚本整体思路是对的，但在本机不能直接跑通，主要有下面几个坑。

### 5.1 附件路径要改

原脚本默认：

```python
parser.add_argument("archive", nargs="?", default=str(ROOT / "attachment-18.rar"))
```

意思是默认找脚本同目录的 `attachment-18.rar`。

如果脚本和附件不在同一个目录，直接运行会找不到附件。解决方法有两个：

方法一：运行时传参：

```bash
python3 solve.py ./attachment-18.rar
```

方法二：把附件复制到脚本同目录，本 WP 就采用这种方式。

### 5.2 RAR 工具要适配

原脚本只搜索这些工具：

```python
names = ("unrar", "rar", "7z", "7zz")
```

但本机只有：

```text
unar
```

所以原脚本会报：

```text
RuntimeError: missing RAR extractor: install WinRAR/UnRAR or 7-Zip, or add it to PATH
```

修法：把 `unar` 加进去：

```python
names = ("unrar", "rar", "7z", "7zz", "unar")
```

### 5.3 `unar` 解压会多套目录

`unar` 默认遇到多个顶层文件时，可能会自动创建一个包含目录，例如：

```text
work/attachment-18/barcode_00.png
```

但脚本后续用的是：

```python
WORK.glob("barcode_*.png")
```

它期望图片直接在：

```text
work/barcode_00.png
```

所以调用 `unar` 时要加：

```bash
-no-directory
```

修正版脚本中对应逻辑：

```python
cmd = [
    str(tool),
    "-quiet",
    "-force-overwrite",
    "-no-directory",
    "-output-directory",
    str(out_dir),
]
```

### 5.4 OpenCV 读取中文路径问题

脚本里生成 QR 图片后，需要用 OpenCV 解码。

有些环境中 `cv2.imread()` 读中文路径会失败，所以修正版脚本不用 `cv2.imread(path)`，而是：

```python
qr_array = cv2.imdecode(np.frombuffer(qr_path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR)
```

这样路径里有中文也更稳。

---

## 6. 第二步：读每张 barcode 图片的三层信息

外层 RAR 解出来 21 张图片：

```text
barcode_00.png 到 barcode_20.png
```

每张图片都藏了三种信息：

1. 图片本身的 Code128 条形码
2. PNG 的 `Comment` 元数据
3. 红色通道最低位，也就是 Red LSB

### 6.1 Code128 条形码

Code128 是一种常见一维条形码。

脚本没有依赖 `zbar`，而是自己实现了一个简单的 Code128 解码器：

```python
CODE128 = (...)
CODE128_MAP = {bits: idx for idx, bits in enumerate(CODE128)}
```

解码流程大概是：

```text
取图片中间一行
  -> 黑色像素记为 1，白色像素记为 0
  -> 统计黑白 run length
  -> 按 Code128 模块宽度还原 bit 串
  -> 查 Code128 表得到字符
```

例如某张图 Code128 解出来可能是：

```text
D175b5dD
```

这种就是有用数据。

### 6.2 PNG Comment

PNG 文件是由 chunk 组成的，其中可以有 `tEXt` 文本块。

本题的脚本会找：

```python
if typ == b"tEXt" and chunk.startswith(b"Comment\x00"):
    return chunk.split(b"\x00", 1)[1].decode("latin1")
```

也就是读取 PNG 的 `Comment` 字段。

某些图片的有用数据不在条形码里，而在 `Comment` 里。

### 6.3 红色通道 LSB

LSB 是最低有效位。

这里不是 RGB 三个通道都取，而是只取红色通道：

```python
for y in range(im.height):
    for x in range(im.width):
        bits.append(im.getpixel((x, y))[0] & 1)
```

然后每 8 bit 组成 1 字节。

第一个字节表示后面字符串长度：

```python
ln = data[0]
return data[1 : 1 + ln].decode("ascii")
```

所以每张图片的红色通道 LSB 也能得到一个字符串。

---

## 7. 第三步：找出真正有用的数据

每张图有三层字符串，但不是每个字符串都有用。

真正有用的格式是：

```text
XhhhhhhX
```

含义：

```text
首尾都是同一个字母 X
中间是 6 位十六进制 hhhhhh
```

脚本判断函数：

```python
def note_tag(value: str):
    if len(value) == 8 and value[0] == value[-1] and re.fullmatch(r"[0-9a-fA-F]{6}", value[1:-1]):
        return value[0], value[1:-1]
    return None
```

例如：

```text
D175b5dD
```

解析为：

```text
label = D
hex = 175b5d
```

21 张图片最终提取到的标签和 hex 如下：

```text
A 1fc57f
B 105d41
C 17465d
D 175b5d
E 174b5d
F 105341
G 1fd57f
H 000800
I 1f71aa
J 1cb8b7
K 0f47c2
L 071b9f
M 15df8c
N 001621
O 1fd98e
P 10449f
Q 17503f
R 17557c
S 175fc8
T 1050bc
U 1fd58a
```

---

## 8. 第四步：用 21 列数据重建 QR

标签从 `A` 到 `U`，刚好是 21 个字母。

QR 版本 1 的大小就是：

```text
21 x 21
```

所以可以猜测：

```text
每个 label 对应 QR 的一列
每个 6 位 hex 是这一列的 bit 数据
```

6 位 hex 是 24 bit，但 QR 只需要 21 行，因此脚本取其中一段：

```python
for y in range(21):
    bit = y + 3
    for x, value in enumerate(values):
        black = (value >> (23 - bit)) & 1
```

为什么从 `y + 3` 开始？

因为 6 位 hex 有 24 bit，而 QR 是 21 bit，高低各可能有填充/对齐位。脚本通过观察/验证取第 3 到第 23 位能还原出正确 QR。

生成 QR 后，用 OpenCV 解码：

```python
decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(qr_array)
```

得到：

```text
crYWvkGgQKRJ5bW
```

这就是二层 `score.rar` 的密码。

---

## 9. 第五步：解二层 score.rar

用 QR 得到的密码解：

```text
score.rar
```

密码：

```text
crYWvkGgQKRJ5bW
```

解出文件：

```text
music score.pdf
```

脚本对应：

```python
pdf = out_dir / "music score.pdf"
```

---

## 10. 第六步：分析 PDF 隐藏提示

PDF 中的数据通常在 `stream ... endstream` 里。

脚本会遍历 PDF stream：

```python
for match in re.finditer(rb"<<(.*?)>>\s*stream\r?\n(.*?)\r?\nendstream", data, re.S):
```

如果 stream 字典里有：

```text
/FlateDecode
```

就用 zlib 解压。

然后找形如 PDF hex string 的内容：

```python
<4b45592b...>
```

脚本会把十六进制转成 ASCII，并寻找 `KEY+` 开头的字符串。

最终得到：

```text
KEY+numberaboveline3
```

意思是：

```text
key 是第 3 行上方的数字
```

---

## 11. 第七步：读取乐谱第 3 行上方数字

PDF 里有一张内嵌图像，脚本会把它提取出来。

核心逻辑：

```python
if b"/Subtype/Image" in dictionary:
    width = ...
    height = ...
    return Image.frombytes("L", (width, height), stream[: width * height])
```

然后截取固定区域：

```python
x0, y0, x1, y1 = 50, 390, 640, 416
crop = im.crop((x0, y0, x1, y1))
```

这个区域就是乐谱第 3 行上方数字所在的位置。

脚本不是用通用 OCR，而是针对本题的数字形状做连通域识别：

```text
如果是第一个数字 -> 4
如果宽度很窄 -> 1
否则 -> 5
```

最终识别为：

```text
4151515
```

---

## 12. 第八步：拼接 flag

QR 解出来的密码：

```text
crYWvkGgQKRJ5bW
```

PDF 第三行上方数字：

```text
4151515
```

拼起来：

```text
crYWvkGgQKRJ5bW4151515
```

套上 flag 格式：

```text
ISCC{crYWvkGgQKRJ5bW4151515}
```

---

## 13. solve.py 函数说明

```text
find_rar_tool()             查找 unrar/rar/7z/7zz/unar
extract_rar()               解 RAR，已适配 unar 的 -no-directory
png_comment()               读取 PNG Comment
extract_red_lsb_text()      提取红色通道 LSB 文本
decode_code128_png()        解 Code128 条形码
read_barcode_layers()       综合三层信息，提取 label 和 hex
qr_password_from_notes()    重建 QR 并解码出二层密码
extract_score()             用密码解 score.rar
hidden_pdf_payload()        从 PDF stream 中提取 KEY 提示
number_above_line_three()   从 PDF 图像中识别第 3 行上方数字
main()                      拼接并输出 flag
```

---

## 14. 小白排错表

| 现象 | 原因 | 解决方法 |
|---|---|---|
| `missing RAR extractor` | 没有可用 RAR 工具 | macOS 执行 `brew install unar`，或安装 `7z/unrar` |
| 解压后找不到 `barcode_*.png` | `unar` 多套了一层目录 | 使用修正版脚本，或手动加 `-no-directory` |
| `No module named 'PIL'` | 没装 Pillow | `python3 -m pip install Pillow` |
| `No module named 'cv2'` | 没装 OpenCV | `python3 -m pip install opencv-python` |
| `No module named 'numpy'` | 没装 numpy | `python3 -m pip install numpy` |
| QR 解码失败 | 21 列顺序或 bit 位置错 | 按 label `A` 到 `U` 排序，并取 `y + 3` 对应的 bit |
| PDF 提示找不到 | 没有解压 FlateDecode stream | 对 `/FlateDecode` 的 stream 做 `zlib.decompress` |

---

## 15. 题目质量评价

这题作为 Misc 题质量不错，属于“多层组合型”题目：

- 外层 RAR 给出多张图片和二层压缩包，入口清晰。
- 条形码、PNG 元数据、LSB 三层信息混合，能考察选手是否会多角度看图片。
- 21 个标签正好对应 21x21 QR，有比较自然的 aha moment。
- QR 密码解二层 RAR，再从 PDF 中找提示和数字，链路完整。

但对新手来说，环境坑比较明显：

- RAR5 工具兼容性会影响体验。
- 原脚本没有适配 `unar`，macOS 上容易失败。
- PDF 数字识别是固定坐标 + 启发式，不是通用方法，WP 里需要说明这是针对本题。

总体评价：题目思路好，步骤多但合理；如果用于比赛，建议在官方环境或提示中说明 RAR5 解压工具，避免环境问题盖过解题本身。
