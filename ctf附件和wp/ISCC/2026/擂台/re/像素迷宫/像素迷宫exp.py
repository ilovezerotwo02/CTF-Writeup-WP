"""
PixelMaze (像素迷宫) - Exploit Script
ISCC Reverse Challenge

从 PixelMaze.exe 中提取迷宫数据，解密后 BFS 求解最短路径，得到 flag。
"""

import struct
from pathlib import Path
from collections import deque


EXE_PATH = Path("PixelMaze.exe")

# PE 文件偏移（通过 objdump 确定 .rdata 段位置）
RDATA_FILE_OFFSET = 0xBB800
PART2_OFFSET = RDATA_FILE_OFFSET + 0xE0   # 第 3-6 行 (40 个 int)
PART1_OFFSET = RDATA_FILE_OFFSET + 0x180  # 第 0-2 行 (30 个 int)


def read_encrypted_parts(data: bytes):
    """从 PE 文件中读取三段加密数据。"""
    # 第 1 段：前 3 行，.rdata 区
    part1 = [
        struct.unpack("<I", data[PART1_OFFSET + i * 4 : PART1_OFFSET + i * 4 + 4])[0]
        for i in range(30)
    ]
    # 第 2 段：中间 4 行，.rdata 区
    part2 = [
        struct.unpack("<I", data[PART2_OFFSET + i * 4 : PART2_OFFSET + i * 4 + 4])[0]
        for i in range(40)
    ]
    # 第 3 段：最后 3 行，栈上初始化（从反编译直接提取）
    part3 = [
        0xBE, 0xBE, 0x37, 0x2E, 0x7E, 0xB7, 0x8B, 0x1D, 0x66, 0x9D,
        0x6E, 0x4A, 0x3C, 0x5A, 0x7D, 0xA9, 0x3E, 0xEE, 0x2E, 0xEB,
        0x76, 0xEE, 0x4D, 0x0C, 0x67, 0x49, 0xAD, 0x7C, 0x3D, 0x00,
    ]
    return part1, part2, part3


def decrypt(ciphertext: list) -> list:
    """用 XOR 0x7F 解密像素值。"""
    return [x ^ 0x7F for x in ciphertext]


def build_grid(part1: list, part2: list, part3: list) -> list[list[int]]:
    """将三段数据拼成 10x10 的迷宫网格。"""
    encrypted = part1 + part2 + part3
    decrypted = decrypt(encrypted)
    return [decrypted[i * 10 : (i + 1) * 10] for i in range(10)]


def print_grid(grid: list[list[int]]):
    """打印迷宫网格及方向信息以便人工验证。"""
    dir_names = ["E", "W", "S", "N"]
    print("Decrypted maze grid (hex + available directions):")
    for r in range(10):
        row_parts = []
        for c in range(10):
            val = grid[r][c]
            dirs = "".join(dir_names[i] for i in range(4) if (val >> i) & 1)
            row_parts.append(f"{val:02X}({dirs:4s})")
        print(f"  row {r}: " + "  ".join(row_parts))
    print()


def solve_maze(grid: list[list[int]]) -> str:
    """
    BFS 求解迷宫最短路径。

    起点 (0,0)，终点 (9,9)。
    每个格子值的低 4 位表示四个方向是否可走：
      bit0: E (East,  col+1)
      bit1: W (West,  col-1)
      bit2: S (South, row+1)
      bit3: N (North, row-1)

    validatePath 要求必须在路径最后一个字符恰好到达 (9,9)，
    不能提前到达，所以必须找最短路径（BFS 天然保证）。
    """
    moves = {
        "N": (-1, 0),
        "S": (1, 0),
        "E": (0, 1),
        "W": (0, -1),
    }
    bit_index = {"E": 0, "W": 1, "S": 2, "N": 3}

    queue = deque()
    queue.append(((0, 0), ""))  # ((row, col), path_string)
    visited = {(0, 0)}

    while queue:
        (r, c), path = queue.popleft()

        # 到达终点
        if (r, c) == (9, 9):
            return path

        # 检查当前格子的四个方向
        cell = grid[r][c]
        for direction, (dr, dc) in moves.items():
            if (cell >> bit_index[direction]) & 1:  # 该方向可走
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append(((nr, nc), path + direction))

    raise RuntimeError("No path found! Maze may be unsolvable.")


def main():
    # 1. 读取 PE 文件
    print("[*] Reading PixelMaze.exe ...")
    data = EXE_PATH.read_bytes()

    # 2. 提取三段加密数据
    part1, part2, part3 = read_encrypted_parts(data)
    print(f"    PART1: {len(part1)} ints")
    print(f"    PART2: {len(part2)} ints")
    print(f"    PART3: {len(part3)} ints")

    # 3. 构建解密后的迷宫
    grid = build_grid(part1, part2, part3)
    print_grid(grid)

    # 4. BFS 求解
    print("[*] Solving maze with BFS ...")
    path = solve_maze(grid)
    print(f"    Path length: {len(path)}")
    print(f"    Path: {path}")

    # 5. 组装 flag
    flag = f"ISCC{{{path}}}"
    print(f"\n[+] Flag: {flag}")

    # 6. 验证路径格式（可选）
    assert all(c in "ENSW" for c in path), "Invalid path characters!"
    assert len(flag) == len("ISCC{") + len(path) + 1, "Flag length mismatch!"


if __name__ == "__main__":
    main()
