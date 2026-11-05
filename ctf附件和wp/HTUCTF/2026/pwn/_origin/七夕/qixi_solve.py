# -*- coding: utf-8 -*-
"""
HTUCTF 2026 - qixi_gift (pwn/RE, 1000pt)

题目链路：
  本地 ELF 走 4 关（答案都藏在运行时状态里，必须用 GDB 读）：
    1. 卡片编号  -> $r12（stage_one 把 random_u64() 的返回值留在 r12）
    2. 礼物地点  -> 全局字符串 gift_place = "银桦大道第三棵树下"
    3. 丝带密码  -> main 中 random_u32() 的返回值，作为参数传给 stage_three（$edi）
    4. 礼物盒    -> 把全局变量 gift_box_open 改成 1
  全通过后打印卡片内容：
    "七夕快乐，我喜欢你。愿意和我在一起吗？"
  远程 103.163.47.230:32846 是"礼物投递员"，把这句话原样告诉它即可拿 flag。
  （也就是 flag 不需要爆破/不需要打远程二进制，只需要把这句话读出来）

运行：
  python qixi_solve.py              # 直接取 flag
  python qixi_solve.py 1.2.3.4 9999 # 指定地址
"""
import re
import socket
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "103.163.47.230"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 32846

# 卡片上的那句话（也就是 .rodata 0x2538 处的字符串）
CARD = "七夕快乐，我喜欢你。愿意和我在一起吗？"


def main():
    s = socket.create_connection((HOST, PORT), timeout=10)
    s.settimeout(5)

    def recv_all():
        data = b""
        while True:
            try:
                chunk = s.recv(4096)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        return data

    banner = recv_all().decode("utf-8", "replace")
    print(banner, end="")

    s.sendall(CARD.encode("utf-8") + b"\n")
    resp = recv_all().decode("utf-8", "replace")
    print(resp, end="")

    m = re.search(r"HTUCTF\{[^}]*\}", resp)
    if m:
        print("\n[+] FLAG =", m.group(0))
    s.close()
    return m.group(0) if m else None


if __name__ == "__main__":
    main()
