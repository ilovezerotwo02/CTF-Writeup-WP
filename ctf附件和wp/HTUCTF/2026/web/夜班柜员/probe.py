import urllib.request, urllib.parse, http.cookiejar, json, sys

BASE = "http://103.163.47.230:33663"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def get(p, hdrs=None):
    req = urllib.request.Request(BASE + p, headers=hdrs or {})
    try:
        r = op.open(req, timeout=12)
        return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, {}, str(e)


def post(p, data, hdrs=None):
    body = urllib.parse.urlencode(data).encode()
    h = {"Content-Type": "application/x-www-form-urlencoded"}
    h.update(hdrs or {})
    return post_raw(p, body, h)


def post_raw(p, body, hdrs=None):
    req = urllib.request.Request(BASE + p, data=body, headers=hdrs or {})
    try:
        r = op.open(req, timeout=12)
        return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, {}, str(e)


if __name__ == "__main__":
    paths = ["/", "/register", "/login", "/dashboard", "/shop", "/buy", "/buy_hint",
             "/change_password", "/robots.txt", "/.git/config", "/static/app.py",
             "/app.py", "/source", "/api", "/flag", "/admin", "/logout", "/hint",
             "/transfer", "/vault", "/gold", "/debug", "/console", "/metrics"]
    for p in paths:
        s, h, b = get(p)
        print(f"{p:24s} {s} len={len(b)} ct={h.get('Content-Type','')} {b[:120].strip()[:120]!r}")
