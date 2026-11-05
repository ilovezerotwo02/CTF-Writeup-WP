import os
from hashlib import sha256

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Util.number import getRandomRange
from gmpy2 import invert, is_prime, legendre, next_prime, powmod

from secret import flag

BITS = 256
SMALL = 5000
MID = (2 ** 38, 2 ** 39)

O = None
p = b = 0


def ec_add(P, Q):
    if P is O:
        return Q
    if Q is O:
        return P
    (x1, y1), (x2, y2) = P, Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return O
    if P == Q:
        lam = 3 * x1 * x1 * invert(2 * y1, p) % p
    else:
        lam = (y2 - y1) * invert(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    return int(x3), int((lam * (x1 - x3) - y1) % p)


def ec_mul(k, P):
    R = O
    while k:
        if k & 1:
            R = ec_add(R, P)
        P = ec_add(P, P)
        k >>= 1
    return R


def gen_p():
    while True:
        mid = int(getRandomRange(*MID))
        if not is_prime(mid):
            continue
        n = 12 * mid
        fac = {2: 2, 3: 1, mid: 1}
        while n.bit_length() < BITS:
            q = int(next_prime(getRandomRange(2, SMALL)))
            n *= q
            fac[q] = fac.get(q, 0) + 1
        if (n - 1).bit_length() == BITS and is_prime(n - 1):
            return int(n - 1), fac


def rand_point():
    while True:
        x = int(getRandomRange(0, p))
        rhs = (x * x * x + b) % p
        if rhs == 0:
            return x, 0
        if legendre(rhs, p) == 1:
            y = int(powmod(rhs, (p + 1) // 4, p)) 
            if y * y % p == rhs:
                return x, y

def main():
    global p, b
    p, fac = gen_p()
    b = int(getRandomRange(2, 1000))
    n = p + 1 

    while True:
        G = rand_point()
        if ec_mul(n, G) is O and all(ec_mul(n // q, G) is not O for q in fac):
            break

    d = int(getRandomRange(2, n))
    Q = ec_mul(d, G)

    key = sha256(str(d).encode()).digest()
    enc = AES.new(key, AES.MODE_ECB).encrypt(pad(flag.encode(), 16))

    with open("attack.txt", "w") as file:
        file.write(f"{p=}\na = 0\n{b=}\n{G=}\n{Q=}\nenc = {enc.hex()}")
        file.close()


if __name__ == "__main__":
    main()
