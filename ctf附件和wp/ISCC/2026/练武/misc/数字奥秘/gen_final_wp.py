from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
import base64, hashlib, ast, re
from collections import Counter
from math import gcd

doc = Document()

# --- Style setup ---
style = doc.styles['Normal']
style.font.name = 'SimSun'
style.font.size = Pt(11)
style.paragraph_format.line_spacing = 1.5

# ===================================================================
# TITLE
# ===================================================================
h = doc.add_heading('', level=1)
r = h.add_run('ISCC 2026 WriteUp —— 数字奥秘')
r.font.size = Pt(18)

# ===================================================================
# BASIC INFO
# ===================================================================
doc.add_heading('题目信息', level=3)

info_items = [
    ('题目名称', '数字奥秘（Mystery of Numbers）'),
    ('题目类型', 'Misc（杂项）'),
    ('题目分值', '350'),
    ('题目描述', '真正的秘密藏在数字之间'),
]
for label, content in info_items:
    p = doc.add_paragraph()
    p.add_run(f'{label}：').bold = True
    p.add_run(content)

# ===================================================================
# SOLUTION
# ===================================================================
doc.add_heading('解题思路', level=3)

# ---- Section 1 ----
doc.add_heading('一、附件初步分析', level=4)

p = doc.add_paragraph()
p.add_run('给出的附件是一个压缩包，里面只有一个文件 challenge.bin。起初看起来是个二进制文件，但用十六进制工具（如 010 Editor）打开后，可以在文件头部看到一段很熟悉的字节：')

p = doc.add_paragraph()
code_run = p.add_run('89 50 4E 47 0D 0A 1A 0A')
code_run.font.name = 'Consolas'
code_run.font.size = Pt(10)

p = doc.add_paragraph()
p.add_run('这正是 PNG 图片的标准文件头签名。不出意外的话，这其实是一张 PNG 图片，出题人改了后缀名来迷惑选手。')

p = doc.add_paragraph()
p.add_run('【截图指引】').bold = True
p.add_run('用 010 Editor 打开 challenge.bin，在文件偏移 0x00 ~ 0x20 截一张图，圈出 89 50 4E 47 这一行作为 PNG 文件头的证据。')

# ---- Section 2 ----
doc.add_heading('二、PNG 隐藏数据提取', level=4)

p = doc.add_paragraph()
p.add_run('PNG 文件除了图像像素数据以外，还支持在 tEXt 文本块中存储任意键值对。用 Python 脚本解析 challenge.bin 的 chunk 结构，发现了以下几个关键的隐藏字段：')

p = doc.add_paragraph()
p.add_run('  (1) SYNC_CODE  —— 一段超过 31000 个字符的超长 Brainfuck 代码')
p.add_run('\n  (2) PERIODS     —— 数组 [182, 902, 1173, 822, 1145, 1654, 296, 1390]')
p.add_run('\n  (3) SYNC_HINT   —— "payload=base64;encryption=xor;key=merged_result;method=crt"')
p.add_run('\n  (4) SYNC_PAYLOAD—— 一段 Base64 编码的密文')
p.add_run('\n  (5) README      —— 四条解题指引')

p = doc.add_paragraph()
p.add_run('此外，在 PNG 的 IEND 标志之后，还有一段额外附加的文本数据，内容是出题人写的一个自定义 Brainfuck 虚拟机源码（vm.py）。')

p = doc.add_paragraph()
p.add_run('【截图指引】').bold = True
p.add_run('用 010 Editor 继续往下翻，找到第一个 tEXt 块的位置（通常在偏移 0x30 附近），截一张图展示 SYNC_CODE 和 PERIODS 两个字段的起始位置。再翻到文件末尾找到 IEND 块之后的 vm.py 源码，截图展示 VM 代码。')

# ---- Section 3 ----
doc.add_heading('三、Brainfuck VM 中的 Bug', level=4)

p = doc.add_paragraph()
p.add_run('README 中有一条提示：')
p = doc.add_paragraph()
r = p.add_run('"If data looks incorrect, check vm.py for bugs"')
r.italic = True

p = doc.add_paragraph()
p.add_run('顺着这个线索去看 vm.py 里的关键代码。VM 在处理 * 和 # 两个扩展指令时是这样写的：')

p = doc.add_paragraph()
code_run = p.add_run('''elif cmd == '*':
    self.fp_reg = self.memory[self.ptr] * 0.1   # 浮点数乘法
elif cmd == '#':
    val = int(self.fp_reg)                      # 直接用 int() 截断
    self.output.append(val)''')
code_run.font.name = 'Consolas'
code_run.font.size = Pt(9)

p = doc.add_paragraph()
p.add_run('这里 * 指令会把当前内存单元的值乘以 0.1 然后存进浮点寄存器，而 # 指令取出这个浮点数后，用 int() 直接截断取整，这就丢掉了一部分精度。')

p = doc.add_paragraph()
p.add_run('举个例子：如果内存单元里存的是 1806，乘 0.1 得到 180.6，int(180.6) = 180。但按四舍五入算的话，180.6 应当取 181。所以 int() 截断才是出题人埋的坑。')

