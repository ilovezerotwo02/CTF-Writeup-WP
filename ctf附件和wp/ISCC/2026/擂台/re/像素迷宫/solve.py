from pathlib import Path
from collections import deque


EXE_PATH = Path("PixelMaze.exe")


def load_grid() -> list[list[int]]:
    data = EXE_PATH.read_bytes()

    # PE offsets recovered from objdump:
    # .rdata file offset = 0xBB800
    # ENCRYPTED_PART2 at .rdata+0xE0, ENCRYPTED_PART1 at .rdata+0x180
    rdata_off = 0xBB800
    part2_off = rdata_off + 0xE0
    part1_off = rdata_off + 0x180

    part2 = [
        int.from_bytes(data[part2_off + i * 4 : part2_off + i * 4 + 4], "little")
        for i in range(40)
    ]
    part1 = [
        int.from_bytes(data[part1_off + i * 4 : part1_off + i * 4 + 4], "little")
        for i in range(30)
    ]

    # The last 30 encrypted values are stack-initialized inside getDecryptedPixel().
    part3 = [
        0xBE, 0xBE, 0x37, 0x2E, 0x7E, 0xB7, 0x8B, 0x1D, 0x66, 0x9D,
        0x6E, 0x4A, 0x3C, 0x5A, 0x7D, 0xA9, 0x3E, 0xEE, 0x2E, 0xEB,
        0x76, 0xEE, 0x4D, 0x0C, 0x67, 0x49, 0xAD, 0x7C, 0x3D, 0x00,
    ]

    enc = part1 + part2 + part3
    dec = [x ^ 0x7F for x in enc]
    return [dec[i * 10 : (i + 1) * 10] for i in range(10)]


def can_move(cell: int, direction: str) -> bool:
    bits = {
        "E": 0,
        "W": 1,
        "S": 2,
        "N": 3,
    }
    return ((cell >> bits[direction]) & 1) == 1


def find_path(grid: list[list[int]]) -> str:
    moves = {
        "N": (-1, 0),
        "S": (1, 0),
        "E": (0, 1),
        "W": (0, -1),
    }

    q = deque([((0, 0), "")])
    seen = {(0, 0)}

    while q:
        (r, c), path = q.popleft()
        if (r, c) == (9, 9):
            return path

        for direction, (dr, dc) in moves.items():
            if not can_move(grid[r][c], direction):
                continue

            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append(((nr, nc), path + direction))

    raise RuntimeError("path not found")


def main() -> None:
    grid = load_grid()
    path = find_path(grid)
    print("path =", path)
    print("flag =", f"ISCC{{{path}}}")


if __name__ == "__main__":
    main()
