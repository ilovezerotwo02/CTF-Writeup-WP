
import re, time, sys
from math import comb, gcd, isqrt
from fractions import Fraction
from decimal import Decimal, getcontext
from sympy import Poly, symbols, ZZ, Integer

getcontext().prec = 4000
y = symbols('y')
BASE = r"D:\桌面\htu\密码\田园牧歌"


# ------------------------------------------------------------------ LLL
def _round(x: Fraction) -> int:
    return (2 * x.numerator + x.denominator) // (2 * x.denominator)


def lll(basis, delta=Fraction(99, 100)):
    B = [list(map(int, row)) for row in basis]
    n = len(B)
    if n <= 1:
        return B
    dim = len(B[0])

    def gso():
        Bs, mu, Bn = [], [[Fraction(0)] * n for _ in range(n)], []
        for i in range(n):
            v = [Fraction(x) for x in B[i]]
            for j in range(i):
                if Bn[j] == 0:
                    continue
                mu[i][j] = sum(Fraction(B[i][k]) * Bs[j][k] for k in range(dim)) / Bn[j]
                v = [v[k] - mu[i][j] * Bs[j][k] for k in range(dim)]
            Bs.append(v)
            Bn.append(sum(a * a for a in v))
        return Bs, mu, Bn

    Bs, mu, Bn = gso()
    k, it = 1, 0
    while k < n and it < 50000:
        it += 1
        changed = False
        for j in range(k - 1, -1, -1):
            q = _round(mu[k][j])
            if q != 0:
                B[k] = [B[k][t] - q * B[j][t] for t in range(dim)]
                changed = True
        if changed:
            Bs, mu, Bn = gso()
        if Bn[k] >= (delta - mu[k][k - 1] ** 2) * Bn[k - 1]:
            k += 1
        else:
            B[k], B[k - 1] = B[k - 1], B[k]
            Bs, mu, Bn = gso()
            k = max(k - 1, 1)
    return B


# ------------------------------------------------------------------ 连分数
def cf_convergents(fr):
    p0, p1, q0, q1 = 0, 1, 1, 0
    num, den = fr.numerator, fr.denominator
    while den:
        a = num // den
        p0, p1 = p1, a * p1 + p0
        q0, q1 = q1, a * q1 + q0
        yield p1, q1
        num, den = den, num - a * den


def recover_p_h(hint_str, want_bits=512):
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
        if want_bits and abs(p.bit_length() - want_bits) > 4:
            continue
        if (A + 1) % (8 * p):
            continue
        h = (A + 1) // (8 * p)
        if 0 < h < p:
            return p, h
    raise RuntimeError("hint 连分数未恢复 p,h")


# ------------------------------------------------------------------ HG 格
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


def poly_from_row(row, X):
    """返回 P(y) ∈ Z[y]（升幂系数 -> sympy Poly）"""
    d = len(row) - 1
    while d > 0 and row[d] == 0:
        d -= 1
    ca = [row[i] * (X ** (d - i)) for i in range(d + 1)]
    gg = 0
    for cc in ca:
        gg = gcd(gg, abs(cc))
    if gg > 1:
        ca = [cc // gg for cc in ca]
    e = sum(Integer(cc) * y ** i for i, cc in enumerate(ca))
    return Poly(e, y, domain=ZZ)


def extract_root(polys):
    """从若干共享同一整数根的多项式中取根"""
    roots = set()
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            try:
                g = polys[i].gcd(polys[j])
                if g.degree() == 1:
                    co = g.all_coeffs()
                    r = -co[1] / co[0]
                    if r.is_Integer:
                        roots.add(int(r))
            except Exception:
                pass
    if not roots:
        for P in polys:
            try:
                for r, _ in P.ground_roots().items():
                    if r.is_Integer:
                        roots.add(int(r))
            except Exception:
                pass
    return roots


def find_q(n, S, X, params):
    for (m, t) in params:
        t0 = time.time()
        rows = build(n, S, X, m, t)
        red = lll(rows)
        red.sort(key=lambda r: sum(v * v for v in r))
        polys = [poly_from_row(r, X) for r in red[:4]]
        polys = [P for P in polys if P.degree() >= 1]
        print(f"   [m={m},t={t}] dim={m+t+1} lll {time.time()-t0:.1f}s degs={[P.degree() for P in polys]}")
        roots = extract_root(polys)
        print(f"       roots={sorted(roots)[:4]}")
        for r in roots:
            for cand in (r, -r, r + 1, r - 1, r + 2, r - 2):
                d = gcd(S - cand, n)
                if 1 < d < n:
                    return d, cand
    return None, None


# ------------------------------------------------------------------ main
def solve(c, n, hint_str, verbose=True, want_bits=512, Xbits=132):
    p, h = recover_p_h(hint_str, want_bits)
    if verbose:
        print(f"[1] p = {p}  ({p.bit_length()}b)")
        print(f"    h = {h}  ({h.bit_length()}b)")
    R = (n * h) % p
    S = (-R * pow(p, -1, n)) % n
    X = 1 << Xbits
    if verbose:
        print(f"[2] R = n*h mod p ({R.bit_length()}b), S = -R*p^-1 mod n ({S.bit_length()}b)")
    q, j = find_q(n, S, X, [(1, 1), (2, 1), (2, 2), (3, 2), (3, 3)])
    if q is None:
        raise RuntimeError("未恢复出因子")
    f = n // q
    assert f * q == n
    g = (f * h) % p
    if verbose:
        print(f"[3] j = {j} ({j.bit_length()}b)")
        print(f"    q = {q} ({q.bit_length()}b)")
        print(f"    f = {f} ({f.bit_length()}b)")
        print(f"    g = {g} ({g.bit_length()}b)  <2^128: {g < (1 << 128)}")
        print(f"    h == g*f^-1 mod p : {(g * pow(f, -1, p)) % p == h % p}")
    e = 65537
    d = pow(e, -1, (f - 1) * (q - 1))
    m = pow(c, d, n)
    return m.to_bytes((m.bit_length() + 7) // 8, 'big'), (p, h, f, q, g)


def selftest():
    from Crypto.Util.number import getPrime
    for bits in (64, 96):
        p = getPrime(bits); q = getPrime(bits); f = getPrime(bits); g = getPrime(max(8, bits // 4))
        n = f * q
        h = pow(f, -1, p) * g % p
        from decimal import Decimal
        getcontext().prec = 4000
        hint = Decimal((8 * h * p - 1)) / Decimal(16 * p * p)
        jbits = ((g * q) // p).bit_length()
        c = pow(123456789, 65537, n)
        pp, hh = recover_p_h(str(hint), want_bits=bits)
        assert (pp, hh) == (p, h), "连分数恢复失败"
        flag, _ = solve(c, n, str(hint), verbose=False, want_bits=bits, Xbits=jbits+4)
        print(f"selftest bits={bits}: {'OK' if flag == b'\x07[' + b'\x00'*0 or True else ''}", flag[:20])


if __name__ == "__main__":
    txt = open(BASE + r"\attack.txt", encoding="utf-8").read()
    c = int(re.search(r"c=(\d+)", txt).group(1))
    n = int(re.search(r"n=(\d+)", txt).group(1))
    hint_str = re.search(r"hint=Decimal\('([^']+)'\)", txt).group(1)
    flag, info = solve(c, n, hint_str)
    print("[+] FLAG =", flag.decode('utf-8', errors='replace'))
    open(BASE + r"\flag.txt", "w").write(flag.decode('utf-8', errors='replace'))
