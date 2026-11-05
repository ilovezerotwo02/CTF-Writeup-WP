
import os
import re
import sys
import math
import time
import hashlib

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


# ----------------------------------------------------------------------------
# 1. 参数读取
# ----------------------------------------------------------------------------
def load_attack(path):
    txt = open(path, "r", encoding="utf-8", errors="ignore").read()

    def grab(pat, cast=int):
        m = re.search(pat, txt)
        if not m:
            raise SystemExit(f"[-] 解析失败，找不到 {pat}")
        return cast(m.group(1))

    p = grab(r"p\s*=\s*(\d+)")
    a = grab(r"a\s*=\s*(-?\d+)")
    b = grab(r"b\s*=\s*(-?\d+)")
    gx, gy = (int(v) for v in re.search(r"G\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", txt).groups())
    qx, qy = (int(v) for v in re.search(r"Q\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", txt).groups())
    enc = bytes.fromhex(re.search(r"enc\s*=\s*([0-9a-fA-F]+)", txt).group(1))
    return p, a, b, (gx, gy), (qx, qy), enc


# ----------------------------------------------------------------------------
# 2. 短 Weierstrass 曲线运算（a = 0 通用式，None 表示无穷远点 O）
# ----------------------------------------------------------------------------
class Curve:
    def __init__(self, p, a, b):
        self.p, self.a, self.b = p, a, b

    def on_curve(self, P):
        if P is None:
            return True
        x, y = P
        return (y * y - (x * x * x + self.a * x + self.b)) % self.p == 0

    def neg(self, P):
        return None if P is None else (P[0], (-P[1]) % self.p)

    def add(self, P, Q):
        p = self.p
        if P is None:
            return Q
        if Q is None:
            return P
        x1, y1 = P
        x2, y2 = Q
        if x1 == x2:
            if (y1 + y2) % p == 0:      # 互为逆元（含 y = 0 的自逆），结果为 O
                return None
            return self.dbl(P)
        lam = (y2 - y1) * pow(x2 - x1, -1, p) % p
        x3 = (lam * lam - x1 - x2) % p
        return (x3, (lam * (x1 - x3) - y1) % p)

    def dbl(self, P):
        p = self.p
        if P is None:
            return None
        x, y = P
        if y == 0:
            return None
        lam = (3 * x * x + self.a) * pow(2 * y, -1, p) % p
        x3 = (lam * lam - 2 * x) % p
        return (x3, (lam * (x - x3) - y) % p)

    def mul(self, k, P):
        """标量乘，支持负数；k 会自动对群阶取模（由调用方保证 P 的阶已知）。"""
        if P is None or k == 0:
            return None
        if k < 0:
            return self.mul(-k, self.neg(P))
        R = None
        Q = P
        while k:
            if k & 1:
                R = self.add(R, Q)
            Q = self.dbl(Q)
            k >>= 1
        return R


# ----------------------------------------------------------------------------
# 3. 整数分解：小素数试除 + Miller-Rabin + Pollard rho（兜底）
# ----------------------------------------------------------------------------
def is_prime(n):
    if n < 2:
        return False
    for q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47):
        if n % q == 0:
            return n == q
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41):
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def pollard_rho(n, c=1):
    if n % 2 == 0:
        return 2
    x, y, d = 2, 2, 1
    f = lambda v: (v * v + c) % n
    while d == 1:
        x = f(x)
        y = f(f(y))
        d = math.gcd(abs(x - y), n)
    return d if d != n else None


