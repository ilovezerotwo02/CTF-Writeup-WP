_MAPS = (
    (
        "#########################",
        "#S#.........#...........#",
        "#.#.###.#####.#######.#.#",
        "#.#...#.....#.#.....#.#.#",
        "#.###.#####.#.#.###.#.#.#",
        "#.#A..#...#.#.#...#.#.#.#",
        "#.###.#.#.#.#.###.###.#.#",
        "#...#...#.#.....#.#...#.#",
        "###.###########.#.#.###.#",
        "#...#...#.....#...#.#...#",
        "#.###.#.#.###.###.#.#.###",
        "#.....#...#...#...#.#...#",
        "###########.#####.#.###.#",
        "#...#.....#.....#.#...#.#",
        "#.###.###.#####.#####.#.#",
        "#......B#.............#C#",
        "#########################",
    ),
    (
        "#########################",
        "#S#.....#...............#",
        "#.#.###.#.#######.#####.#",
        "#.#...#...#.....#.#.....#",
        "#.###.#####.###.#.#.#####",
        "#.#A..#...#.#...#.#.....#",
        "#.#####.#.#.#.#######.#.#",
        "#.#.....#...#.#.....#.#.#",
        "#.#.#########.#.###.###.#",
        "#...#.....#...#...#...#.#",
        "#####.#.###.#####.###.#.#",
        "#...#.#.#...#.....#.#...#",
        "###.#.#.#.###.#####.###.#",
        "#...#.#.#.#B..#...#.....#",
        "#.###.#.#.###.#.###.#####",
        "#.....#.......#........C#",
        "#########################",
    ),
    (
        "#########################",
        "#S....#.......#.......#.#",
        "#####.#.#.###.#.#####.#.#",
        "#...#.#A#.#.#.#.....#.#.#",
        "#.#.#.###.#.#.#####.#.#.#",
        "#.#.#.#...#.#.#.....#...#",
        "#.#.#.#.###.#.#.#########",
        "#.#...#...#...#.....#...#",
        "#.#####.#.###.#.###.#.#.#",
        "#...#...#...#.#..B#...#.#",
        "###.#.#####.#.#####.###.#",
        "#.#.#.....#.#.....#...#.#",
        "#.#.#######.#####.#####.#",
        "#.#.#...#...#.#...#.....#",
        "#.#.#.#.#.###.#.###.###.#",
        "#.....#...#.........#C..#",
        "#########################",
    ),
)

_CONTINUE_EXIT = (0, 2, 1)  # 各层正确出口在 'ABC' 中的下标
_CREDENTIAL_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
_KEY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_KEY_SALT = (23, 163, 92, 225, 40, 150, 79, 210)
_KEY_ORDER = (7, 2, 10, 0, 5, 11, 3, 8, 1, 6, 4, 9)
_FLAG_ORDER = (
    11, 50, 3, 34, 30, 33, 13, 43, 1, 14, 26, 7, 20, 35, 55, 25,
    39, 49, 42, 46, 54, 4, 48, 51, 2, 23, 32, 22, 9, 5, 16, 24,
    12, 37, 45, 47, 27, 44, 31, 36, 41, 38, 21, 8, 52, 28, 10, 19,
    18, 17, 29, 53, 40, 6, 15, 0,
)
_FLAG_SALT = (11, 29, 7, 41, 18, 3, 37)
_FLAG_BOX = (
    44, 58, 2, 48, 16, 65, 32, 90, 90, 70, 93, 16, 55, 72, 36, 83,
    93, 18, 46, 64, 27, 52, 15, 10, 78, 48, 64, 94, 36, 61, 7, 73,
    58, 20, 43, 74, 40, 5, 51, 66, 48, 53, 78, 65, 72, 45, 6, 76,
    83, 28, 45, 3, 43, 31, 79, 13,
)
MASK32 = 4294967295



