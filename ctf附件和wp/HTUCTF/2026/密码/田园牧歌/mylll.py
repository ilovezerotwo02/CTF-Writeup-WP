# -*- coding: utf-8 -*-
"""精确有理数 LLL（小维数、大整数条目可用）"""
from fractions import Fraction


def _dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def _round(x: Fraction) -> int:
    # 四舍五入
    return (2 * x.numerator + x.denominator) // (2 * x.denominator)


def lll(basis, delta=Fraction(99, 100)):
    B = [list(map(int, row)) for row in basis]
    n = len(B)
    if n <= 1:
        return B
    dim = len(B[0])

    def gso():
        Bs = []
        mu = [[Fraction(0)] * n for _ in range(n)]
        Bn = []
        for i in range(n):
            v = [Fraction(x) for x in B[i]]
            for j in range(i):
                if Bn[j] == 0:
                    mu[i][j] = Fraction(0)
                    continue
                mu[i][j] = _dot([Fraction(x) for x in B[i]], Bs[j]) / Bn[j]
                v = [v[k] - mu[i][j] * Bs[j][k] for k in range(dim)]
            Bs.append(v)
            Bn.append(_dot(v, v))
        return Bs, mu, Bn

    Bs, mu, Bn = gso()
    k = 1
    it = 0
    while k < n:
        it += 1
        if it > 20000:
            break
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


if __name__ == "__main__":
    # 小测试：验证 LLL 能找到短向量
    B = [
        [1, 1, 1],
        [-1, 0, 2],
        [3, 5, 6],
    ]
    print(lll(B))
    # 随机格
    import random
    random.seed(1)
    M = [[random.randint(-1000, 1000) for _ in range(4)] for _ in range(4)]
    R = lll(M)
    print("orig norms", [sum(x * x for x in r) for r in M])
    print("red  norms", [sum(x * x for x in r) for r in R])