def factorize(n, limit=100000, _out=None):
    """返回 [(prime, exp), ...]；先小素数试除，剩下的大因子用 rho 拆。"""
    out = [] if _out is None else _out
    # 2 单独处理，后面只扫奇数
    e = 0
    while n % 2 == 0:
        n //= 2
        e += 1
    if e:
        out.append((2, e))
    f = 3
    while f < limit and f * f <= n:
        if n % f == 0:
            e = 0
            while n % f == 0:
                n //= f
                e += 1
            out.append((f, e))
        f += 2
    if n == 1:
        return out
    if is_prime(n):
        out.append((n, 1))
        return out
    # 大合数：rho 递归
    d = None
    c = 1
    while d is None:
        d = pollard_rho(n, c)
        c += 1
    factorize(d, limit, out)
    factorize(n // d, limit, out)
    # 合并同类项
    merged = {}
    for q, e in out:
        merged[q] = merged.get(q, 0) + e
    out.clear()
    out.extend(sorted(merged.items()))
    return out


# ----------------------------------------------------------------------------
# 4. 素数幂子群上的 DLP：BSGS
# ----------------------------------------------------------------------------
def bsgs(E, P, Q, order):
    """求 x 使 x*P = Q，其中 ord(P) = order（素数幂）。失败返回 None。"""
    m = math.isqrt(order)
    if m * m < order:
        m += 1

    # baby steps: j*P, 用 x 坐标建表（j 从小到大，保留最小 j）
    table = {}
    R = None
    for j in range(m):
        if R is not None:
            table.setdefault(R[0], j)
        R = E.add(R, P)

    # giant steps: Q - i*(m*P)
    mP = R                                  # R == m*P
    negmP = E.neg(mP)
    gamma = Q
    for i in range(m + 1):
        if gamma is None:
            cand = (i * m) % order
            return cand if E.mul(cand, P) == Q else None
        j = table.get(gamma[0])
        if j is not None:
            cand = (i * m + j) % order
            if E.mul(cand, P) == Q:         # 排除 x 相同但符号相反的碰撞
                return cand
        gamma = E.add(gamma, negmP)
    return None


def dlog_small(E, P, Q, order):
    """order 很小时直接枚举。"""
    R = None
    for k in range(order):
        if R == Q:
            return k
        R = E.add(R, P)
    return None


# ----------------------------------------------------------------------------
# 5. Pohlig-Hellman
# ----------------------------------------------------------------------------
def pohlig_hellman(E, G, Q, n, fac, verbose=True):
    residues = []
    for q, e in fac:
        qe = q ** e
        Gi = E.mul(n // qe, G)
        Qi = E.mul(n // qe, Q)
        if Gi is None:
            if Qi is not None:
                raise SystemExit(f"[-] 子群 q={q} 投影矛盾")
            continue
        t0 = time.time()
        if qe <= 64:
            x = dlog_small(E, Gi, Qi, qe)
        else:
            x = bsgs(E, Gi, Qi, qe)
        if x is None:
            raise SystemExit(f"[-] q^e = {q}^{e} 上 BSGS 失败")
        residues.append((x % qe, qe))
        if verbose:
            print(f"    q^e = {q:>6}^{e}  (~2^{qe.bit_length():.0f})  "
                  f"d ≡ {x % qe}   [{time.time() - t0:6.2f}s]")
            sys.stdout.flush()

    # CRT 拼接
    d, M = 0, 1
    for x, mod in residues:
        assert math.gcd(M, mod) == 1
        t = (x - d) % mod * pow(M, -1, mod) % mod
        d += M * t
        M *= mod
    return d % M, M


# ----------------------------------------------------------------------------
# 6. 主流程
# ----------------------------------------------------------------------------
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "attack.txt")

    p, a, b, G, Q, enc = load_attack(path)
    print(f"[+] attack      : {path}")
    print(f"[+] p           : {p}  ({p.bit_length()} bits, p mod 4 = {p % 4})")
    print(f"[+] curve       : y^2 = x^3 + {a}*x + {b}  mod p")
    print(f"[+] G on curve  : {Curve(p, a, b).on_curve(G)}")
    print(f"[+] Q on curve  : {Curve(p, a, b).on_curve(Q)}")

    E = Curve(p, a, b)
    n = p + 1                                # 超奇异：t = 0 => #E = p + 1
    assert E.mul(n, G) is None, "n*G != O，说明 #E != p+1，需要换思路"
    print(f"[+] #E = p + 1  : {n}  ({n.bit_length()} bits)  校验 n*G = O ✓")

    t0 = time.time()
    fac = factorize(n)
    print(f"[+] factorize   : " + " * ".join(f"{q}^{e}" for q, e in fac)
          + f"   [{time.time() - t0:.2f}s]")
    if any(e != 1 and q > 100000 for q, e in fac):
        print("[!] 存在大的素数幂因子，BSGS 可能较慢")
    smooth = all(q < (1 << 45) for q, _ in fac)
    print(f"[+] B-smooth    : {smooth}")

    print("[+] Pohlig-Hellman:")
    d, M = pohlig_hellman(E, G, Q, n, fac)
    print(f"[+] d           : {d}")

    # 回代校验：d*G 必须等于 Q（这是唯一可信的正确性判据）
    assert E.mul(d, G) == Q, "d*G != Q，求解失败"
    print("[+] verify      : d*G == Q  ✓")

    key = hashlib.sha256(str(d).encode()).digest()
    pt = AES.new(key, AES.MODE_ECB).decrypt(enc)
    try:
        flag = unpad(pt, 16).decode()
    except Exception:
        flag = pt.decode("utf-8", errors="replace")
        print("[!] PKCS#7 unpad 失败，输出原始明文")

    print(f"[!] FLAG        : {flag}")
    with open(os.path.join(here, "flag.txt"), "w", encoding="utf-8") as f:
        f.write(flag)


if __name__ == "__main__":
    main()
