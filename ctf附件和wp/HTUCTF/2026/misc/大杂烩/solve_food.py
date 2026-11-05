
import sys, re, base64, string

SRC = sys.argv[1] if len(sys.argv) > 1 else "好吃吗.txt"

# ---------- 1. Chef 菜谱：配料值入栈，栈顶优先输出 ----------
text = open(SRC, encoding="utf-8").read()
ing_sec = text.split("Ingredients.")[1].split("Method.")[0]
meth_sec = text.split("Method.")[1]

ingredients = {}
for line in ing_sec.strip().splitlines():
    m = re.match(r"^(\d+)\s+g\s+(.+)$", line.strip())
    if m:
        ingredients[" ".join(m.group(2).split())] = int(m.group(1))

pushes = []
for line in meth_sec.strip().splitlines():
    m = re.match(r"^Put\s+(.+?)\s+into the mixing bowl\.?$", line.strip(), re.I)
    if m:
        pushes.append(" ".join(m.group(1).split()))

s0 = "".join(chr(ingredients[n]) for n in pushes[::-1])   # 栈顶优先（LIFO）
serves = re.search(r"Serves\s+(\d+)", text)
print(f"[0] Chef: 配料 {len(ingredients)} 个 / 入碗 {len(pushes)} 次 / Serves {serves.group(1)}")
assert len(s0) == len(pushes) == int(serves.group(1))

def nbase_decode(s: str, alphabet: str) -> bytes:
    n = 0
    for ch in s:
        n = n * len(alphabet) + alphabet.index(ch)
    return n.to_bytes((n.bit_length() + 7) // 8, "big")

# ---------- 2..6 逐层解码 ----------
s1 = base64.b64decode(s0, validate=True)                      # base64
print(f"[1] base64 -> {len(s1)} 字符\n    {s1.decode()}")

s2 = nbase_decode(s1.decode(), string.digits + string.ascii_uppercase + string.ascii_lowercase)
print(f"[2] base62 -> {len(s2)} 字符\n    {s2.decode()}")

s3 = nbase_decode(s2.decode(), "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
print(f"[3] base58 -> {len(s3)} 字符\n    {s3.decode()}")

# base45 / RFC 9285：3 字符 -> 2 字节（末组可 2 字符 -> 1 字节）
B45 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"
t45, out = s3.decode(), bytearray()
for i in range(0, len(t45), 3):
    g, v = t45[i:i+3], 0
    for j, c in enumerate(g):
        v += B45.index(c) * 45 ** j
    out += bytes([v >> 8, v & 255]) if len(g) == 3 else bytes([v & 255])
s4 = bytes(out)
print(f"[4] base45 -> {len(s4)} 字符\n    {s4.decode()}")

s5 = base64.b32decode(s4.decode())
print(f"[5] base32 -> {len(s5)} 字节")

flag = s5.decode()
print("\nFLAG =", flag)
assert re.fullmatch(r"HTUCTF\{.*\}", flag)
