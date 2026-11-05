# -*- coding: utf-8 -*-
import lib, unicodedata, re, time, sys

CANDS = {
    "fullwidth": "ａｄｍｉｎ",
    "smallcaps": "\u1d00\u1d05\u1d0d\u026a\u0274",
    "mathbold": "\U0001d41a\U0001d41d\U0001d426\U0001d422\U0001d427",
    "circled": "\u24d0\u24d9\u24dc\u24d8\u24dd",
    "modifier": "\u1d43\u1d44\u1d50\u1d35\u207f",
    "roman1": "adm\u2170n",
    "cyrillic_a": "\u0430dmin",
    "dotless_i": "adm\u0131n",
    "greek": "\u03b1dmin",
    "enclosed": "\u249c\u249f\u24a2\u24a0\u24a3",
    "fw_partial": "a\uff44min",
    "fw_admin_mixed": "\uff41dmin",
    "superscript": "\u1d43\u1d44\u1d50\u2071\u207f",
    "tag": "\U000e0061\U000e0064\U000e006d\U000e0069\U000e006e",
    "mono": "\U0001d670\U0001d673\U0001d67c\U0001d678\U0001d67d",
    "script": "\U0001d4b6\U0001d4b9\U0001d4c2\U0001d4be\U0001d4c3",
    "fraktur": "\U0001d51e\U0001d521\U0001d52a\U0001d526\U0001d52b",
    "double": "\U0001d56e\U0001d571\U0001d57a\U0001d576\U0001d57b",
    "sans": "\U0001d5ba\U0001d5bd\U0001d5c6\U0001d5c2\U0001d5c7",
    "sansbold": "\U0001d5ee\U0001d5f1\U0001d5fa\U0001d5f6\U0001d5fb",
    "sansi": "\U0001d622\U0001d625\U0001d62e\U0001d62a\U0001d62f",
    "parenthesized": "\u249c\u249f\u24a2\u24a0\u24a3",
    "squared": "\U0001f130\U0001f133\U0001f136\U0001f136",
}


def nfkc(s):
    try:
        return unicodedata.normalize("NFKC", s)
    except Exception:
        return "?"


def mkuser(u):
    op = lib.sess()
    pw = "Pw" + str(int(time.time() * 1000) % 100000)
    s, h, b = lib.req(op, "/register", {"username": u, "password": pw}, "POST")
    t = lib.clean(b)
    st = "TAKEN" if "已被占用" in t else ("OK" if "开户成功" in t else t[:40])
    return op, pw, st, t[:80]


def try_login(u, pw):
    op = lib.sess()
    s, h, b = lib.req(op, "/login", {"username": u, "password": pw}, "POST")
    t = lib.clean(b)
    m = re.search(r"我的账户（(.*?)）", t)
    emp = "员工通道" in t
    return ("我的账户" in t), (m.group(1) if m else ""), emp, t[:90]


print("### 控制组：注册全角名，看能否用 ASCII 名登录（说明入库做了 NFKC）")
ctl = "ｚｑ" + str(int(time.time()) % 10000)
op, pw, st, t = mkuser(ctl)
print("  reg", repr(ctl), st, "nfkc=", repr(nfkc(ctl)))
if st == "OK":
    ok, who, emp, tt = try_login(nfkc(ctl), pw)
    print("  login(ascii normalized)", repr(nfkc(ctl)), "->", ok, who)
    ok, who, emp, tt = try_login(ctl, pw)
    print("  login(raw)", repr(ctl), "->", ok, who, "EMP=", emp)

print()
print("### 同形字注册 admin 影子")
for name, u in CANDS.items():
    n = nfkc(u)
    op, pw, st, t = mkuser(u)
    line = f"  {name:18s} {u!r:20s} nfkc={n!r:12s} reg={st}"
    if st == "OK":
        ok, who, emp, tt = try_login(u, pw)
        line += f" | login_raw ok={ok} as={who!r} EMP={emp}"
        ok2, who2, emp2, tt2 = try_login("admin", pw)
        line += f" | login_admin={ok2} as={who2!r} EMP={emp2}"
        if n and n != u:
            ok3, who3, emp3, tt3 = try_login(n, pw)
            line += f" | login_nfkc ok={ok3} as={who3!r} EMP={emp3}"
    print(line)
