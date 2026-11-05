import json, itertools, hashlib, sys, time

d = json.load(open('attack.json'))
pts = [tuple(p) for p in d['points']]
ct = bytes.fromhex(d['ct'])
L = len(ct)
n = len(pts)
D = 6

adj = [set() for _ in range(n)]
for i, j in itertools.combinations(range(n), 2):
    if max(abs(pts[i][0] - pts[j][0]), abs(pts[i][1] - pts[j][1])) <= D:
        adj[i].add(j); adj[j].add(i)
adj = [sorted(a) for a in adj]

# main component
seen = set(); comps = []
for s in range(n):
    if s in seen: continue
    st = [s]; seen.add(s); comp = []
    while st:
        u = st.pop(); comp.append(u)
        for v in adj[u]:
            if v not in seen:
                seen.add(v); st.append(v)
    comps.append(comp)
comps.sort(key=len, reverse=True)
main = set(comps[0])
print('main comp', len(main), 'L', L)
for i in range(n):
    adj[i] = [j for j in adj[i] if j in main]

def keystream(route, nbytes):
    route_bytes = b''.join(int(a).to_bytes(4, 'big', signed=True) + int(b).to_bytes(4, 'big', signed=True) for a, b in route)
    seed = hashlib.sha256(b"HTUCTF|" + route_bytes).digest()
    return [hashlib.sha256(seed + i.to_bytes(4, 'big')).digest()[0] for i in range(nbytes)]

def check(cycle):
    for rot in range(L):
        route = cycle[rot:] + cycle[:rot]
        ks = keystream(route, L)
        pt = bytes(c ^ k for c, k in zip(ct, ks))
        if pt.startswith(b'HTU') or pt.startswith(b'flag'):
            print('FOUND', pt)
            return pt
    return None

nodes = sorted(main)
budget = 20_000_000
cnt = 0
found = []
t0 = time.time()

def dfs(start, path, visited):
    global cnt
    cnt += 1
    if cnt > budget:
        raise RuntimeError('budget')
    if len(path) == L:
        if start in adj[path[-1]]:
            found.append(list(path))
            print('cycle found', len(found), 'nodes', cnt, '%.1fs' % (time.time() - t0))
            r = check([pts[i] for i in path])
            if r:
                open('flag.txt', 'wb').write(r)
                raise SystemExit
        return
    for w in adj[path[-1]]:
        if w <= start or w in visited:
            continue
        # 剩余可走空间剪枝
        visited.add(w); path.append(w)
        dfs(start, path, visited)
        path.pop(); visited.discard(w)

try:
    for s in nodes:
        dfs(s, [s], {s})
except RuntimeError:
    print('budget exhausted, found', len(found), 'cycles')
except SystemExit:
    raise
print('done, cycles', len(found), 'nodes', cnt)