p = doc.add_paragraph()
p.add_run('【截图指引】').bold = True
p.add_run('在 VS Code 或任意代码编辑器中打开从 challenge.bin 尾部提取出的 vm.py，找到 * 和 # 这两条指令的代码行（大约在类定义的 run 方法中间位置），截图用红框标注出 "int(self.fp_reg)" 这一行，说明这就是 Bug 所在。')

# ---- Section 4 ----
doc.add_heading('四、获得正确的传感器数据', level=4)

p = doc.add_paragraph()
p.add_run('看 SYNC_CODE 里面的内容，发现它本质上就是一大堆加号（+）加上极少量控制字符。按照 Brainfuck 的语义，一个 + 就是让当前单元格加 1，连续的 + 就是在连续累加。代码的结构大致如下：')

p = doc.add_paragraph()
r = p.add_run('++++......++++*#>++++......++++*#>......++++......++++*#')
r.font.name = 'Consolas'
r.font.size = Pt(9)
r.italic = True

p = doc.add_paragraph()
p.add_run('可以看到，代码里一共有 8 组 "许多个 + 后跟 *#>" 的结构。因此只要数出每组里面有几个加号，就得到了对应的原始单元值：')

p = doc.add_paragraph()
code_run = p.add_run('[1806, 5706, 1428, 587, 3327, 15207, 2126, 826]')
code_run.font.name = 'Consolas'
code_run.font.size = Pt(10)

p = doc.add_paragraph()
p.add_run('按照修正后的逻辑（用四舍五入代替截断，即对每个原始值做 (value + 5) // 10），得到正确的传感器读数：')

p = doc.add_paragraph()
code_run = p.add_run('[181, 571, 143, 59, 333, 1521, 213, 83]')
code_run.font.name = 'Consolas'
code_run.font.size = Pt(10)

# ---- Section 5 ----
doc.add_heading('五、中国剩余定理 CRT 合并', level=4)

p = doc.add_paragraph()
p.add_run('SYNC_HINT 里明确指出了 "method=crt" 和 "key=merged_result"。所以我们需要用中国剩余定理，把刚刚得到的 8 个传感器数值（作为余数）和 8 个 PERIODS（作为模数）合并成一个整数。')

p = doc.add_paragraph()
p.add_run('这一步建立以下同余方程组并求解：')

p = doc.add_paragraph()
code_run = p.add_run('''x ≡ 181  (mod 182)
x ≡ 571  (mod 902)
x ≡ 143  (mod 1173)
x ≡ 59   (mod 822)
x ≡ 333  (mod 1145)
x ≡ 1521 (mod 1654)
x ≡ 213  (mod 296)
x ≡ 83   (mod 1390)''')
code_run.font.name = 'Consolas'
code_run.font.size = Pt(9)

p = doc.add_paragraph()
p.add_run('经过计算（使用扩展欧几里得算法逐对合并），得到 merged_result = 1255253。')

# ---- Section 6 ----
doc.add_heading('六、构造真正的解密密钥', level=4)

p = doc.add_paragraph()
p.add_run('拿到 merged_result 之后，并不能直接拿它当 XOR 密钥。需要先构造一个"密钥材料字符串"，然后取这个字符串的 SHA256 哈希值，作为最终的 32 字节 XOR 密钥。')

p = doc.add_paragraph()
p.add_run('密钥材料的格式是：')
p.add_run('"{merged_result}:{前缀}_{关键词}_{年份}"')
p.add_run('。')

p = doc.add_paragraph()
p.add_run('其中：')
p.add_run('\n  前缀 —— 从 PNG 的 tEXt 块键名中提取。SYNC_CODE、SYNC_HINT、SYNC_PAYLOAD 的键名都以 "SYNC" 开头，所以前缀取值 "SYNC"。')
p.add_run('\n  关键词 —— 从 vm.py（PNG 尾部文本）和 README 中按词边界搜索单词 "sensor"，找到 "get sensor data" 中的 sensor，规范化为大写 "SENSOR"。')
p.add_run('\n  年份 —— 来自题目描述中的提示串，连续做多次 Base64 解码后得到 ":SYNC_SENSOR_2025"，由此确定年份为 2025。')

p = doc.add_paragraph()
p.add_run('拼在一起，最终的密钥材料字符串为：')

p = doc.add_paragraph()
code_run = p.add_run('1255253:SYNC_SENSOR_2025')
code_run.font.name = 'Consolas'
code_run.font.size = Pt(11)
code_run.bold = True

# ---- Section 7 ----
doc.add_heading('七、XOR 解密得到 Flag', level=4)

p = doc.add_paragraph()
p.add_run('把 SYNC_PAYLOAD 先做 Base64 解码，得到 38 字节的密文。然后计算 SHA256("1255253:SYNC_SENSOR_2025") 得到 32 字节密钥，用循环异或解密每一字节密文，最终明文就是 flag：')

