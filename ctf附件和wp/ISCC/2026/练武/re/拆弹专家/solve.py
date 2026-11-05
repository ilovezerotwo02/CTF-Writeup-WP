#!/usr/bin/env python3
"""
ISCC 拆弹专家 (Bomb Defusal) - Reverse Engineering Solver
"""

import base64

# ============================================================
# Rubik's Cube Cipher (2x2x2) - Combined transformation
# Key: "R U F R' D2" → expanded: R, U, F, R', D, D
# ============================================================

# Permutation: c[perm[i]] = a[i] + add[i] (mod 256)
# Derived by tracing all 6 moves step by step
COMBINED_PERM = [5, 1, 0, 3, 6, 7, 4, 2]
COMBINED_ADD = [8, 14, 23, 8, 5, 11, 23, 4]

def encrypt_block(block):
    """Encrypt an 8-byte block using the combined transformation."""
    assert len(block) == 8
    result = [0] * 8
    for i in range(8):
        result[COMBINED_PERM[i]] = (block[i] + COMBINED_ADD[i]) & 0xFF
    return bytes(result)

def pkcs7_pad(data, block_size=8):
    """PKCS#7 padding."""
    pad = block_size - (len(data) % block_size)
    if pad == 0:
        pad = block_size
    return data + bytes([pad] * pad)

def encrypt_cbc(data):
    """Encrypt data using ECB mode with the Rubik's cube cipher."""
    padded = pkcs7_pad(data, 8)
    result = b""
    for i in range(0, len(padded), 8):
        block = padded[i:i+8]
        result += encrypt_block(block)
    return result

AHR2 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

def fafe2(data):
    """Same base64 encode as the C++ code."""
    out = []
    i = 0
    while i + 3 <= len(data):
        n = (data[i] << 16) | (data[i+1] << 8) | data[i+2]
        out.append(AHR2[(n >> 18) & 63])
        out.append(AHR2[(n >> 12) & 63])
        out.append(AHR2[(n >> 6) & 63])
        out.append(AHR2[n & 63])
        i += 3
    rem = len(data) - i
    if rem == 1:
        n = data[i] << 16
        out.append(AHR2[(n >> 18) & 63])
        out.append(AHR2[(n >> 12) & 63])
        out.append('=')
        out.append('=')
    elif rem == 2:
        n = (data[i] << 16) | (data[i+1] << 8)
        out.append(AHR2[(n >> 18) & 63])
        out.append(AHR2[(n >> 12) & 63])
        out.append(AHR2[(n >> 6) & 63])
        out.append('=')
    return ''.join(out)

def fnv1a32(s):
    """FNV-1a 32-bit hash."""
    h = 0x811C9DC5
    for c in s:
        if isinstance(c, str):
            c = ord(c)
        h ^= c
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h

# ============================================================
# Stage 1: Verify password
# ============================================================

def check_stage1(password):
    """Check if password passes stage 1."""
    data = password.encode('latin-1')
    encrypted = encrypt_cbc(data)
    b64 = fafe2(encrypted)
    h = fnv1a32(b64)
    target = 0x8D93FFF8 ^ 0xA5A5A5A5
    print(f"  Password: {password}")
    print(f"  Encrypted: {encrypted.hex()}")
    print(f"  Base64: {b64}")
    print(f"  FNV1a: 0x{h:08X}, Target: 0x{target:08X}, Match: {h == target}")
    return h, h == target

# ============================================================
# Stage 2: Linear system
# ============================================================

def d4bb6(state):
    """LCG step (returns new state)."""
    return (state * 1664525 + 1013904223) & 0xFFFFFFFF

def setup_stage2(h):
    """Compute g_a, g_e from the stage 1 hash."""
    base_a = [2, 3, 4, 5, 6]
    g_a = [0] * 5
    for i in range(5):
        delta = (h >> (i * 6)) & 0x3
        g_a[i] = base_a[i] + delta

    seed = h ^ 0x12345678
    state = seed
    x = [0] * 5
    for i in range(5):
        state = d4bb6(state)
        if i != 0:
            x[i] = 10 + (state % 90)
        else:
            x[i] = state % 10

    g_e = [0] * 5
    g_e[0] = g_a[0] * x[0] + x[1] + x[4]
    g_e[1] = x[0] + g_a[1] * x[1] + x[2]
    g_e[2] = x[1] + g_a[2] * x[2] + x[3]
    g_e[3] = x[2] + g_a[3] * x[3] + x[4]
    g_e[4] = x[0] + x[3] + g_a[4] * x[4]

    return g_a, g_e, x

def gauss_solve(A, b):
    """Solve Ax = b using Gaussian elimination with partial pivoting (fractions)."""
    from fractions import Fraction
    n = len(A)
    # Augmented matrix with Fractions for exact arithmetic
    M = [[Fraction(A[i][j]) for j in range(n)] + [Fraction(b[i])] for i in range(n)]

    for col in range(n):
        # Partial pivoting
        max_row = max(range(col, n), key=lambda r: abs(M[r][col]))
        if M[max_row][col] == 0:
            raise ValueError("Singular matrix")
        M[col], M[max_row] = M[max_row], M[col]

        # Eliminate below
        for row in range(col + 1, n):
            factor = M[row][col] / M[col][col]
            for c in range(col, n + 1):
                M[row][c] -= factor * M[col][c]

    # Back substitution
    x = [Fraction(0)] * n
    for i in range(n - 1, -1, -1):
        s = M[i][n]
        for j in range(i + 1, n):
            s -= M[i][j] * x[j]
        x[i] = s / M[i][i]

    return [int(xi) for xi in x]  # Should be exact integers

