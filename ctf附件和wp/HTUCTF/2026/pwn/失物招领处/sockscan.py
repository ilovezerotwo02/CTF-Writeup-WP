"""筛 SOCKS5 代理：能 CONNECT 到靶机端口并收到 banner，且能继续收发。"""
import concurrent.futures as cf
import socket, socks, sys

HOST, PORT = "103.163.47.230", 34424
CAND = [l.strip() for l in open(r"D:\桌面\htu\_s5.txt") if l.strip()]


def test(hp):
    h, p = hp.rsplit(":", 1)
    try:
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, h, int(p), rdns=True)
        s.settimeout(6)
        s.connect((HOST, PORT))
        b = s.recv(200)
        if b"\xe6\xa0\xa1" not in b and b"======" not in b:   # 校园
            s.close()
            return None
        s.sendall(b"1\n")
        b2 = s.recv(400)
        s.close()
        if b"\xe8\xaf\xb7" in b2 or b">" in b2:
            return hp, len(b), len(b2)
    except Exception:
        return None
    return None


cands = [c for c in CAND if c.rsplit(":", 1)[1] in ("1080", "1081", "1082", "1083", "9050", "4145", "1085", "1086", "1087", "1088")]
print("socks 候选", len(cands))
with cf.ThreadPoolExecutor(30) as ex:
    for r in ex.map(test, cands[:300]):
        if r:
            print("HIT", r, flush=True)
print("done")
