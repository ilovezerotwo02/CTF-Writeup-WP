import urllib.request, urllib.parse, http.cookiejar, re, time, sys

BASE = "http://103.163.47.230:33663"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(p, data=None, method=None, hdrs=None):
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


u = "h" + str(int(time.time()) % 100000)
pw = "pw123456"
print(req("/register", {"username": u, "password": pw}, "POST")[1] and "reg ok")
s, b = req("/login", {"username": u, "password": pw}, "POST")
print(clean(b)[:400])

for hid in ("hint1", "hint2"):
    s, b = req("/buy_hint", {"hint_id": hid}, "POST")
    print(f"\n=== buy_hint {hid} -> {s}")
    print(clean(b)[:1500])

print("\n=== buy_flag")
s, b = req("/buy_flag", {}, "POST")
print(s, clean(b)[:800])
