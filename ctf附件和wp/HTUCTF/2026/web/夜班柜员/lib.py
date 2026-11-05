import urllib.request, urllib.parse, http.cookiejar, re, json, time, socket

BASE = "http://103.163.47.230:33681"
socket.setdefaulttimeout(20)


def sess():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                     urllib.request.HTTPRedirectHandler())
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op


def req(op, p, data=None, method=None, hdrs=None, raw_body=None, ctype=None):
    body = raw_body
    if body is None and data is not None:
        if isinstance(data, str):
            body = data.encode()
        else:
            body = urllib.parse.urlencode(data).encode()
    h = {}
    if body is not None:
        h["Content-Type"] = ctype or "application/x-www-form-urlencoded"
    if hdrs:
        h.update(hdrs)
    r = urllib.request.Request(BASE + p, data=body, headers=h, method=method)
    try:
        resp = op.open(r, timeout=20)
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            b = e.read().decode("utf-8", "replace")
        except Exception:
            b = ""
        return e.code, dict(e.headers), b
    except Exception as e:
        return -1, {}, str(e)


def clean(b):
    b = re.sub(r"<style.*?</style>", "", b, flags=re.S)
    b = re.sub(r"<script.*?</script>", "", b, flags=re.S)
    b = re.sub(r"<[^>]+>", " ", b)
    b = re.sub(r"&[a-z#0-9]+;", " ", b)
    return re.sub(r"\s+", " ", b).strip()


def state(op):
    s, h, b = req(op, "/dashboard")
    t = clean(b)
    m = re.search(r"我的账户（(.*?)）", t)
    d = re.search(r"(\d+) 存款余额", t)
    c = re.search(r"(\d+) 现金金币", t)
    emp = "员工通道" in t
    return (m.group(1) if m else "?"), (d.group(1) if d else "?"), (c.group(1) if c else "?"), emp


def reg(op, u, pw="pw123456"):
    s, h, b = req(op, "/register", {"username": u, "password": pw}, "POST")
    return s, clean(b)[:150]


def login(op, u, pw):
    s, h, b = req(op, "/login", {"username": u, "password": pw}, "POST")
    return s, clean(b)[:200]
