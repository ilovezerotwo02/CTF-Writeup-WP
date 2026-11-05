
import re
import sys
import os

from Crypto.Util.number import long_to_bytes, bytes_to_long, inverse


def load_params(path: str) -> dict:
    """从题目脚本里抓 p/q/e/c（只在注释块里出现也无所谓，正则全局扫）。"""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()

    params = {}
    for name in ("p", "q", "e", "c"):
        # 匹配  p = 12345   /   'p = 12345'  /   print(f'p = {...}')
        m = re.findall(rf"\b{name}\s*=\s*(\d+)", src)
        if not m:
            raise SystemExit(f"[-] 没在 {path} 里找到 {name}")
        params[name] = int(m[-1])  # 取最后一处（注释里那组输出值）
    return params


def rsa_decrypt_with_pq(p: int, q: int, e: int, c: int):
    n = p * q
    assert p * q == n
    assert (p - 1) * (q - 1) > e

    phi = (p - 1) * (q - 1)
    d = inverse(e, phi)

    # CRT 加速：m1 = c^dp mod p, m2 = c^dq mod q
    dp, dq = d % (p - 1), d % (q - 1)
    q_inv = inverse(q, p)
    m1 = pow(c, dp, p)
    m2 = pow(c, dq, q)
    h = (q_inv * (m1 - m2)) % p
    m = m2 + h * q

    return n, d, m


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "Ez_rsa.py")

    prm = load_params(path)
    p, q, e, c = prm["p"], prm["q"], prm["e"], prm["c"]

    n, d, m = rsa_decrypt_with_pq(p, q, e, c)

    pt = long_to_bytes(m)
    flag = pt.decode("utf-8", errors="replace")

    print(f"[+] target file : {path}")
    print(f"[+] n  bitlen   : {n.bit_length()}")
    print(f"[+] p  bitlen   : {p.bit_length()}   q bitlen: {q.bit_length()}")
    print(f"[+] e           : {e}")
    print(f"[+] d           : {d}")
    print(f"[+] plaintext   : {pt!r}")

    # 回代校验，确认没解错
    assert pow(bytes_to_long(flag.encode()), e, n) == c, "回代校验失败"
    print("[+] verify      : pow(m, e, n) == c  OK")

    hit = re.search(rb"[A-Za-z0-9_]{2,20}\{[^}]{0,200}\}", pt)
    print(f"[!] FLAG        : {hit.group().decode() if hit else flag}")


if __name__ == "__main__":
    main()
