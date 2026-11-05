"""工业时代：D=6 主块 2-core 上做哈密顿环 DFS，带可用度剪枝，命中即验明文前缀。"""
import json, hashlib, sys, time

d = json.load(open('attack.json'))
pts = [tuple(p) for p in d['points']]
ct = bytes.fromhex(d['ct'])
N = len(pts)
D = 6


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
main = set(comps[0])
deg = {v: len(adj[v] & main) for v in main}
alive = set(main)
ch = True
while ch:
    ch = False
    for v in list(alive):
        if deg[v] < 2:
            alive.discard(v); ch = True
            for w in adj[v] & main:
                deg[w] -= 1
core = sorted(alive)
idx = {v: k for k, v in enumerate(core)}
n = len(core)
A = [sorted({idx[w] for w in adj[v] if w in alive}) for v in core]
print('n=', n, 'edges=', sum(len(x) for x in A) // 2, flush=True)


def route_bytes(route):
    return b"".join(int(pts[i][0]).to_bytes(4, 'big', signed=True) +
                    int(pts[i][1]).to_bytes(4, 'big', signed=True) for i in route)


def check(cyc):
    for rot in range(len(cyc)):
        for r in (cyc[rot:] + cyc[:rot], (cyc[rot:] + cyc[:rot])[::-1]):
            seed = hashlib.sha256(b"HTUCTF|" + route_bytes(r)).digest()
            ks = [hashlib.sha256(seed + i.to_bytes(4, 'big')).digest()[0] for i in range(7)]
            if bytes(a ^ b for a, b in zip(ct, ks)) == b'HTUCTF{':
                return r
    return None


found = []
tested = [0]
start_t = time.time()
LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0

used = [False] * n
path = []


def dfs(u, depth):
    if time.time() - start_t > LIMIT:
        raise TimeoutError
    if depth == n:
        if 0 in A[u] or path[0] in A[u]:
            tested[0] += 1
            cyc = [core[i] for i in path]
            r = check(cyc)
            if r:
                print('HIT', r, flush=True)
                found.append(r)
                return True
        return False
    for w in A[u]:
        if used[w]:
            continue
        used[w] = True
        path.append(w)
        ok = True
        for v in range(n):
            if used[v]:
                continue
            cnt = 0
            for x in A[v]:
                if not used[x] or x == path[0]:
                    cnt += 1
            if cnt < 2:
                ok = False
                break
        if ok and dfs(w, depth + 1):
            return True
        path.pop(); used[w] = False
    return False


try:
    for s in range(n):
        used = [False] * n
        used[s] = True
        path = [s]
        if dfs(s, 1):
            break
except TimeoutError:
    print('timeout', flush=True)
print('tested cycles', tested[0], 'found', len(found), 'elapsed %.1f' % (time.time() - start_t))
if found:
    r = found[0]
    seed = hashlib.sha256(b"HTUCTF|" + route_bytes(r)).digest()
    ks = [hashlib.sha256(seed + i.to_bytes(4, 'big')).digest()[0] for i in range(len(ct))]
    print('FLAG', bytes(a ^ b for a, b in zip(ct, ks)))
