import re, hashlib, math, sys, time
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

txt = open('attack.txt', encoding='utf-8').read()
p = int(re.search(r'p=(\d+)', txt).group(1))
b = int(re.search(r'b=(\d+)', txt).group(1))
G = tuple(int(x) for x in re.search(r'G=\((\d+), (\d+)\)', txt).groups())
Q = tuple(int(x) for x in re.search(r'Q=\((\d+), (\d+)\)', txt).groups())
enc = bytes.fromhex(re.search(r'enc = ([0-9a-f]+)', txt).group(1))

O = None


def add(P, Q_):
    if P is O: return Q_
    if Q_ is O: return P
    x1, y1 = P; x2, y2 = Q_
    if x1 == x2:
        if (y1 + y2) % p == 0:
            return O
        lam = 3 * x1 * x1 % p * pow(2 * y1, p - 2, p) % p
    else:
        lam = (y2 - y1) * pow(x2 - x1, p - 2, p) % p
    x3 = (lam * lam - x1 - x2) % p
    return (x3, (lam * (x1 - x3) - y1) % p)


def mul(k, P):
    R = O
    while k:
        if k & 1: R = add(R, P)
        P = add(P, P)
        k >>= 1
    return R


def bsgs(P, T, order):
    m = math.isqrt(order) + 1
    tbl = {}
    cur = O
    for j in range(m):
        if cur is not O:
            tbl.setdefault(cur[0], j)
        cur = add(cur, P)
    # T - i*(mP)
    mP = mul(m, P)
    neg_mP = (mP[0], (-mP[1]) % p) if mP is not O else None
    gamma = T
    for i in range(m + 1):
        if gamma is O:
            return (i * m) % order
        j = tbl.get(gamma[0])
        if j is not None:
            x = (i * m + j) % order
            if mul(x, P) == T:
                return x
        gamma = add(gamma, neg_mP)
    raise ValueError('bsgs failed')


def is_prime(n):
    if n < 2: return False
    for q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % q == 0: return n == q
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2; s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1): continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1: break
        else:
            return False
    return True


n = p + 1
print('n bits', n.bit_length())

# factor n by trial division with primes < 100000
fac = []
rem = n
small = [q for q in range(2, 100000) if is_prime(q)]
for q in small:
    if rem % q == 0:
        e = 0
        while rem % q == 0:
            rem //= q; e += 1
        fac.append((q, e))
print('factors:', [(q, e) for q, e in fac])
print('remaining:', rem, 'bits', rem.bit_length(), 'prime?', is_prime(rem))
if rem > 1:
    fac.append((rem, 1))

t0 = time.time()
res = []
for q, e in fac:
    Nq = q ** e
    if Nq == 1: continue
    Gi = mul(n // Nq, G)
    Qi = mul(n // Nq, Q)
    if Gi is O:
        continue
    if Nq <= 4:
        x = 0
        cur = O
        for k in range(Nq):
            if cur == Qi: x = k; break
            cur = add(cur, Gi)
    else:
        x = bsgs(Gi, Qi, Nq)
    res.append((x, Nq))
    print(f'  q={q}^{e} -> {x}   ({time.time()-t0:.1f}s)')
    sys.stdout.flush()

# CRT
d = 0; M = 1
for x, Nq in res:
    # solve d = x mod Nq
    g = math.gcd(M, Nq)
    assert g == 1
    t = (x - d) % Nq * pow(M, -1, Nq) % Nq
    d += M * t
    M *= Nq
d %= M
print('d =', d)
assert mul(d, G) == Q, 'verify failed'
print('verify ok')

key = hashlib.sha256(str(d).encode()).digest()
pt = AES.new(key, AES.MODE_ECB).decrypt(enc)
print('flag:', unpad(pt, 16).decode())
with open('flag.txt', 'w', encoding='utf-8') as f:
    f.write(unpad(pt, 16).decode())
