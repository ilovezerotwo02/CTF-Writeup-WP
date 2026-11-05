"""通过 HTTP 代理的 CONNECT 隧道连靶机（我们出口 IP 被平台 REJECT，只能走代理）。

用法:
    from tunnel import tunnel
    s = tunnel("103.163.47.230", 34424)       # 返回已建连的 socket
"""
import socket

PROXIES = [
    "143.246.138.227:80",
    "5.42.127.131:80",
    "112.216.54.226:12121",
    "47.91.29.151:81",
]


def tunnel(host, port, proxies=None, timeout=10):
    last = None
    for hp in (proxies or PROXIES):
        ph, pp = hp.rsplit(":", 1)
        try:
            s = socket.create_connection((ph, int(pp)), timeout=timeout)
            req = ("CONNECT %s:%d HTTP/1.1\r\nHost: %s:%d\r\n\r\n" % (host, port, host, port)).encode()
            s.sendall(req)
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = s.recv(1024)
                if not chunk:
                    break
                buf += chunk
            head = buf.split(b"\r\n\r\n")[0]
            if b" 200" in head:
                return s, hp, head
            s.close()
            last = (hp, head[:80])
        except Exception as e:
            last = (hp, repr(e))
    raise RuntimeError("所有代理都失败: %r" % (last,))


if __name__ == "__main__":
    import sys
    h, p = sys.argv[1], int(sys.argv[2])
    s, used, head = tunnel(h, p)
    print("via", used, head.split(b"\r\n")[0])
    s.settimeout(5)
    try:
        print("recv:", s.recv(4096))
    except Exception as e:
        print("recv err", e)
