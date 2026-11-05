# -*- coding: utf-8 -*-
"""Chef 语言（Base Stew）解析：配料=字符码，Method 逐条压栈，最后输出。"""
import re, sys, base64, binascii, itertools

SRC = r"C:/Users/ASUS/WorkBuddy/htuctf/work/chef/source.txt"
text = open(SRC, encoding="utf-8").read()

ing_sec = text.split("Ingredients.")[1].split("Method.")[0]
meth_sec = text.split("Method.")[1]

# 配料： "<value> g <name>"，name 形如 "x 7" / "z"
ings = {}
for line in ing_sec.strip().splitlines():
    line = line.strip()
    if not line:
        continue
    m = re.match(r"^(\d+)\s+g\s+(.+)$", line)
    assert m, line
    ings[" ".join(m.group(2).split())] = int(m.group(1))

print("配料数 =", len(ings))

# Method：按顺序取 "Put <name> into the mixing bowl."
order = []
for line in meth_sec.strip().splitlines():
    line = line.strip().rstrip(".")
    m = re.match(r"^Put\s+(.+?)\s+into the mixing bowl$", line, re.I)
    if m:
        order.append(" ".join(m.group(1).split()))

print("Put 指令数 =", len(order))
missing = [n for n in order if n not in ings]
print("缺配料:", missing)
print("未被使用的配料:", [k for k in ings if k not in order])

push = [ings[n] for n in order]
print("值范围:", min(push), max(push))

def to_s(vals):
    return "".join(chr(v) for v in vals)

cands = {
    "push顺序": to_s(push),
    "栈顶优先(逆序)": to_s(push[::-1]),
}
for k, v in cands.items():
    print("\n==", k, "len=", len(v))
    print(repr(v[:200]))
open(r"C:/Users/ASUS/WorkBuddy/htuctf/work/chef/push.txt", "w", encoding="utf-8").write(cands["push顺序"])
open(r"C:/Users/ASUS/WorkBuddy/htuctf/work/chef/pop.txt", "w", encoding="utf-8").write(cands["栈顶优先(逆序)"])
