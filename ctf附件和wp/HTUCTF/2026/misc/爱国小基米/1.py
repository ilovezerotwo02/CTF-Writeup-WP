from pathlib import Path
from zipfile import ZipFile

ZIP_PATH = Path("哈基米南北绿豆.zip")

# 读取 ZIP 内的 txt，无需关心压缩包里文件名的编码形式
with ZipFile(ZIP_PATH) as zf:
    txt_name = next(name for name in zf.namelist() if name.lower().endswith(".txt"))
    data = zf.read(txt_name).decode("utf-8").strip()

ternary = {"哈": 0, "基": 1, "米": 2}

# 第一层：三进制编码单元 -> Unicode 汉字
pos = 0
stage1 = []
lengths = {6: 0, 9: 0, 12: 0}

while pos < len(data):
    header = data[pos:pos + 3]
    assert len(header) == 3
    r = 3 * ternary[header[0]] + ternary[header[1]]
    kind = (ternary[header[2]] - r) % 3
    n = (6, 9, 12)[kind]
    pos += 3

    block = data[pos:pos + n]
    assert len(block) == n, "编码块长度不足"
    pos += n

    digits = "".join(str(ternary[c]) for c in block)
    shifted = digits[r:] + digits[:r]  # 循环左移 r 位
    codepoint = int(shifted, 3) - 3 - r
    stage1.append(chr(codepoint))
    lengths[n] += 1

core_text = "".join(stage1)
print("原始字符数：", len(data))
print("第一层字符数：", len(core_text))
print("各数据长度统计：", lengths)
print("第一层开头：", core_text[:40])

# 第二层：核心价值观词组 -> 十六进制 -> 明文
alphabet = "富强民主文明和谐自由平等公正法治爱国敬业诚信友善"
phrases = [alphabet[i:i + 2] for i in range(0, len(alphabet), 2)]
lookup = {word: i for i, word in enumerate(phrases)}

assert len(core_text) % 2 == 0
values = [lookup[core_text[i:i + 2]] for i in range(0, len(core_text), 2)]

hex_digits = []
i = 0
while i < len(values):
    value = values[i]
    i += 1
    if value == 10 or value == 11:
        next_value = values[i]
        i += 1
        value = (10 if value == 10 else 6) + next_value
    assert 0 <= value <= 15
    hex_digits.append(format(value, "x"))

hex_text = "".join(hex_digits)
flag = bytes.fromhex(hex_text).decode("utf-8")
print("Flag：", flag)
