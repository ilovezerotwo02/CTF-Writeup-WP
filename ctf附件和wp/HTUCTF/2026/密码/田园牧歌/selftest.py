# -*- coding: utf-8 -*-
"""小参数端到端自测：验证 HG 格 + 取根 + 分解 的完整流程"""
import time
from math import comb, gcd
from sympy import Poly, symbols, ZZ, Integer, gcd as sp_gcd
from Crypto.Util.number import getPrime
from mylll import lll

y = symbols('y')


def expr_poly(coeffs_asc):
    e = sum(Integer(co) * y ** i for i, co in enumerate(coeffs_asc))
    return Poly(e, y, domain=ZZ)


def build(N, S, X, m, t):
    d = m + t
    rows = []
    for k in range(m + 1):
        row = [0] * (d + 1)
        Nk = N ** (m - k)
        for i in range(k + 1):
            row[i] = Nk * comb(k, i) * (X ** i) * ((-S) ** (k - i))
        rows.append(row)
    for r in range(1, t + 1):
        row = [0] * (d + 1)
        for i in range(m + 1):
            row[i + r] = comb(m, i) * (X ** (i + r)) * ((-S) ** (m - i))
        rows.append(row)
    return rows


def row_to_coeffs_asc(row, X):
    d = len(row) - 1
    while d > 0 and row[d] == 0:
        d -= 1
    return [row[i] * (X ** (d - i)) for i in range(d + 1)]


def attack(n, S, X, param_list):
    for (m, t) in param_list:
        rows = build(n, S, X, m, t)
        t0 = time.time()
        red = lll(rows)
        red.sort(key=lambda r: sum(v * v for v in r))
        polys = []
        for row in red[:4]:
            ca = row_to_coeffs_asc(row, X)
            if len(ca) < 2:
                continue
            P = expr_poly(ca)
            g = 0
            for cc in P.all_coeffs():
                g = gcd(g, abs(int(cc)))
            if g > 1:
                P = Poly([int(cc) // g for cc in reversed(P.all_coeffs())], y, domain=ZZ) if False else expr_poly([int(cc) // g for cc in P.all_coeffs()])
            polys.append(P)
        print(f"   m={m},t={t}: {time.time()-t0:.1f}s degs={[P.degree() for P in polys]}")
        roots = set()
        for i in range(len(polys)):
            for j in range(i + 1, len(polys)):
                try:
                    gg = sp_gcd(polys[i], polys[j])
                    if gg.degree() == 1:
                        co = gg.all_coeffs()
                        r = -co[1] / co[0]
                        if r.is_Integer:
                            roots.add(int(r))
                except Exception as e:
                    print("     gcd err", str(e)[:50])
        print("   roots from gcd:", roots)
        for r in roots:
            for cand in (r, -r):
                d = gcd(S - cand, n)
                if 1 < d < n:
                    return d, cand, (m, t)
    return None, None, None


for bits in (64, 96):
    p = getPrime(bits); q = getPrime(bits); f = getPrime(bits); g = getPrime(max(8, bits // 4))
    n = f * q
    h = pow(f, -1, p) * g % p
    R = (n * h) % p
    S = (-R * pow(p, -1, n)) % n
    j_true = (g * q - R) // p
    assert (g * q - R) % p == 0
    assert (S - j_true) % q == 0
    X = 1 << (j_true.bit_length() + 3)
    print(f"bits={bits} n={n.bit_length()}b j={j_true.bit_length()}b X=2^{X.bit_length()-1} n^0.25=2^{n.bit_length()//4}")
    got, j, params = attack(n, S, X, [(1, 1), (2, 1), (2, 2)])
    if got is None:
        print("   FAIL")
    else:
        print(f"   OK: q correct={got==q}, j correct={j==j_true}, params={params}")
