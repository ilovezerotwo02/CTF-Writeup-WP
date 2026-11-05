import base64, hashlib, ast, re
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
    if tag == b'tEXt' and b'\x00' in body:
        k, v = body.split(b'\x00', 1)
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
all_text  = '\n'.join(texts.values()) + '\n' + trailer
m         = re.search(r'\bsensor\b', all_text, re.IGNORECASE)
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
        print('Flag:', plain.decode())
