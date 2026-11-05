
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

P = 112693480841240579684880016842662081173570772522470050854859284408885200781311
D = 3
AAD = b"HTUCTF-PellDH-v1"
COORD_SIZE = (P.bit_length() + 7) // 8

G = (45529683599522671022807596340652114484610686148579805997571708664068043366186,
     97804930605010306693199213047832149890713809638166431210272334335371650039546)
P_A = (25210898330666257160269417738891143099325031526283155943258955320320603608114,
       60209046686157198283029668316148935102046630738066331763771668975959351988557)
P_B = (43761926894242056144597425018268874989824262080133637207574576666775847709836,
       71192165764830168217434466682847559421795521162317121018560227035787797149639)

nonce = bytes.fromhex("3c85acdd7abe939d73796d5a")
ciphertext = bytes.fromhex("ebeba90bdf56ca578379d28ade0e637e34361bb071f5f79cb4b61c1f")
tag = bytes.fromhex("7432eeb657177934c4ce89f864be2a19")

# 素数幂分解: 2^15 与 7 个 35-bit 素数
PRIME_POWERS = [(2, 15), (21880660013, 1), (19386034781, 1), (25626614479, 1),
                (18117811853, 1), (29077022453, 1), (21613218131, 1), (27786452483, 1)]


def add(P1, P2):
    x1, y1 = P1
    x2, y2 = P2
    return ((x1 * x2 + D * y1 * y2) % P, (x1 * y2 + x2 * y1) % P)


def mul(P1, scalar):
    result = (1, 0)
    addend = P1
    while scalar:
        if scalar & 1:
            result = add(result, addend)
        addend = add(addend, addend)
        scalar >>= 1
    return result


def neg(P1):
    x, y = P1
    return (x, (-y) % P)


def bsgs(base, target, order):
    """Solve k*base = target for k in [0, order)."""
    if target == (1, 0):
        return 0
    m = int(order ** 0.5) + 1
    table = {}
    cur = (1, 0)
    for j in range(m):
        table[cur] = j
        cur = add(cur, base)
    # target - i*m*base
    factor = mul(base, m)
    factor_neg = neg(factor)
    cur = target
    for i in range(m + 1):
        if cur in table:
            k = i * m + table[cur]
            if k < order:
                return k
        cur = add(cur, factor_neg)
    raise ValueError(f"bsgs failed order={order}")


def dlp_prime_power(base, target, q, e):
    """求 k mod q^e，使 k*base = target。逐位提升。"""
    Nq = q ** e
    # 先降到 q 阶子群解 k0
    cof = Nq // q
    k = bsgs(mul(base, cof), mul(target, cof), q)
    # Hensel 提升：k_{i+1} = k_i + t*q^i
    for i in range(1, e):
        # target - k*base = t * q^i * base  (mod q^{i+1} 阶意义)
        # 即 (target - k*base) * (N/q^{i+1}) = t * (base * (N/q)) * q^{i-1}? 直接用:
        # base_q = (N/q^{i+1})*base 阶为 q^{i+1} 不方便。
        # 令 Gq = (N/q^{i+1})*base，阶 q^{i+1}；解 t 使 k+t*q^i 匹配。
        pass
    return k, Nq


def pohlig_hellman(base, target):
    """Solve k*base = target where ord(base) | N = prod PRIME_POWERS."""
    N = 1
    for q, e in PRIME_POWERS:
        N *= q ** e
    assert mul(base, N) == (1, 0), "base order does not divide N"

    residues, moduli = [], []
    for q, e in PRIME_POWERS:
        qe = q ** e
        # 在阶为 q^e 的子群上直接 BSGS（最大 2^15=32768，很快）
        cof = N // qe
        base_q = mul(base, cof)
        target_q = mul(target, cof)
        kq = bsgs(base_q, target_q, qe)
        assert mul(base_q, kq) == target_q, f"verify fail q={q}"
        residues.append(kq)
        moduli.append(qe)

    # CRT（模两两互素）
    x, M = 0, 1
    for m in moduli:
        M *= m
    for ai, mi in zip(residues, moduli):
        Mi = M // mi
        x += ai * Mi * pow(Mi, -1, mi)
    return x % M


def derive_key(shared_point):
    x, _ = shared_point
    return hashlib.sha256(x.to_bytes(COORD_SIZE, "big")).digest()


def main():
    print("[*] 验证群阶 ...")
    N = 1
    for q, e in PRIME_POWERS:
        N *= q ** e
    print("    N =", N, "p+1 =", P + 1, "match:", N == P + 1)

    print("[*] Pohlig-Hellman 求 a (P_A = a*G) ...")
    a = pohlig_hellman(G, P_A)
    print("    a =", a)
    check = mul(G, a)
    print("    验证:", check == P_A)

    if check != P_A:
        print("[*] 改求 b (P_B = b*G) ...")
        b = pohlig_hellman(G, P_B)
        print("    b =", b)
        assert mul(G, b) == P_B
        shared = mul(P_A, b)
    else:
        shared = mul(P_B, a)
    print("[*] shared point =", shared)

    key = derive_key(shared)
    print("[*] key =", key.hex())
    pt = AESGCM(key).decrypt(nonce, ciphertext + tag, AAD)
    print("[+] FLAG =", pt.decode())


if __name__ == "__main__":
    main()
