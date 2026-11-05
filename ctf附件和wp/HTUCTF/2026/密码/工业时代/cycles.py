"""枚举主连通块里长度 >= 44 的简单环，用已知明文前缀验 keystream。"""
import json, hashlib, sys, time

d = json.load(open('attack.json'))
pts = [tuple(p) for p in d['points']]
ct = bytes.fromhex(d['ct'])
N = len(pts)
D = 6
LMIN = len(ct)


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


adj = {i: {j for j in range(N) if j != i and cheb(pts[i], pts[j]) <= D} for i in range(N)}
seen = set(); comps = []
for s in range(N):
    if s in seen:
        continue
    st = [s]; seen.add(s); c = []
    while st:
        u = st.pop(); c.append(u)
        for v in adj[u]:
            if v not in seen:
                seen.add(v); st.append(v)
    comps.append(c)
comps.sort(key=len, reverse=True)
comp = sorted(comps[0])
idx = {v: k for k, v in enumerate(comp)}
n = len(comp)
A = [sorted(idx[w] for w in adj[v] if w in set(comp)) for v in comp]
print('component', n, 'edges', sum(len(x) for x in A) // 2, 'LMIN', LMIN, flush=True)


def rb(route):
    return b"".join(int(pts[i][0]).to_bytes(4, 'big', signed=True) +
                    int(pts[i][1]).to_bytes(4, 'big', signed=True) for i in route)


def check(cyc):
    for rot in range(len(cyc)):
        base = cyc[rot:] + cyc[:rot]
        for r in (base, base[::-1]):
            seed = hashlib.sha256(b"HTUCTF|" + rb(r)).digest()
            ks = [hashlib.sha256(seed + i.to_bytes(4, 'big')).digest()[0] for i in range(7)]
            if bytes(a ^ b for a, b in zip(ct, ks)) == b'HTUCTF{':
                return r
    return None


start_t = time.time()
LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 240.0
cnt = [0]
hit = []

used = [False] * n
path = []


def dfs(u, s0):
    if time.time() - start_t > LIMIT:
        raise TimeoutError
    if len(path) >= LMIN and s0 in A[u]:
        cnt[0] += 1
        cyc = [comp[i] for i in path]
        r = check(cyc)
        if r:
            print('HIT len=%d' % len(cyc), flush=True)
            hit.append(r)
            return True
    # 还能不能凑到 LMIN
    if len(path) + (n - len(path)) < LMIN:
        return False
    for w in A[u]:
        if used[w] or w < s0:
            continue
        used[w] = True
        path.append(w)
        if dfs(w, s0):
            return True
        path.pop(); used[w] = False
    return False


try:
    for s0 in range(n):
        used = [False] * n
        used[s0] = True
        path = [s0]
        if dfs(s0, s0):
            break
except TimeoutError:
    print('timeout', flush=True)

print('cycles', cnt[0], 'hit', len(hit), 'elapsed %.1f' % (time.time() - start_t))
if hit:
    r = hit[0]
    print('route', r)
    seed = hashlib.sha256(b"HTUCTF|" + rb(r)).digest()
    ks = [hashlib.sha256(seed + i.to_bytes(4, 'big')).digest()[0] for i in range(len(ct))]
    print('FLAG', bytes(a ^ b for a, b in zip(ct, ks)).decode())
