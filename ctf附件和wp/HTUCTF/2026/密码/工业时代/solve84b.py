import json, itertools, hashlib, time, sys

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
main = comps[0]
A = {i: sorted(adj[i] & set(main)) for i in main}
nodes = sorted(main)

def ks_for(route, nbytes):
    rb = b''.join(int(a).to_bytes(4, 'big', signed=True) + int(b).to_bytes(4, 'big', signed=True) for a, b in route)
    seed = hashlib.sha256(b"HTUCTF|" + rb).digest()
    return [hashlib.sha256(seed + i.to_bytes(4, 'big')).digest()[0] for i in range(nbytes)]

def try_cycle(cyc):
    for rot in range(L):
        route = cyc[rot:] + cyc[:rot]
        ks = ks_for(route, L)
        pt = bytes(c ^ k for c, k in zip(ct, ks))
        if pt[:4] in (b'HTUC', b'flag', b'HTU{', b'HTUF'):
            return pt
    return None

budget = 200_000_000
cnt = 0
passdeg = 0
t0 = time.time()
path = []
inpath = [False] * n

def dfs(start):
    global cnt, passdeg
    cnt += 1
    if cnt % 2_000_000 == 0:
        print('nodes', cnt, 'degpass', passdeg, '%.0fs' % (time.time() - t0), flush=True)
    last = path[-1]
    if len(path) == L:
        if start in adj[last]:
            degs = [sum(1 for v in A[u] if inpath[v]) for u in path]
            if min(degs) >= 2:
                passdeg += 1
                r = try_cycle([pts[i] for i in path])
                if r:
                    print('FOUND', r, flush=True)
                    open('flag.txt', 'wb').write(r)
                    sys.exit(0)
        return
    need = L - len(path)
    for w in A[last]:
        if inpath[w]:
            continue
        # 内部度数不超过 3：prev 已占 1，path 中已有邻居最多再 2
        hits = sum(1 for v in A[w] if inpath[v])
        if hits > 2:
            continue
        inpath[w] = True; path.append(w)
        dfs(start)
        path.pop(); inpath[w] = False

for s in nodes:
    inpath[s] = True; path.append(s)
    dfs(s)
    path.pop(); inpath[s] = False
print('done cycles', passdeg, 'nodes', cnt)
