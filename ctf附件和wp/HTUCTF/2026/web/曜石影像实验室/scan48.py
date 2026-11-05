import urllib.request, urllib.parse, http.cookiejar, re, itertools

BASE = "http://103.163.47.230:33662"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(p, data=None, method=None, hdrs=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    h = {"Content-Type": "application/x-www-form-urlencoded"} if body else {}
    h.update(hdrs or {})
    r = urllib.request.Request(BASE + p, data=body, headers=h, method=method)
    try:
        resp = op.open(r, timeout=12)
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, {}, str(e)


print("=== /admin POST 细节")
cj.clear()
s, h, b = req("/admin", {"username": "admin", "password": "admin"}, "POST")
print("status", s, "len", len(b))
print("headers", {k: v for k, v in h.items() if k.lower() in ("set-cookie", "location", "content-type")})
print("cookies", [(c.name, c.value[:40]) for c in cj])
m = re.search(r"<form.*?</form>", b, re.S)
print("form:", m.group(0)[:300] if m else None)
print("body head:", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b))[:300])

print("\n=== 路径扫描")
DIRS = ["admin", "assets", "static", "upload", "uploads", "archive", "archives",
        "files", "avatars", "avatar", "img", "images", "media", "data", "db",
        "api", "app", "src", "backup", "backups", "old", "tmp", "temp", "cache",
        "log", "logs", "config", "conf", "private", "internal", "secret", "hidden",
        "index", "catalog", "gallery", "photo", "photos", "picture", "thumb",
        "thumbs", "sync", "export", "profile", "user", "users", "member", "account",
        "console", "dashboard", "panel", "manage", "manager", "system", "node",
        "obsidian", "lab", "desk", "control", "records", "record", "library",
        "download", "downloads", "dist", "build", "public", "web", "site", "www",
        "cgi-bin", "scripts", "js", "css", "fonts", "vendor", "node_modules"]
FILES = ["index.php", "index.html", "login.php", "admin.php", "config.php", "db.php",
         "robots.txt", "sitemap.xml", ".htaccess", ".env", ".git/HEAD", ".gitignore",
         "readme.md", "README.md", "package.json", "composer.json", "Dockerfile",
         "flag.txt", "flag", "flag.php", "app.py", "main.py", "server.py",
         "requirements.txt", "db.sqlite", "database.db", "users.db", "backup.sql",
         "phpinfo.php", "info.php", "test.php", "upload.php", "avatar.php",
         "archive.php", "sync.php", "export.php", "profile.php", "error_log",
         "access.log", ".DS_Store", ".bash_history", "docker-compose.yml"]

found = []
for d in DIRS:
    s, h, b = req("/" + d + "/")
    if s != 404:
        print(f"  DIR /{d}/ -> {s} len={len(b)} ct={h.get('Content-Type','')[:30]}")
        found.append(("/" + d + "/", s))
    s, h, b = req("/" + d)
    if s != 404 and s != 200:
        print(f"  DIR /{d} -> {s}")

for f in FILES:
    s, h, b = req("/" + f)
    if s != 404:
        print(f"  FILE /{f} -> {s} len={len(b)} ct={h.get('Content-Type','')[:30]}")
        found.append((("/" + f), s))
