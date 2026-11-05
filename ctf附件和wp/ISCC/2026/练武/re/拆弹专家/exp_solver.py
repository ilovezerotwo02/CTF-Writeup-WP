#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ISCC zerotwo — 完整求解脚本
"""
from fractions import Fraction
from collections import deque

# ------------------------------------------------------------
# Part 1: Rubik Cube Cipher (2x2x2) 复合变换
# 密钥 "R U F R' D2" → 6步转动 → 等价于单步仿射
# ------------------------------------------------------------
MAPPING = [5, 1, 0, 3, 6, 7, 4, 2]
OFFSET  = [8, 14, 23, 8, 5, 11, 23, 4]

def _enc_blk(blk):
    """8字节块加密：out[perm[i]] = (blk[i] + add[i]) & 0xFF"""
    out = bytearray(8)
    for i in range(8):
        out[MAPPING[i]] = (blk[i] + OFFSET[i]) & 0xFF
    return bytes(out)

def _pad8(raw):
    """PKCS#7 填充至8的倍数"""
    pad = 8 - (len(raw) % 8)
    return raw + bytes([pad] * pad)

B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

def _b64(data):
    """标准Base64编码（同C++实现）"""
    out = []
    for i in range(0, len(data), 3):
        chunk = data[i:i+3]
        n = chunk[0] << 16
        if len(chunk) > 1: n |= chunk[1] << 8
        if len(chunk) > 2: n |= chunk[2]
        out.append(B64[(n >> 18) & 0x3F])
        out.append(B64[(n >> 12) & 0x3F])
        out.append(B64[(n >> 6) & 0x3F] if len(chunk) > 1 else '=')
        out.append(B64[n & 0x3F] if len(chunk) > 2 else '=')
    return ''.join(out)

def _fnv1a(s):
    """FNV-1a 32-bit"""
    h = 0x811C9DC5
    for ch in s:
        h ^= (ch if isinstance(ch, int) else ord(ch))
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h

def stage1_check(pw: str):
    """验证第一关密码"""
    data = _pad8(pw.encode())
    ct = b''
    for i in range(0, len(data), 8):
        ct += _enc_blk(data[i:i+8])
    b64 = _b64(ct)
    hv = _fnv1a(b64)
    return hv ^ 0xA5A5A5A5 == 0x8D93FFF8, hv

# ------------------------------------------------------------
# Part 2: 线性方程组（高斯消元）
# ------------------------------------------------------------
def _lcg_step(st):
    return (st * 1664525 + 1013904223) & 0xFFFFFFFF

def derive_stage2(hv: int):
    """从Stage1哈希推导Stage2参数"""
    base = [2, 3, 4, 5, 6]
    a = [base[i] + ((hv >> (i * 6)) & 3) for i in range(5)]
    st = hv ^ 0x12345678
    xs = []
    for i in range(5):
        st = _lcg_step(st)
        xs.append(st % 10 if i == 0 else 10 + st % 90)
    e = [
        a[0]*xs[0] + xs[1] + xs[4],
        xs[0] + a[1]*xs[1] + xs[2],
        xs[1] + a[2]*xs[2] + xs[3],
        xs[2] + a[3]*xs[3] + xs[4],
        xs[0] + xs[3] + a[4]*xs[4],
    ]
    return a, e, xs

def gauss(mat, vec):
    """高斯消元（分数精确运算）"""
    n = len(mat)
    aug = [[Fraction(mat[i][j]) for j in range(n)] + [Fraction(vec[i])] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if aug[pivot][col] == 0:
            raise ValueError("singular")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for r in range(col + 1, n):
            f = aug[r][col] / aug[col][col]
            for c in range(col, n + 1):
                aug[r][c] -= f * aug[col][c]
    x = [Fraction(0)] * n
    for i in range(n - 1, -1, -1):
        s = aug[i][n]
        for j in range(i + 1, n):
            s -= aug[i][j] * x[j]
        x[i] = s / aug[i][i]
    return [int(v) for v in x]

def solve_stage2(a, e):
    """解五元一次方程组"""
    A = [
        [a[0], 1, 0, 0, 1],
        [1, a[1], 1, 0, 0],
        [0, 1, a[2], 1, 0],
        [0, 0, 1, a[3], 1],
        [1, 0, 0, 1, a[4]],
    ]
    xs = gauss(A, e)
    return f"{xs[0]}{xs[1]:02d}{xs[2]:02d}{xs[3]:02d}{xs[4]:02d}"

# ------------------------------------------------------------
# Part 3: 迷宫生成 & BFS寻路
# ------------------------------------------------------------
def gen_maze(seed):
    """4x4 迷宫生成"""
    st = seed ^ 0x9E3779B9
    W = H = 4
    maze = [[0]*W for _ in range(H)]
    def lcg():
        nonlocal st
        st = (st * 1664525 + 1013904223) & 0xFFFFFFFF
        return st
    x = y = 0
    maze[y][x] = 1
    while not (x == 3 and y == 3):
        r = lcg()
        right = x < 3
        down  = y < 3
        if right and down:
            move = 1 if (r & 1) else 2
        elif right:
            move = 1
        else:
            move = 2
        x += 1 if move == 1 else 0
        y += 0 if move == 1 else 1
        maze[y][x] = 1
    return maze

def bfs_path(maze):
    """BFS找最短路径"""
    q = deque([(0, 0, "")])
    seen = {(0, 0)}
    dirs = [(0, 1, 'D'), (1, 0, 'R'), (0, -1, 'U'), (-1, 0, 'L')]
    while q:
        x, y, p = q.popleft()
        if x == 3 and y == 3:
            return p
        for dx, dy, ch in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 4 and 0 <= ny < 4 and maze[ny][nx] and (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny, p + ch))
    return None

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    print("=" * 50)
    print("zerotwo Solver")
    print("=" * 50)

    # Stage 1
    pw1 = "ZVYHMYFA"
    ok, hv = stage1_check(pw1)
    assert ok, "Stage 1 failed!"
    print(f"\n[1] Password: {pw1}")
    print(f"    Hash: 0x{hv:08X}")

    # Stage 2
    a, e, orig = derive_stage2(hv)
    print(f"\n[2] g_a = {a}")
    print(f"    g_e = {e}")
    pw2 = solve_stage2(a, e)
    print(f"    Password: {pw2}")

    # Stage 3
    seed = (int(pw2) ^ (hv * 0x9E3779B1)) & 0xFFFFFFFF
    maze = gen_maze(seed)
    print(f"\n[3] Maze ({seed:#010x}):")
    for row in maze:
        print("    " + " ".join("O" if c else "." for c in row))
    pw3 = bfs_path(maze)
    print(f"    Path: {pw3}")

    # Flag
    flag = f"ISCC{{{pw1}{pw2}{pw3}}}"
    print("\n" + "=" * 50)
    print(f"FLAG: {flag}")
    print("=" * 50)
    return flag

if __name__ == "__main__":
    main()
