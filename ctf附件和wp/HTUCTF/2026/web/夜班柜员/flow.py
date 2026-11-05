import urllib.request, urllib.parse, http.cookiejar, re, sys, time

BASE = "http://103.163.47.230:33663"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                 urllib.request.HTTPRedirectHandler())
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(p, data=None, hdrs=None, method=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    h = {}
    if body is not None:
        h["Content-Type"] = "application/x-www-form-urlencoded"
    h.update(hdrs or {})
    r = urllib.request.Request(BASE + p, data=body, headers=h, method=method)
    try:
        resp = op.open(r, timeout=15)
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, {}, str(e)


def clean(b):
    b = re.sub(r"<style.*?</style>", "", b, flags=re.S)
    b = re.sub(r"<script.*?</script>", "", b, flags=re.S)
    b = re.sub(r"<[^>]+>", " ", b)
    b = re.sub(r"&[a-z#0-9]+;", " ", b)
    return re.sub(r"\s+", " ", b).strip()


def raw(p, data=None, method=None, hdrs=None, n=3000):
    s, h, b = req(p, data, hdrs, method)
    print(f"--- {p} -> {s}")
    print(clean(b)[:n])
    return s, h, b


if __name__ == "__main__":
    import random
    u = sys.argv[1] if len(sys.argv) > 1 else "u" + str(int(time.time()) % 100000)
    pw = sys.argv[2] if len(sys.argv) > 2 else "pw123456"
    print("=== register", u)
    raw("/register", {"username": u, "password": pw}, "POST")
    print("=== login", u)
    raw("/login", {"username": u, "password": pw}, "POST")
    print("=== dashboard")
    s, h, b = req("/dashboard")
    print(clean(b))
    print("RAW HTML (forms/links):")
    for m in re.finditer(r"<(form|a|button|input)[^>]*>", b):
        print("   ", m.group(0)[:220])