p = doc.add_paragraph()
flag_run = p.add_run('ISCC{vSHL1ZkW7WhCVJypzsCMS8ovNIZ1cYMc}')
flag_run.font.size = Pt(14)
flag_run.font.color.rgb = RGBColor(200, 30, 30)

p = doc.add_paragraph()
p.add_run('【截图指引】').bold = True
p.add_run('在终端里运行 exp 脚本，把最后打印出 flag 的那几行截一张图即可。')

# ===================================================================
# EXP
# ===================================================================
doc.add_heading('Exp（完整解题脚本）', level=3)

exp_code = '''import base64, hashlib, ast, re
from collections import Counter
from math import gcd

# ===== 第1步：读取 challenge.bin 并解析 PNG chunk =====
with open('challenge.bin', 'rb') as f:
    data = f.read()

idx = 8                     # 跳过 PNG 签名 (8 字节)
texts = {}
trailer = ''

while idx + 8 <= len(data):
    size = int.from_bytes(data[idx:idx+4], 'big')
    tag  = data[idx+4:idx+8]
    body = data[idx+8:idx+8+size]
    if tag == b'tEXt' and b'\\x00' in body:
        k, v = body.split(b'\\x00', 1)
        texts[k.decode('latin-1')] = v.decode('latin-1')
    idx += 12 + size
    if tag == b'IEND':
        trailer = data[idx:].decode('utf-8', 'ignore')
        break

# ===== 第2步：从 SYNC_CODE 统计加号个数 =====
code   = texts['SYNC_CODE']
counts = []
cnt    = 0
for ch in code:
    if ch == '+':
        cnt += 1
    elif ch == '*':
        counts.append(cnt)
        cnt = 0

# ===== 第3步：修正版 VM — 四舍五入代替 int() 截断 =====
sensor  = [(c + 5) // 10 for c in counts]   # 等价于 round(c/10)
periods = ast.literal_eval(texts['PERIODS'])
payload = base64.b64decode(texts['SYNC_PAYLOAD'])

print('原始 + 计数 :', counts)
print('修正后传感器:', sensor)
print('周期 (PERIODS):', periods)

# ===== 第4步：中国剩余定理 (CRT) =====
def crt(remainders, moduli):
    def pair(a1, m1, a2, m2):
        g     = gcd(m1, m2)
        delta = a2 - a1
        assert delta % g == 0, 'CRT 数据不一致!'
        l = m1 // g
        r = m2 // g
        step = (delta // g * pow(l, -1, r)) % r
        return (a1 + m1 * step) % (m1 * r), m1 * r

    val, mod = 0, 1
    for a, m in zip(remainders, moduli):
        val, mod = pair(val, mod, int(a) % int(m), int(m))
    return val

merged = crt(sensor, periods)
print('merged_result =', merged)

# ===== 第5步：构造密钥材料字符串 =====
# 从 tEXt 块键名提取前缀
pre_list = [k.split('_')[0].upper() for k in texts
            if '_' in k and k.split('_')[0].isalpha()]
prefix   = Counter(pre_list).most_common(1)[0][0]

# 从尾部文本中搜索 "sensor" 关键词
all_text  = '\\n'.join(texts.values()) + '\\n' + trailer
m         = re.search(r'\\bsensor\\b', all_text, re.IGNORECASE)
word      = m.group(0).upper()

print('前缀  :', prefix)
print('关键词:', word)

# ===== 第6步：SHA256 + 循环 XOR 解密 =====
for year in range(2020, 2027):
    candidate = f'{merged}:{prefix}_{word}_{year}'
    key       = hashlib.sha256(candidate.encode()).digest()
    extended  = (key * ((len(payload) // len(key)) + 1))[:len(payload)]
    plain     = bytes(p ^ k for p, k in zip(payload, extended))

    if plain[:4] == b'ISCC' and plain[-1] == ord('}'):
        print('密钥材料:', candidate)
        print('Flag =>', plain.decode())
        break'''

p = doc.add_paragraph()
code_run = p.add_run(exp_code)
code_run.font.name = 'Consolas'
code_run.font.size = Pt(7)

# ===================================================================
# NOTES
# ===================================================================
doc.add_heading('备注', level=3)

notes = [
    '1. 直接用 challenge.bin 运行上述脚本即可得到 flag，不需要额外安装特殊库（只需 Python 标准库）。',
    '2. 如果没有 challenge.bin，而是从 zip 解压得到的，脚本也可以直接读取解压后的文件。',
    '3. 解题的关键一步是识别出 int() 截断是 bug，要用四舍五入替代。否则得到的余数每个都少了 1，CRT 结果也会不同，最终无法正确解密。',
    '4. 密钥材料中的年份 2025 既可以通过题目描述中的提示串解码获得，也可以像本脚本一样在合理范围内枚举（2020~2026），两种方式结果一致。',
]
for note in notes:
    p = doc.add_paragraph(note)

# ===================================================================
# SAVE
# ===================================================================
doc.save('数字奥秘_WP.docx')
print('Saved: 数字奥秘_WP.docx')
