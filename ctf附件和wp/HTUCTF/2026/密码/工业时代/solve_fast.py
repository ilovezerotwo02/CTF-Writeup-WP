#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTU Crypto - 工业时代  快速解

为什么原来的 cycles.py 要跑 3 分多钟：
  它在 57 点主块上 DFS 枚举**所有长度 >= 44 的简单环**，一共 15 万+ 条，
  每条候选还要试 52 个旋转 × 2 个方向 × 7 个 SHA256 字节 = 728 次哈希，
  粗算 1.5e5 × 728 ≈ 1e8 次 SHA256，光哈希就上百秒；DFS 本身也是满树搜索。

真正的结构性事实（这份数据上可以直接验证）：
  主块 57 点 = 52 点的环 + 5 个吊坠（度 1 的树），2-core 恰好 52 点 / 71 边；
  真路线的点集 == 2-core 的点集，长度 52 == |2-core|。
  => 真路线是 2-core 上的一个**哈密顿环**，而 2-core 上哈密顿环总共只有 24 个！
  于是候选数从 1.5e5 掉到 24，再乘 104 个旋转/方向 = 2496 次哈希，毫秒级出结果。

脚本流程：
  1. 建图（切比雪夫距离 <= D），拆连通块，取大小 >= len(ct) 的块
  2. 迭代剥度 1 点得到 2-core
  3. 在 core 上 DFS 枚举哈密顿环（规范起点 + 度小于 2 的剪枝 + Warnsdorff 排序）
  4. 每个哈密顿环试 52 个旋转 × 2 个方向：
        seed = sha256(b"HTUCTF|" + route_bytes)
        ks[i] = sha256(seed + i.to_bytes(4,'big')).digest()[0]
     先用 ks[0] 卡掉 255/256 的错误候选，再验前 7 字节 b"HTUCTF{"
  5. 命中即解出整条 flag；两步都失败时自动降级为通用长环枚举（兜底）

用法：
    python solve_fast.py                 # 默认 attack.json、D=6
    python solve_fast.py attack.json 6   # 指定文件与 D
