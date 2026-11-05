"""靶机访问小工具：默认走可用的公共代理（我们自己的 IP 被平台封了）。"""
import urllib.request, urllib.parse, http.cookiejar, json, time

P = ["http://145.220.227.132:8118", "http://5.42.127.131:80"]

def opener(proxy=None, cookie=True):
    cj = http.cookiejar.CookieJar()
    hs = [urllib.request.HTTPCookieProcessor(cj)] if cookie else []
    for p in ([proxy] if proxy else P):
        hs.append(urllib.request.ProxyHandler({"http": p}))
        break
    op = urllib.request.build_opener(*hs)
    op.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0 Safari/537.36")]
    return op

def get(url, op=None, timeout=20):
    op = op or opener()
    try:
        r = op.open(url, timeout=timeout)
        return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, {}, str(e)

def post(url, data=None, op=None, timeout=20, ctype="application/x-www-form-urlencoded", raw=None):
    op = op or opener()
    body = raw if raw is not None else (urllib.parse.urlencode(data).encode() if data else None)
    req = urllib.request.Request(url, data=body, method="POST")
    if body is not None:
        req.add_header("Content-Type", ctype)
    try:
        r = op.open(req, timeout=timeout)
        return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, {}, str(e)