def _final_credential(route):
    """把正确出口序列编码成 TRI-XXXX-XXXX-XXXX 凭证。"""
    state = 1831565813
    for index, exit_name in enumerate(route, 1):
        state = ((state << 7) | (state >> 25)) & MASK32
        state ^= (ord(exit_name) * 73244475) ^ (index * 2654435769)
        state = (state + 2712847316 + index * 1267611) & MASK32

    parts = []
    for block in range(3):
        state = (state * 1664525 + 1013904223 + block) & MASK32
        word = []
        for _ in range(4):
            state ^= (state << 13) & MASK32
            state ^= state >> 17
            state ^= (state << 5) & MASK32
            state &= MASK32
            word.append(_CREDENTIAL_ALPHABET[state % len(_CREDENTIAL_ALPHABET)])
        parts.append("".join(word))
    return "TRI-" + "-".join(parts)


def _derive_console_key(credential):
    """由凭证派生 12 位终端密钥（游戏里要手输的“击败妖精王的密钥”）。"""
    compact = credential.replace("-", "")
    state = 3237998097
    for index, char in enumerate(compact):
        state = (state + (ord(char) ^ _KEY_SALT[index % len(_KEY_SALT)])) & MASK32
        state = ((state * 33) ^ (state >> 11) ^ (index * 81)) & MASK32

    raw = []
    for index in range(len(_KEY_ORDER)):
        state = (state * 1103515245 + 12345 + _KEY_SALT[index % len(_KEY_SALT)]) & MASK32
        raw.append(_KEY_ALPHABET[state % len(_KEY_ALPHABET)])
    return "".join(raw[i] for i in _KEY_ORDER)


def _open_flag(console_key):
    """用终端密钥反演 _FLAG_BOX，还原最终 flag。"""
    key_bytes = console_key.encode("ascii")
    restored = [" "] * len(_FLAG_BOX)
    for index, storage_index in enumerate(_FLAG_ORDER):
        shift = (key_bytes[index % len(key_bytes)] + _FLAG_SALT[index % len(_FLAG_SALT)]) * (index + 3) % 95
        restored[index] = chr((_FLAG_BOX[storage_index] - shift) % 95 + 32)
    return "".join(restored)


# ========== 迷宫 BFS：验证正确出口可达并输出路径 ==========

def _find(level, wanted):
    for row, line in enumerate(_MAPS[level]):
        col = line.find(wanted)
        if col >= 0:
            return row, col
    raise ValueError(wanted)


def solve_maze(level, target):
    """BFS 求 S → target 的最短路径，返回方向串（W/A/S/D）。"""
    from collections import deque
    grid = _MAPS[level]
    start = _find(level, "S")
    goal = _find(level, target)
    moves = {"W": (-1, 0), "A": (0, -1), "S": (1, 0), "D": (0, 1)}
    q = deque([start])
    prev = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for d, (dr, dc) in moves.items():
            nxt = (cur[0] + dr, cur[1] + dc)
            if 0 <= nxt[0] < len(grid) and 0 <= nxt[1] < len(grid[0]):
                if grid[nxt[0]][nxt[1]] != "#" and nxt not in prev:
                    prev[nxt] = (cur, d)
                    q.append(nxt)
    # 回溯
    path = []
    cur = goal
    while prev[cur] is not None:
        cur, d = prev[cur]
        path.append(d)
    return "".join(reversed(path))


def main():
    print("[*] 三层迷宫正确出口（_CONTINUE_EXIT = (0,2,1) → 'ABC' 下标）：")
    route = []
    for level in range(3):
        idx = _CONTINUE_EXIT[level]
        exit_name = "ABC"[idx]
        route.append(exit_name)
        path = solve_maze(level, exit_name)
        print(f"    第{level + 1}层 → 出口 {exit_name}  最短路径({len(path)}步): {path}")

    print(f"\n[*] route = {route}")

    credential = _final_credential(route)
    print(f"[*] 妖精们的凭证 credential = {credential}")

    console_key = _derive_console_key(credential)
    print(f"[*] 终端密钥 console_key   = {console_key}")

    flag = _open_flag(console_key)
    print(f"\n[+] 最终 flag: {flag}")
    return flag


if __name__ == "__main__":
    main()
