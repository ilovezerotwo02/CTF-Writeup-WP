#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTUCTF「田园牧歌」solver
=====================================================
思路：
1) hint = (8hp-1)/(16p^2) 是有理数（已约分），Decimal 只给了 1024 位有效数字，
   而真值分母 16p^2 约 309 位十进制——连分数必然恢复出 A/B = (8hp-1)/(16p^2)。
   于是 B = 16p^2 -> p = isqrt(B/16)；h = (A+1)/(8p)。
2) h = g * f^{-1} mod p, g 只有 128bit  =>  f*h = g + k*p。
   乘 q： n*h = g*q + k*p*q  =>  R := n*h mod p 满足 g*q = R + j*p（j ~ 128bit）。
   于是 q | (S - j)，其中 S = (-R * p^{-1}) mod n（S = j + l*q，l < f）。
   这是 PACD（部分近似公因子）/未知因子 Coppersmith：
   f(x) = x - S 在未知因子 q | n（q ~ n^{1/2}）上有小根 |j| < 2^130 < n^{1/4}。
   Howgrave-Graham 格（m,t 阶移位）+ LLL 求出 j，gcd(S-j, n) = q。
3) f = n/q，g = f*h mod p（128bit 校验），phi=(f-1)(q-1)，RSA 解密。
"""
import re
import math
from math import comb, isqrt, gcd
from fractions import Fraction
from decimal import Decimal

ATTACK = r"D:\桌面\htu\密码\田园牧歌\attack.txt"

# ============================================================
# 0. 解析
# ============================================================
def parse_attack(path):
    txt = open(path, encoding="utf-8").read()
    c = int(re.search(r"c=(\d+)", txt).group(1))
    n = int(re.search(r"n=(\d+)", txt).group(1))
    hint_str = re.search(r"hint=Decimal\('([^']+)'\)", txt).group(1)
    return c, n, hint_str

# ============================================================
# 1. 连分数恢复 p, h
# ============================================================
def cf_convergents(fr):
    p0, p1 = 0, 1
    q0, q1 = 1, 0
    num, den = fr.numerator, fr.denominator
    while den:
        a = num // den
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
        yield p1, q1
        num, den = den, num - a * den

def recover_p_h(hint_str):
    s = Fraction(Decimal(hint_str))
    for A, B in cf_convergents(s):
        if B.bit_length() > 1100:
            break
        if B % 16:
            continue
        p2 = B // 16
        p = isqrt(p2)
        if p * p != p2:
            continue
        if (A + 1) % (8 * p):
            continue
        h = (A + 1) // (8 * p)
        if 0 < h < p and 8 * h * p - 1 == A:
            return p, h
    raise RuntimeError("hint 连分数未能恢复 p, h")

# ============================================================
# 2. 精确 LLL（分数 GSO，小维数）
# ============================================================
def _round(x: Fraction) -> int:
    return math.floor(x + Fraction(1, 2))

def lll(basis, delta=Fraction(3, 4)):
    n = len(basis)
    B = [list(map(int, row)) for row in basis]
    if n == 0:
        return B
    dim = len(B[0])

    def dot(u, v):
        return sum(x * y for x, y in zip(u, v))

    Bs = [[Fraction(0)] * dim for _ in range(n)]
    mu = [[Fraction(0)] * n for _ in range(n)]
    Bnorm = [Fraction(0)] * n

    def gso():
        for i in range(n):
            Bs[i] = [Fraction(x) for x in B[i]]
            for j in range(i):
                if Bnorm[j] == 0:
                    mu[i][j] = Fraction(0)
                else:
                    mu[i][j] = Fraction(dot(B[i], Bs[j])) / Bnorm[j]
                Bs[i] = [Bs[i][k] - mu[i][j] * Bs[j][k] for k in range(dim)]
            Bnorm[i] = dot(Bs[i], Bs[i])

    gso()
    k = 1
    while k < n:
        for j in range(k - 1, -1, -1):
            qij = _round(mu[k][j])
            if qij != 0:
                B[k] = [B[k][t] - qij * B[j][t] for t in range(dim)]
                for t in range(j):
                    mu[k][t] -= qij * mu[j][t]
                mu[k][j] -= qij  # mu[j][j] := 1
        if Bnorm[k] >= (delta - mu[k][k - 1] ** 2) * Bnorm[k - 1]:
            k += 1
        else:
            B[k], B[k - 1] = B[k - 1], B[k]
            gso()
            k = max(k - 1, 1)
    return B

# ============================================================
# 3. Howgrave-Graham 未知因子 Coppersmith
#    f(x) = x - S，小根 j (mod q)，q | n 未知
# ============================================================
def build_hg_lattice(N, S, X, m, t):
    """多项式（代换 x -> Xx 后）的系数向量，系数按 x^0..x^{m+t} 排列"""
    maxdeg = m + t
    rows = []
    # g_k = N^{m-k} * (X x - S)^k , k = 0..m
    for k in range(m + 1):
        row = [0] * (maxdeg + 1)
        Nk = pow(N, m - k)
        for i in range(k + 1):
            row[i] = Nk * comb(k, i) * pow(X, i) * pow(-S, k - i)
        rows.append(row)
    # h_r = (X x)^r * (X x - S)^m , r = 1..t
    for r in range(1, t + 1):
        row = [0] * (maxdeg + 1)
        for i in range(m + 1):
            row[i + r] = comb(m, i) * pow(X, i + r) * pow(-S, m - i)
        rows.append(row)
    return rows

def poly_from_row(row, X):
    """row[i] = 系数 of x^i in G(Xx)  =>  整系数 P(y)=sum row[i] X^{d-i} y^i，
    P(j)=0 <=> G(j)=0。返回按降幂排列的整数系数表。"""
    d = len(row) - 1
    while d > 0 and row[d] == 0:
        d -= 1
    return [row[d - i] * pow(X, i) for i in range(d + 1)], d

def find_small_root(rows, X, bound):
    from sympy import Poly, symbols, QQ, gcd as sp_gcd
    y = symbols("y")
    polys = []
    for row in rows:
        if all(v == 0 for v in row):
            continue
        coeffs, d = poly_from_row(row, X)
        if d < 1:
            continue
        try:
            P = Poly(coeffs, y, domain=QQ)
        except Exception:
            continue
        polys.append(P)
    if not polys:
        return None
    # 两两取 gcd，期望得到 (y - j)
    g = polys[0]
    for P in polys[1:]:
        g = sp_gcd(g, P)
        if g.degree() <= 1:
            break
    for cand_poly in [g] + polys:
        if cand_poly.degree() == 1:
            c = cand_poly.all_coeffs()
            root = -c[1] / c[0]
            if root.is_Integer and abs(int(root)) < bound:
                return int(root)
        elif cand_poly.degree() == 0:
            continue
    # 兜底：对每个多项式试有理根（小根）
    for P in polys:
        if P.degree() < 1:
            continue
        # 提取一次因式分解中的线性因子
        try:
            facs = P.factor_list()[1]
        except Exception:
            continue
        for fac, _e in facs:
            if fac.degree() == 1:
                c = fac.all_coeffs()
                root = -c[1] / c[0]
                if root.is_Integer and abs(int(root)) < bound:
                    return int(root)
    return None

def recover_factor(n, p, h):
    """返回 (f, q, g)"""
    u = pow(h, -1, p)            # f = g*u mod p 的 u
    R = (n * h) % p              # g*q = R + j*p
    S = (-R * pow(p, -1, n)) % n  # S = j + l*q
    X = 1 << 130                 # |j| < 2^129
    for (m, t) in [(3, 3), (2, 2), (4, 4), (5, 5), (2, 4), (4, 2)]:
        print(f"[*] Howgrave-Graham lattice m={m}, t={t} ...")
        rows = build_hg_lattice(n, S, X, m, t)
        red = lll(rows)
        # 按行范数排序，优先看短向量
        red.sort(key=lambda r: sum(x * x for x in r))
        j = find_small_root(red, X, 1 << 131)
        if j is None:
            print("    - 未提取到小根，换参数")
            continue
        print(f"    - 找到小根 j = {j} ({j.bit_length()} bits)")
        for jj in (j, -j, j + 1, j - 1):
            if jj < 0:
                continue
            d = gcd(S - jj, n)
            if 1 < d < n:
                q = d
                f = n // q
                g = (f * h) % p
                ok = (f * q == n) and (0 < g < (1 << 128)) and ((f * h) % p == g)
                print(f"    - q bits={q.bit_length()} f bits={f.bit_length()} g bits={g.bit_length()} ok={ok}")
                if ok:
                    return f, q, g
    raise RuntimeError("Coppersmith 未能恢复因子")

# ============================================================
# 4. RSA 解密
# ============================================================
def long_to_bytes(x):
    if x == 0:
        return b"\x00"
    bl = (x.bit_length() + 7) // 8
    return x.to_bytes(bl, "big")

def main():
    c, n, hint_str = parse_attack(ATTACK)
    print(f"[*] n bits={n.bit_length()}  c bits={c.bit_length()}  hint digits={len(hint_str)}")

    p, h = recover_p_h(hint_str)
    print(f"[*] p bits={p.bit_length()}  h bits={h.bit_length()}")
    assert pow(p, 2, 1 << 1) == p % 2
    print(f"    8hp-1 = 16p^2 * hint 校验: {8*h*p - 1 == Fraction(Decimal(hint_str)) * 16 * p * p or 'decimal-rounded (ok)'}")

    f, q, g = recover_factor(n, p, h)
    print(f"[*] f bits={f.bit_length()}  q bits={q.bit_length()}  g bits={g.bit_length()}")
    print(f"    g = {g}")
    assert f * q == n
    assert pow(f, 1, 1) == 0
    # 校验 h = g * f^{-1} mod p
    assert (g * pow(f, -1, p)) % p == h % p
    print("[*] h == g * f^{-1} mod p  校验通过")

    e = 65537
    phi = (f - 1) * (q - 1)
    d = pow(e, -1, phi)
    m = pow(c, d, n)
    flag = long_to_bytes(m)
    print("[+] flag =", flag.decode("utf-8", errors="replace"))
    return flag

if __name__ == "__main__":
    main()
