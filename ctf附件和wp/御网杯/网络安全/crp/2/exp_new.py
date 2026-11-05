import itertools
import re
from pathlib import Path

import mpmath as mp
from sympy import Poly, symbols

y = symbols("y")
mp.mp.dps = 350


# ------------------------------------------------------------
#  vector helpers (mpmath high‑precision)
# ------------------------------------------------------------

def vec_add(u, v, s=1):
    return [a + s * b for a, b in zip(u, v)]


def vec_mul_scalar(u, c):
    return [c * a for a in u]


def inner(u, v):
    s = mp.mpf("0")
    for a, b in zip(u, v):
        s += mp.mpf(a) * mp.mpf(b)
    return s


def nearest_int(v):
    return int(mp.nint(v))


# ------------------------------------------------------------
#  high‑precision Gram–Schmidt  (in‑place style)
# ------------------------------------------------------------

def gram_schmidt_rows(basis):
    n = len(basis)
    m = len(basis[0])
    mu = [[mp.mpf("0")] * n for _ in range(n)]
    bstar = [[mp.mpf("0")] * m for _ in range(n)]
    bsq = [mp.mpf("0")] * n

    for i in range(n):
        w = [mp.mpf(v) for v in basis[i]]
        for j in range(i):
            if bsq[j] == 0:
                continue
            mu[i][j] = inner(basis[i], bstar[j]) / bsq[j]
            w = vec_add(w, bstar[j], -mu[i][j])
        bstar[i] = w
        bsq[i] = inner(w, w)
    return mu, bsq, bstar


# ------------------------------------------------------------
#  LLL (delta = 0.99 — cleaner reduction)
# ------------------------------------------------------------

def lll(basis):
    b = [row[:] for row in basis]
    delta = mp.mpf("0.99")
    sz = len(b)
    k = 1
    mu, norms, _ = gram_schmidt_rows(b)

    while k < sz:
        for j in range(k - 1, -1, -1):
            q = nearest_int(mu[k][j])
            if q:
                b[k] = vec_add(b[k], b[j], -q)
        mu, norms, _ = gram_schmidt_rows(b)

        cond = norms[k] >= (delta - mu[k][k - 1] ** 2) * norms[k - 1]
        if cond:
            k += 1
        else:
            b[k], b[k - 1] = b[k - 1], b[k]
            mu, norms, _ = gram_schmidt_rows(b)
            k = max(k - 1, 1)
    return b


# ------------------------------------------------------------
#  manual CRT  (avoid sympy.crt to keep things different)
# ------------------------------------------------------------

def crt_combine(residues, moduli):
    value = 0
    modulus = 1
    for r, m in zip(residues, moduli):
        #  find t such that  (value + modulus * t) ≡ r (mod m)
        target = (r - value) % m
        inv = pow(modulus % m, -1, m)
        t = (target * inv) % m
        value = value + modulus * t
        modulus = modulus * m
    return value % modulus, modulus


# ------------------------------------------------------------
#  I/O
# ------------------------------------------------------------

def load_challenge(path):
    text = Path(path).read_text(encoding="utf-8").strip()
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z]\d*|e)\s*=\s*(\d+)$", line.strip())
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


# ------------------------------------------------------------
#  main recovery (Coppersmith variant — Hastad broadcast with
#  linear padding)
# ------------------------------------------------------------

def solve(data):
    e = data["e"]
    if e != 3:
        raise ValueError("only e=3")

    n_list = [data[f"n{i}"] for i in (1, 2, 3)]
    a_list = [data[f"a{i}"] for i in (1, 2, 3)]
    b_list = [data[f"b{i}"] for i in (1, 2, 3)]
    c_list = [data[f"c{i}"] for i in (1, 2, 3)]

    # ----------  step 1:  expand each local cubic  ----------
    # (a_i*y + b_i)^3  ≡  c_i  (mod n_i)
    #  →  coeffs: [constant, y^1, y^2, y^3]

    cubics = []  # list of  (modulus, [c0,c1,c2,c3])
    for a, b, c, n in zip(a_list, b_list, c_list, n_list):
        c0 = (b**3 - c) % n
        c1 = (3 * a * b**2) % n
        c2 = (3 * a**2 * b) % n
        c3 = (a**3) % n
        cubics.append((n, [c0, c1, c2, c3]))

    # ----------  step 2:  CRT across moduli per degree  ----------
    big_n = 1
    for n in n_list:
        big_n *= n

    global_coeffs = []
    for deg in range(4):
        residues = [coeffs[deg] for _, coeffs in cubics]
        val, _ = crt_combine(residues, n_list)
        global_coeffs.append(val % big_n)

    # ----------  step 3:  monic polynomial  ----------
    lead_inv = pow(global_coeffs[3], -1, big_n)
    monic = [(c * lead_inv) % big_n for c in global_coeffs]

    # ----------  step 4:  Coppersmith lattice (3×3 shift set) ----------
    #  Standard Howgrave‑Graham for monic cubic f(y) mod big_n
    #  shifts:  big_n, big_n*y, big_n*y^2,  f, y*f, y^2*f

    B = 1 << 256                    # root < 2^256

    shifts = []
    for shift in range(3):
        row = [0] * 6
        row[shift] = big_n
        shifts.append(row)

    for shift in range(3):
        #  f(y) * y^shift
        row = [0] * 6
        for d in range(4):          # degree of f is 3
            row[d + shift] = monic[d]
        shifts.append(row)

    #  apply scaling  B^k
    mat = []
    for row in shifts:
        scaled = [coeff * (B ** k) for k, coeff in enumerate(row)]
        mat.append(scaled)

    # ----------  step 5:  LLL ----------
    reduced = lll(mat)

    # ----------  step 6:  extract candidate roots ----------
    for r in reduced[:3]:
        #  un‑scale row back to integer coefficients
        coeffs = [int(c) // (B ** k) for k, c in enumerate(r)]
        poly = Poly(sum(c * y**k for k, c in enumerate(coeffs)), y, domain="ZZ")

        for iv, _ in poly.intervals():
            lo = int(iv[0])
            hi = int(iv[1])
            for cand in {lo, hi}:
                if cand <= 0:
                    continue
                # full cross‑check against three original equations
                ok = True
                for a, b, c, n in zip(a_list, b_list, c_list, n_list):
                    if pow((a * cand + b) % n, e, n) != c:
                        ok = False
                        break
                if ok:
                    return cand

    raise RuntimeError("root not found")


# ------------------------------------------------------------
def main():
    params = load_challenge(Path(__file__).with_name("output.txt"))
    msg_int = solve(params)
    raw = msg_int.to_bytes((msg_int.bit_length() + 7) // 8, "big")
    print(raw.decode())


if __name__ == "__main__":
    main()
