import urllib.request, urllib.parse, http.cookiejar, re, time, json, base64

BASE = "http://103.163.47.230:33663"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(p, data=None, method=None, hdrs=None, o=op):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    h = {}
    if body is not None:
        h["Content-Type"] = "application/x-www-form-urlencoded"
    h.update(hdrs or {})
    r = urllib.request.Request(BASE + p, data=body, headers=h, method=method)
    try:
        resp = o.open(r, timeout=15)
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, {}, str(e)


u = "s" + str(int(time.time()) % 100000)
pw = "pw123456"
req("/register", {"username": u, "password": pw})
req("/login", {"username": u, "password": pw})
print("cookies:")
for c in cj:
    print("  ", c.name, "=", c.value[:200])

print("\nroute enum (POST):")
for p in ["/withdraw", "/deposit", "/transfer", "/convert", "/exchange", "/recharge",
          "/work", "/salary", "/employee", "/staff", "/promote", "/upgrade",
          "/buy_flag", "/buy_hint", "/reset", "/delete", "/profile", "/me",
          "/settings", "/withdraw_cash", "/cash", "/gold", "/bank", "/vip"]:
    s, h, b = req(p, {}, "POST")
    if s != 404:
        print(f"   {p:20s} {s} {re.sub('<[^>]+>',' ',b)[:150]}")

print("\nroute enum (GET):")
for p in ["/withdraw", "/deposit", "/transfer", "/profile", "/me", "/settings", "/vip",
          "/staff", "/employee", "/admin", "/panel", "/manage", "/users", "/db", "/backup",
          "/static/", "/templates/", "/secret", "/config", "/.env", "/proc"]:
    s, h, b = req(p, method="GET")
    if s != 404:
        print(f"   {p:20s} {s} {re.sub('<[^>]+>',' ',b)[:120]}")