"""

import os
import sys
import json
import time
import hashlib
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = b"HTUCTF|"
MAGIC = b"HTUCTF{"          # 已知明文前缀，当 oracle 用


# ---------------------------------------------------------------------------
# 1. 读题 + 建图
# ---------------------------------------------------------------------------
def load(path):
    d = json.load(open(path, encoding="utf-8"))
    pts = [tuple(p) for p in d["points"]]
    return pts, bytes.fromhex(d["ct"])


def build_graph(pts, D):
    n = len(pts)
    adj = [set() for _ in range(n)]
    for i in range(n):
        xi, yi = pts[i]
        for j in range(i + 1, n):
            xj, yj = pts[j]
            if abs(xi - xj) <= D and abs(yi - yj) <= D:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def components(adj):
    n = len(adj)
    seen = [False] * n
    out = []
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        st, comp = [s], []
        while st:
            u = st.pop()
            comp.append(u)
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    st.append(v)
        out.append(comp)
    out.sort(key=len, reverse=True)
    return out


def core_of(adj, comp):
    """迭代剥掉度 <= 1 的叶子，返回 2-core 顶点集合。"""
    core = set(comp)
    deg = {v: sum(1 for w in adj[v] if w in core) for v in core}
    q = deque(v for v in core if deg[v] <= 1)
    while q:
        u = q.popleft()
        if u not in core:
            continue
        core.discard(u)
        for w in adj[u]:
            if w in core:
                deg[w] -= 1
                if deg[w] <= 1:
                    q.append(w)
    return core


# ---------------------------------------------------------------------------
# 2. 哈密顿环枚举（规范起点 + 剪枝）
# ---------------------------------------------------------------------------
def ham_cycles(A, n, cap=200000):
    """A: 局部邻接表。返回所有 n 长简单环，每个环以最小下标为起点、唯一一次。"""
    out = []
    used = [False] * n
    path = []
    nodes = 0

    def feasible(cur, s0):
        """每个未访问点必须还剩下 >=2 个可用邻居（cur 与 s0 算可用）。"""
        for v in range(n):
            if used[v]:
                continue
            c = 0
            for t in A[v]:
                if not used[t] or t == cur or t == s0:
                    c += 1
                    if c >= 2:
                        break
            if c < 2:
                return False
        return True

    def dfs(u, s0):
        nonlocal nodes
        nodes += 1
        if nodes > cap:
            raise RuntimeError("搜索节点超限")
        if len(path) == n:
            if s0 in Aset[u]:
                out.append(path.copy())
            return
        cand = [w for w in A[u] if not used[w] and w > s0]
        # Warnsdorff：先走“自由度小”的点，剪枝更早生效
        cand.sort(key=lambda w: sum(1 for t in A[w] if not used[t]))
        for w in cand:
            used[w] = True
            path.append(w)
            if feasible(w, s0):
                dfs(w, s0)
            path.pop()
            used[w] = False

    Aset = [set(a) for a in A]
    for s0 in range(n):
        used[s0] = True
        path.append(s0)
        dfs(s0, s0)
        path.pop()
        used[s0] = False
    return out, nodes


# ---------------------------------------------------------------------------
# 3. 用已知明文前缀验 keystream
# ---------------------------------------------------------------------------
class Oracle:
    def __init__(self, pts, ct):
        self.ct = ct
        self.pb = [p[0].to_bytes(4, "big", signed=True) +
                   p[1].to_bytes(4, "big", signed=True) for p in pts]
        self.tested = 0

    def _seed(self, raw):
        return hashlib.sha256(PREFIX + raw).digest()

    def try_route(self, gids):
        """gids: 全局点号列表（环的某个定向）。命中返回该方向/旋转后的路线。"""
        raw = b"".join(self.pb[g] for g in gids)
        m = len(raw)
        step = 8                        # 每点 8 字节
        double = raw + raw
        hit = None
        for r in range(len(gids)):
            rot = double[step * r: step * r + m]
            self.tested += 1
            seed = self._seed(rot)
            if self.ct[0] ^ hashlib.sha256(seed + b"\x00\x00\x00\x00").digest()[0] != MAGIC[0]:
                continue            # 1 次哈希就砍掉 255/256
            ks = [hashlib.sha256(seed + i.to_bytes(4, "big")).digest()[0]
                  for i in range(len(MAGIC))]
            if bytes(a ^ b for a, b in zip(self.ct, ks)) == MAGIC:
                # 完整解密 + 校验
                ks = [hashlib.sha256(seed + i.to_bytes(4, "big")).digest()[0]
                      for i in range(m // step)]
                pt = bytes(a ^ b for a, b in zip(self.ct, ks))
                try:
                    txt = pt.decode()
                except UnicodeDecodeError:
                    continue
                if txt.startswith("HTUCTF{") and txt.endswith("}"):
                    hit = list(rot[i:i + step] for i in range(0, m, step))
                    return txt
        return None


# ---------------------------------------------------------------------------
# 4. 兜底：通用长环枚举（只在哈密顿环落空时启用）
# ---------------------------------------------------------------------------
def long_cycles(A, n, lmin, cap=4000000):
    """枚举长度 >= lmin 的简单环（规范起点），逐个产出。"""
    used = [False] * n
    path = []
    nodes = 0

    def gen(u, s0):
        nonlocal nodes
        nodes += 1
        if nodes > cap:
            return
        if len(path) >= lmin and s0 in Aset[u]:
            yield path.copy()
        for w in A[u]:
            if used[w] or w < s0:
                continue
            used[w] = True
            path.append(w)
            yield from gen(w, s0)
            path.pop()
            used[w] = False

    Aset = [set(a) for a in A]
    for s0 in range(n):
        used[s0] = True
        path.append(s0)
        yield from gen(s0, s0)
        path.pop()
        used[s0] = False


# ---------------------------------------------------------------------------
# 5. 主流程
# ---------------------------------------------------------------------------
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "attack.json")
    D = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    t_all = time.time()
    pts, ct = load(path)
    lmin = len(ct)
    print(f"[+] attack.json : {path}")
    print(f"[+] points {len(pts)}  ct {lmin} bytes  D={D}")

    adj = build_graph(pts, D)
    comps = components(adj)
    print(f"[+] components  : {[len(c) for c in comps]}")

    oracle = Oracle(pts, ct)
    flag = None
    route = None

    for comp in comps:
        if len(comp) < lmin:
            continue
        core = core_of(adj, comp)
        if len(core) < lmin:
            continue

        core = sorted(core)
        idx = {v: k for k, v in enumerate(core)}
        n = len(core)
        A = [sorted(idx[w] for w in adj[v] if w in core) for v in core]
        edges = sum(len(a) for a in A) // 2
        print(f"[*] comp={len(comp)}  core={n}  core_edges={edges}  (吊坠 {len(comp) - n} 个)")

        t0 = time.time()
        cycles, nodes = ham_cycles(A, n)
        print(f"[*] 哈密顿环 {len(cycles)} 个，DFS 节点 {nodes}，耗时 {time.time() - t0:.3f}s")

        for cyc in cycles:
            gids = [core[i] for i in cyc]
            txt = oracle.try_route(gids)
            if txt is None:
                txt = oracle.try_route(gids[::-1])
            if txt:
                flag, route = txt, gids
                break
        print(f"[*] 候选路线验算 {oracle.tested} 条，"
              f"累计 {time.time() - t_all:.3f}s", flush=True)
        if flag:
            break

    # 兜底
    if not flag:
        print("[!] 哈密顿环没命中，降级枚举所有长度 >= %d 的环 ..." % lmin)
        for comp in comps:
            if len(comp) < lmin:
                continue
            core = core_of(adj, comp)
            if len(core) < lmin:
                continue
            core = sorted(core)
            idx = {v: k for k, v in enumerate(core)}
            n = len(core)
            A = [sorted(idx[w] for w in adj[v] if w in core) for v in core]
            for cyc in long_cycles(A, n, lmin):
                gids = [core[i] for i in cyc]
                txt = oracle.try_route(gids) or oracle.try_route(gids[::-1])
                if txt:
                    flag, route = txt, gids
                    break
            if flag:
                break

    if not flag:
        print("[-] 没解出来（可调 D 或加大 cap）")
        return

    print(f"[!] 环长 {len(route)}   验算 {oracle.tested} 条候选   "
          f"总耗时 {time.time() - t_all:.3f}s")
    print(f"[!] route = {route}")
    print(f"[!] FLAG  = {flag}")
    with open(os.path.join(HERE, "flag.txt"), "w", encoding="utf-8") as f:
        f.write(flag)


if __name__ == "__main__":
    main()
