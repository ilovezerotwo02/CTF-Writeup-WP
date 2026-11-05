---
title: "ScatterRSA"
ctf: "Unknown / local challenge set"
date: 2026-05-30
category: crypto
difficulty: medium
points: 300
flag_format: "flag{...}"
author: "Codex"
---

# ScatterRSA

## Summary

This is a textbook `e=3` broadcast-style RSA challenge with known linear padding:
`c_i = (a_i * m + b_i)^3 mod n_i`. Because the same plaintext is sent across three
different moduli and the linear masks are public, we can combine the three
congruences with CRT and recover the small root with an LLL-based Coppersmith step.

## Solution

### Step 1: Merge the three padded RSA equations

For each channel, define:

```text
f_i(x) = (a_i * x + b_i)^3 - c_i  (mod n_i)
```

Use CRT on each coefficient to build a single cubic polynomial `f(x) (mod N)` with
`N = n1 * n2 * n3`, such that the real message `m` satisfies:

```text
f(m) == 0 (mod N)
```

This is exactly the setting of Hastad's broadcast attack with linear padding.

### Step 2: Recover the small root with LLL

Build a small Coppersmith lattice from:

```text
N, xN, x^2N, f(x), x f(x), x^2 f(x)
```

Then run LLL, turn the shortest vectors back into integer polynomials, isolate
their integer roots, and test each candidate against the original three
congruences.

```python
import re
from pathlib import Path

import mpmath as mp
from sympy import Poly, symbols
from sympy.ntheory.modular import crt


mp.mp.dps = 300
x = symbols("x")


def dot(u, v):
    total = mp.mpf("0")
    for a, b in zip(u, v):
        total += mp.mpf(a) * mp.mpf(b)
    return total


def nearest_integer(value):
    return int(mp.nint(value))


def gram_schmidt(basis):
    rows = len(basis)
    cols = len(basis[0])
    mu = [[mp.mpf("0") for _ in range(rows)] for _ in range(rows)]
    orth = [[mp.mpf("0") for _ in range(cols)] for _ in range(rows)]
    norms = [mp.mpf("0") for _ in range(rows)]

    for i in range(rows):
        vec = [mp.mpf(entry) for entry in basis[i]]
        for j in range(i):
            if norms[j] == 0:
                continue
            mu[i][j] = dot(basis[i], orth[j]) / norms[j]
            for k in range(cols):
                vec[k] -= mu[i][j] * orth[j][k]
        orth[i] = vec
        norms[i] = dot(vec, vec)
    return mu, norms


def lll_reduce(basis, delta=mp.mpf("0.75")):
    basis = [row[:] for row in basis]
    size = len(basis)
    k = 1
    mu, norms = gram_schmidt(basis)

    while k < size:
        for j in range(k - 1, -1, -1):
            q = nearest_integer(mu[k][j])
            if q:
                basis[k] = [bk - q * bj for bk, bj in zip(basis[k], basis[j])]
        mu, norms = gram_schmidt(basis)
        if norms[k] >= (delta - mu[k][k - 1] ** 2) * norms[k - 1]:
            k += 1
        else:
            basis[k], basis[k - 1] = basis[k - 1], basis[k]
            mu, norms = gram_schmidt(basis)
            k = max(k - 1, 1)
    return basis


def parse_output(path):
    values = {}
    pattern = re.compile(r"^([a-z]\d*|e)\s*=\s*(\d+)$")
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            values[match.group(1)] = int(match.group(2))
    return values


def verify_root(root, a_vals, b_vals, c_vals, n_vals, exponent):
    return all(
        pow(a_vals[i] * root + b_vals[i], exponent, n_vals[i]) == c_vals[i]
        for i in range(len(n_vals))
    )


def recover_message(data):
    exponent = data["e"]
    n_vals = [data[f"n{i}"] for i in range(1, 4)]
    a_vals = [data[f"a{i}"] for i in range(1, 4)]
    b_vals = [data[f"b{i}"] for i in range(1, 4)]
    c_vals = [data[f"c{i}"] for i in range(1, 4)]

    modulus = n_vals[0] * n_vals[1] * n_vals[2]
    local_polys = [
        Poly((a_vals[i] * x + b_vals[i]) ** exponent - c_vals[i], x, domain="ZZ")
        for i in range(3)
    ]

    coeffs = []
    for degree in range(exponent + 1):
        residues = [int(local_polys[i].nth(degree) % n_vals[i]) for i in range(3)]
        coeff, _ = crt(n_vals, residues)
        coeffs.append(int(coeff))

    inv_lead = pow(coeffs[exponent], -1, modulus)
    monic = [((coeffs[i] * inv_lead) % modulus) for i in range(exponent + 1)]
    f = Poly(sum(monic[i] * x**i for i in range(exponent + 1)), x, domain="ZZ")

    x_bound = 1 << 256
    lattice_polys = [Poly((x**j) * modulus, x, domain="ZZ") for j in range(exponent)]
    lattice_polys += [
        Poly((x**j) * f.as_expr(), x, domain="ZZ") for j in range(exponent)
    ]
    max_degree = max(poly.degree() for poly in lattice_polys)
    basis = [
        [int(poly.nth(k)) * (x_bound**k) for k in range(max_degree + 1)]
        for poly in lattice_polys
    ]

    reduced = lll_reduce(basis)
    for row in reduced[:3]:
        candidate_poly = Poly(
            sum((entry // (x_bound**k)) * x**k for k, entry in enumerate(row)),
            x,
            domain="ZZ",
        )
        for interval, _ in candidate_poly.intervals():
            lo, hi = map(int, interval)
            for root in {lo, hi}:
                if root < 0:
                    continue
                if verify_root(root, a_vals, b_vals, c_vals, n_vals, exponent):
                    return root

    raise ValueError("failed to recover the message")


data = parse_output("output.txt")
m = recover_message(data)
flag = m.to_bytes((m.bit_length() + 7) // 8, "big").decode()
print(flag)
```

Actual output:

```text
flag{d3e053494a1280f3cff1c22c170069c0}
```

## Flag

```text
flag{d3e053494a1280f3cff1c22c170069c0}
```
