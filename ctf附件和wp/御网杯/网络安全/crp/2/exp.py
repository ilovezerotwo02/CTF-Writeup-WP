from pathlib import Path

import mpmath
from sympy import Poly, Symbol
from sympy.ntheory.modular import crt


Z = Symbol("Z")
mpmath.mp.dps = 280


class ScatterRSAExploit:
    def __init__(self, source: Path):
        self.source = source
        self.e, self.rows = self._load_case(source)

    def _load_case(self, source: Path):
        lines = [line.strip() for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
        exponent = int(lines[0].split("=")[1])
        triples = []
        cursor = 1
        while cursor < len(lines):
            block = {}
            for _ in range(4):
                left, right = lines[cursor].split("=", 1)
                block[left.strip()] = int(right.strip())
                cursor += 1
            idx = len(triples) + 1
            triples.append((block[f"n{idx}"], block[f"a{idx}"], block[f"b{idx}"], block[f"c{idx}"]))
        return exponent, triples

    def _closest(self, value):
        return int(mpmath.nint(value))

    def _inner(self, u, v):
        total = mpmath.mpf("0")
        for left, right in zip(u, v):
            total += mpmath.mpf(left) * mpmath.mpf(right)
        return total

    def _gs(self, basis):
        count = len(basis)
        width = len(basis[0])
        ortho = [[mpmath.mpf("0") for _ in range(width)] for _ in range(count)]
        proj = [[mpmath.mpf("0") for _ in range(count)] for _ in range(count)]
        norms = [mpmath.mpf("0") for _ in range(count)]

        for i in range(count):
            current = [mpmath.mpf(v) for v in basis[i]]
            for j in range(i):
                if not norms[j]:
                    continue
                proj[i][j] = self._inner(basis[i], ortho[j]) / norms[j]
                for k in range(width):
                    current[k] -= proj[i][j] * ortho[j][k]
            ortho[i] = current
            norms[i] = self._inner(current, current)
        return proj, norms

    def _lll(self, basis):
        lattice = [row[:] for row in basis]
        k = 1
        proj, norms = self._gs(lattice)
        delta = mpmath.mpf("0.75")

        while k < len(lattice):
            for j in range(k - 1, -1, -1):
                step = self._closest(proj[k][j])
                if step:
                    lattice[k] = [x - step * y for x, y in zip(lattice[k], lattice[j])]
            proj, norms = self._gs(lattice)
            lhs = norms[k]
            rhs = (delta - proj[k][k - 1] ** 2) * norms[k - 1]
            if lhs >= rhs:
                k += 1
                continue
            lattice[k], lattice[k - 1] = lattice[k - 1], lattice[k]
            proj, norms = self._gs(lattice)
            k = max(1, k - 1)
        return lattice

    def _expand_channel(self, modulus, mul, offset, cipher):
        # (mul*m + offset)^3 - cipher mod modulus
        c0 = (offset * offset * offset - cipher) % modulus
        c1 = (3 * mul * offset * offset) % modulus
        c2 = (3 * mul * mul * offset) % modulus
        c3 = pow(mul, 3, modulus)
        return [c0, c1, c2, c3]

    def _global_poly(self):
        moduli = [item[0] for item in self.rows]
        merged = []
        for degree in range(4):
            residues = []
            for modulus, mul, offset, cipher in self.rows:
                residues.append(self._expand_channel(modulus, mul, offset, cipher)[degree])
            value, _ = crt(moduli, residues)
            merged.append(int(value))

        big_n = 1
        for modulus in moduli:
            big_n *= modulus
        lead_inv = pow(merged[3], -1, big_n)
        normalized = [(coef * lead_inv) % big_n for coef in merged]
        poly = Poly(sum(normalized[i] * Z**i for i in range(4)), Z, domain="ZZ")
        return big_n, poly

    def _make_basis(self, big_n, poly, bound_bits=256):
        scale = 1 << bound_bits
        pieces = []
        for shift in range(3):
            pieces.append(Poly(big_n * (Z**shift), Z, domain="ZZ"))
        anchor = poly.as_expr()
        for shift in range(3):
            pieces.append(Poly(anchor * (Z**shift), Z, domain="ZZ"))

        limit = max(piece.degree() for piece in pieces)
        matrix = []
        for piece in pieces:
            row = []
            for power in range(limit + 1):
                row.append(int(piece.nth(power)) * (scale**power))
            matrix.append(row)
        return scale, matrix

    def _restore_poly(self, row, scale):
        expr = 0
        for degree, coeff in enumerate(row):
            expr += (coeff // (scale**degree)) * Z**degree
        return Poly(expr, Z, domain="ZZ")

    def _check(self, guess):
        for modulus, mul, offset, cipher in self.rows:
            if pow(mul * guess + offset, self.e, modulus) != cipher:
                return False
        return True

    def run(self):
        if self.e != 3:
            raise ValueError("this script is written for e = 3 only")

        big_n, poly = self._global_poly()
        scale, matrix = self._make_basis(big_n, poly)
        reduced = self._lll(matrix)

        for row in reduced:
            candidate = self._restore_poly(row, scale)
            for segment, _ in candidate.intervals():
                left = int(segment[0])
                right = int(segment[1])
                for hit in {left, right}:
                    if hit >= 0 and self._check(hit):
                        raw = hit.to_bytes((hit.bit_length() + 7) // 8, "big")
                        return raw
        raise RuntimeError("message recovery failed")


def main():
    worker = ScatterRSAExploit(Path(__file__).with_name("output.txt"))
    print(worker.run().decode())


if __name__ == "__main__":
    main()
