"""工业时代：在 D=6 图的主连通块 2-core 上枚举哈密顿环，用已知明文前缀验 keystream。"""
import json, hashlib, sys, time

d = json.load(open('attack.json'))
pts = [tuple(p) for p in d['points']]
ct = bytes.fromhex(d['ct'])
N = len(pts)
D = 6


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


adj = {i: {j for j in range(N) if j != i and cheb(pts[i], pts[j]) <= D} for i in range(N)}

# 主连通块
seen = set()
comps = []
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
print('core', len(core), 'edges', sum(1 for u in core for v in adj[u] if v > u))

idx = {v: k for k, v in enumerate(core)}
A = [[idx[w] for w in adj[v] if w in alive] for v in core]
n = len(core)


def route_bytes(route):
    return b"".join(int(pts[i][0]).to_bytes(4, 'big', signed=True) +
                    int(pts[i][1]).to_bytes(4, 'big', signed=True) for i in route)


def check(route):
    seed = hashlib.sha256(b"HTUCTF|" + route_bytes(route)).digest()
    ks = [hashlib.sha256(seed + i.to_bytes(4, 'big')).digest()[0] for i in range(min(7, len(ct)))]
    return bytes(c ^ k for c, k in zip(ct, ks)) == b'HTUCTF{'


found = []
count = [0]
start = time.time()
LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0


def dfs(path, used):
    if time.time() - start > LIMIT:
        return True
    if len(path) == n:
        count[0] += 1
        if 0 not in A[path[-1]]:
            return False
        cyc = [core[i] for i in path]
        for rot in range(n):
            r = cyc[rot:] + cyc[:rot]
            if check(r) or check(r[::-1]):
                print('HIT', r)
                found.append(r)
                return True
        return False
    # 剪枝：未访问节点必须还有 >=2 个未用的邻居（含起点）
    last = path[-1]
    for w in A[last]:
        if w in used:
            continue
        used.add(w); path.append(w)
        ok = True
        for v in range(n):
            if v in used:
                continue
            cnt = sum(1 for x in A[v] if x not in used or (len(path) == n - 1 and x == path[0]))
            if cnt < 2 and not (len(path) == n - 1 and v in A[path[0]] and sum(1 for x in A[v] if x not in used) >= 1):
                ok = False
                break
        if ok and dfs(path, used):
            return True
        path.pop(); used.discard(w)
    return False


for s in range(n):
    used = {s}
    dfs([s], used)
    if found:
        break
print('cycles tested', count[0], 'found', len(found), 'time %.1f' % (time.time() - start))