def solve_stage2(g_a, g_e):
    """Solve the linear system for x1..x5."""
    a0, a1, a2, a3, a4 = g_a
    e0, e1, e2, e3, e4 = g_e

    # Equations:
    # a0*x1 +    x2 +           x5 = e0
    #    x1 + a1*x2 +    x3         = e1
    #           x2 + a2*x3 +    x4  = e2
    #                  x3 + a3*x4 + x5 = e3
    #    x1 +           x4 + a4*x5 = e4

    A = [
        [a0, 1,  0,  0,  1],
        [1,  a1, 1,  0,  0],
        [0,  1,  a2, 1,  0],
        [0,  0,  1,  a3, 1],
        [1,  0,  0,  1,  a4],
    ]
    b = [e0, e1, e2, e3, e4]

    x = gauss_solve(A, b)
    print(f"  Solved x = {x}")

    # Verify
    v0 = a0 * x[0] + x[1] + x[4]
    v1 = x[0] + a1 * x[1] + x[2]
    v2 = x[1] + a2 * x[2] + x[3]
    v3 = x[2] + a3 * x[3] + x[4]
    v4 = x[0] + x[3] + a4 * x[4]
    print(f"  Verify: {v0}=={e0} {v1}=={e1} {v2}=={e2} {v3}=={e3} {v4}=={e4}")

    # Format as 9-digit string: x1(1d) + x2(2d) + x3(2d) + x4(2d) + x5(2d)
    pw2 = f"{x[0]}{x[1]:02d}{x[2]:02d}{x[3]:02d}{x[4]:02d}"
    print(f"  Password2 = {pw2} (len={len(pw2)})")
    return pw2

# ============================================================
# Stage 3: Maze
# ============================================================

def generate_maze(seed):
    """Generate the 4x4 maze from seed."""
    MAZE_W, MAZE_H = 4, 4
    maze = [[0] * MAZE_W for _ in range(MAZE_H)]

    st = seed ^ 0x9E3779B9

    def lcg():
        nonlocal st
        st = (st * 1664525 + 1013904223) & 0xFFFFFFFF
        return st

    x, y = 0, 0
    maze[y][x] = 1

    while not (x == 3 and y == 3):
        r = lcg()
        canR = x < 3
        canD = y < 3
        if canR and canD:
            move = 1 if (r & 1) else 2
        elif canR:
            move = 1
        else:
            move = 2
        if move == 1:
            x += 1
        else:
            y += 1
        maze[y][x] = 1

    return maze

def print_maze(maze):
    """Print the maze."""
    print("  Maze:")
    for y, row in enumerate(maze):
        line = ""
        for x, cell in enumerate(row):
            line += "S " if (x, y) == (0, 0) and cell else (
                    "E " if (x, y) == (3, 3) and cell else (
                    "O " if cell else ". "))
        print(f"  {line}")

def find_maze_path(maze):
    """BFS from (0,0) to (3,3)."""
    from collections import deque
    W, H = 4, 4
    q = deque()
    q.append((0, 0, []))
    visited = {(0, 0)}
    while q:
        x, y, path = q.popleft()
        if x == 3 and y == 3:
            return ''.join(path)
        for dx, dy, move in [(0, 1, 'D'), (1, 0, 'R'), (0, -1, 'U'), (-1, 0, 'L')]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and maze[ny][nx] == 1 and (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append((nx, ny, path + [move]))
    return None

# ============================================================
# Main solver
# ============================================================

def main():
    print("=" * 60)
    print("ISCC 拆弹专家 Bomb Defusal Solver")
    print("=" * 60)

    # ---- Stage 1 ----
    print("\n[Stage 1]")
    stage1_pw = "ZVYHMYFA"
    h, ok = check_stage1(stage1_pw)
    if not ok:
        print("[!] Password ZVYHMYFA doesn't match!")
        return
    print(f"[+] Stage 1 hash: 0x{h:08X}")

    # ---- Stage 2 ----
    print("\n[Stage 2]")
    g_a, g_e, orig_x = setup_stage2(h)
    print(f"  g_a = {g_a}, g_e = {g_e}")
    print(f"  Original x = {orig_x}")

    pw2 = solve_stage2(g_a, g_e)

    # ---- Stage 3 ----
    print("\n[Stage 3]")
    seed = (int(pw2) & 0xFFFFFFFF)
    seed ^= (h * 0x9E3779B1) & 0xFFFFFFFF
    print(f"  Seed: 0x{seed:08X}")

    maze = generate_maze(seed)
    print_maze(maze)

    path = find_maze_path(maze)
    print(f"  Path: {path}")

    # ---- Flag ----
    print("\n" + "=" * 60)
    flag = f"ISCC{{{stage1_pw}{pw2}{path}}}"
    print(f"FLAG: {flag}")
    print("=" * 60)

if __name__ == "__main__":
    main()
