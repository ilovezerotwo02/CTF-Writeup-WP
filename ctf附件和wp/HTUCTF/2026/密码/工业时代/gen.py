
import hashlib, json, os, random
from gmpy2 import is_prime as is_prime_int
from secret import (FLAG, D, R, TARGET, MIN_CHORDS, MAX_CHORDS, MAX_DEG,
                    N_FAKE, FAKE_MIN, FAKE_MAX, N_PENDANT, N_PENDANT_FAKE,
                    N_CHAIN, CYCLE_MIN, CYCLE_CAP)

def is_gauss_prime(a, b):
    if a == 0 or b == 0:
        v = abs(a or b)
        return v % 4 == 3 and is_prime_int(v)
    return is_prime_int(a * a + b * b) 


def adj(p, q):
    return max(abs(p[0] - q[0]), abs(p[1] - q[1])) <= D


OFF = [(x, y) for x in range(-D, D + 1) for y in range(-D, D + 1) if x or y]


def prime_table():
    return {(a, b) for a in range(-R, R + 1) for b in range(-R, R + 1)
            if is_gauss_prime(a, b)}


def build_cycle(rng, primes, target, cmin, cmax, avoid=None):
    def free(p):
        return avoid is None or all(max(abs(p[0] - q[0]), abs(p[1] - q[1])) > 4 * D
                                    for q in avoid)

    def ok_deg(deg, hits):
        return len(hits) <= MAX_DEG and all(deg[q] + 1 <= MAX_DEG for q in hits)

    for _ in range(200000):
        s = (rng.randint(-R + 3 * D, R - 3 * D), rng.randint(-R + 3 * D, R - 3 * D))
        if s not in primes or not free(s):
            continue
        path, deg, chords = [s], {s: 0}, 0
        while len(path) < target:
            cur, start = path[-1], path[0]
            cand = []
            for dx, dy in OFF:
                p = (cur[0] + dx, cur[1] + dy)
                if p in deg or p not in primes or not free(p):
                    continue
                hits = [q for q in deg if adj(p, q)]
                if len(path) > 1 and adj(p, start):        # 收口
                    extra = len(hits) - 2
                    if 0 <= extra <= 1 and chords + extra <= cmax and ok_deg(deg, hits):
                        cand.append((p, extra, True, hits))
                else:
                    extra = len(hits) - 1
                    if extra == 0:
                        cand.append((p, 0, False, hits))
                    elif extra == 1 and chords + 1 <= cmax and ok_deg(deg, hits):
                        cand.append((p, 1, False, hits))   # 加一条弦
            if len(path) + 1 == target:
                cand = [c for c in cand if c[2]]
                if not cand:
                    break
            else:
                cand = [c for c in cand if not c[2]]
                if not cand:
                    break
            p, extra, _, hits = rng.choice(cand)
            for q in hits:
                deg[q] += 1
            deg[p] = len(hits)
            chords += extra
            path.append(p)
        if len(path) == target and adj(path[-1], path[0]) \
                and cmin <= sum(deg.values()) // 2 - target <= cmax \
                and min(deg.values()) >= 2 and max(deg.values()) <= MAX_DEG:
            return path
    return None


def pendant(rng, primes, host, taken):
    for _ in range(2000):
        p = (host[0] + rng.randint(-D, D), host[1] + rng.randint(-D, D))
        if p in taken or p not in primes or not adj(p, host):
            continue
        if sum(1 for q in taken if adj(p, q)) == 1:
            return p
    return None


def route_bytes(route):
    return b"".join(int(a).to_bytes(4, "big", signed=True)
                    + int(b).to_bytes(4, "big", signed=True) for a, b in route)


def keystream(route, n):
    seed = hashlib.sha256(b"HTUCTF|" + route_bytes(route)).digest()
    return [hashlib.sha256(seed + i.to_bytes(4, "big")).digest()[0] for i in range(n)]


def count_cycles(pts, lmin, budget=40_000_000):
    n = len(pts)
    nb = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if adj(pts[i], pts[j]):
                nb[i].append(j)
                nb[j].append(i)
    seen, total, nodes = [False] * n, 0, 0
    for s in range(n):
        if seen[s]:
            continue
        st, comp = [s], []
        seen[s] = True
        while st:
            u = st.pop()
            comp.append(u)
            for v in nb[u]:
                if not seen[v]:
                    seen[v] = True
                    st.append(v)
        if len(comp) < lmin:
            continue
        pos = {v: k for k, v in enumerate(comp)}
        loc = [[pos[w] for w in nb[v] if w in pos] for v in comp]
        used, path = [False] * len(comp), []

        def walk(u, s0):
            nonlocal total, nodes
            nodes += 1
            if nodes > budget:
                return True
            if len(path) >= lmin and s0 in loc[u]:
                total += 1
            for w in loc[u]:
                if w < s0 or used[w]:
                    continue
                used[w] = True
                path.append(w)
                if walk(w, s0):
                    return True
                path.pop()
                used[w] = False
            return False

        for s0 in range(len(comp)):
            used[s0] = True
            path.append(s0)
            bad = walk(s0, s0)
            path.pop()
            used[s0] = False
            if bad:
                break
    return total

def make(rng, primes):
    cycle = build_cycle(rng, primes, TARGET, MIN_CHORDS, MAX_CHORDS)
    if cycle is None:
        return None
    k = rng.randrange(len(cycle))
    cycle = cycle[k:] + cycle[:k]
    ks = keystream(cycle, len(FLAG))
    ct = bytes(c ^ k for c, k in zip(FLAG, ks))

    pts = list(cycle)
    for _ in range(N_FAKE):
        fake = build_cycle(rng, primes, rng.randint(FAKE_MIN, FAKE_MAX), 0, 0,
                           avoid=pts)
        if fake:
            pts += fake

    taken = set(pts)
    pend = []
    for i in range(N_PENDANT + N_PENDANT_FAKE):
        p = pendant(rng, primes, rng.choice(cycle if i < N_PENDANT else pts), taken)
        if p:
            pend.append(p)
            taken.add(p)
            pts.append(p)
    for _ in range(N_CHAIN):
        if not pend:
            break
        p = pendant(rng, primes, rng.choice(pend), taken)
        if p:
            pend.append(p)
            taken.add(p)
            pts.append(p)

    rng.shuffle(pts)
    return pts, ct


def main():
    rng = random.Random(os.urandom(16))
    primes = prime_table()
    last = None
    for _ in range(10): 
        got = make(rng, primes)
        if got is None:
            continue
        last = got
        if CYCLE_MIN <= count_cycles(got[0], len(FLAG)) <= CYCLE_CAP:
            break
    if last is None:
        return
    pts, ct = last
    with open("attack.json", "w") as f:
        json.dump({"points": [list(p) for p in pts], "ct": ct.hex()}, f)


if __name__ == "__main__":
    main()
