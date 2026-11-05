import urllib.request, urllib.parse, http.cookiejar, re, sys

BASE = "http://103.163.47.230:33662"
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
        return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, {}, str(e)


PATHS = ["/admin", "/admin/", "/admin/login", "/admin.php", "/login", "/console",
         "/dashboard", "/panel", "/uploads", "/uploads/", "/archive", "/archive/",
         "/files", "/files/", "/static", "/static/", "/assets", "/assets/",
         "/images", "/img", "/avatars", "/avatar", "/robots.txt", "/sitemap.xml",
         "/.git/HEAD", "/.git/config", "/.env", "/index.php", "/api", "/api/",
         "/api/admin", "/api/login", "/api/user", "/api/avatar", "/api/upload",
         "/profile", "/user", "/member", "/index.php/admin", "/obsidian",
         "/lab", "/status", "/health", "/phpinfo.php", "/info.php", "/server-status",
         "/backup", "/db.sqlite", "/app.db", "/.DS_Store", "/readme.md", "/README.md",
         "/CHANGELOG.md", "/package.json", "/composer.json", "/Dockerfile",
         "/env", "/config.php", "/config.json", "/swagger", "/openapi.json",
         "/docs", "/graphql", "/graphiql", "/wp-admin", "/wp-login.php",
         "/manager", "/manage", "/system", "/internal", "/private", "/secret"]
for p in PATHS:
    s, h, b = req(p)
    if s == 404 and "Not Found" in b and len(b) < 300:
        continue
    ct = h.get("Content-Type", "")
    print(f"{p:24s} {s:4d} {ct[:30]:30s} len={len(b):6d} | {re.sub(r'<[^>]+>',' ',b)[:160].strip()[:160]}")
