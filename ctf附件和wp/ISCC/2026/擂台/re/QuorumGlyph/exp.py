# -*- coding: utf-8 -*-
"""
QuorumGlyph — 完整求解脚本
ISCC{QRM_XXXXX_3_w1tness_no_single_path!!}
"""

import numpy as np
from numba import njit

M32 = 0xFFFFFFFF
M64 = 0xFFFFFFFFFFFFFFFF

TARGET_HASH = 0xE04CF5339F776142
CHARSET = b'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def rol64(x, n):
    n &= 63
    return ((x << n) | (x >> (64 - n))) & M64




def hash_401CA0_py(a1):
    """纯 Python 版 sub_401CA0（对照用）"""
    v1 = a1 & M32
    v2 = (a1 ^ 0xB198FA1458A7836C) & M64
    v3 = 0
    v4 = ((2654435761 * v1) ^ 0xC5C9AFD93FF67D70) & M64

    v20 = [0] * 1024
    for i in range(1024):
        t = (v2 + i - 0x61C8864680B583EB) & M64
        t = (t ^ (t >> 30)) & M64
        v6 = (0xBF58476D1CE4E5B9 * t) & M64
        r1 = ((v6 >> 27) ^ v6) & M64
        prod1 = (0x94D049BB133111EB * r1) & M64
        v2 = ((prod1 >> 31) ^ prod1) & M64

        v7 = (v3 ^ v2) & M64
        v3 = (v3 + 0x100000001B3) & M64

        t2 = ((v7 ^ v4) ^ ((v7 ^ v4) >> 30)) & M64
        v8 = (0xBF58476D1CE4E5B9 * t2) & M64
        r2 = (v8 ^ (v8 >> 27)) & M64
        prod2 = (0x94D049BB133111EB * r2) & M64
        v4 = ((prod2 >> 31) ^ prod2) & M64

        v20[i] = (v2 ^ rol64(v4, i)) & M64

    v9 = 0
    v10 = 0
    for v11 in range(1536):
        idx1 = ((v11 & 0xFFFF) ^ ((v4 ^ v2) & 0xFFFF)) & 0x3FF
        v12 = v20[idx1]
        idx2 = ((v12 & 0xFFFF) ^ ((v10 ^ (v2 >> 17)) & 0xFFFF)) & 0x3FF
        v13 = v20[idx2]

        t3 = (v12 + v2 + v9) & M64
        t3 = (t3 ^ (t3 >> 30)) & M64
        v14 = (0xBF58476D1CE4E5B9 * t3) & M64
        r3 = ((v14 >> 27) ^ v14) & M64
        prod3 = (0x94D049BB133111EB * r3) & M64
        v2 = ((prod3 >> 31) ^ prod3) & M64

        v4 ^= rol64((v13 + v2) & M64, v2 >> 59)
        v4 &= M64

        v15 = (v12 + v11) & M64
        idx3 = ((v4 & 0xFFFF) ^ (((v11 << 7) ^ v12) & 0xFFFF)) & 0x3FF

        t4 = (v13 + v15) & M64
        t4 = (t4 ^ (t4 >> 30)) & M64
        v17 = (0xBF58476D1CE4E5B9 * t4) & M64
        r4 = ((v17 >> 27) ^ v17) & M64
        prod4 = (0x94D049BB133111EB * r4) & M64
        v20[idx3] = (v2 ^ v4 ^ ((prod4 >> 31) ^ prod4)) & M64

        v10 += 131
        v9 = (v9 - 0x2917014799A6026D) & M64

    idx_final = (((v2 + v4) & 0xFFFF)) & 0x3FF
    v18 = (v20[idx_final] ^ v2 ^ v4 ^ 0x51474C5950484153) & M64
    t5 = (v18 ^ (v18 >> 30)) & M64
    t6 = (0xBF58476D1CE4E5B9 * t5) & M64
    r5 = ((t6 >> 27) ^ t6) & M64
    prod5 = (0x94D049BB133111EB * r5) & M64
    return ((prod5 >> 31) ^ prod5) & M64


# ---- Numba JIT 加速版 (全部使用 uint64 确保逻辑移位) ----
U0 = np.uint64(0)

@njit
def hash_401CA0(a1):
    """sub_401CA0 — JIT 加速"""
    v2 = np.uint64(a1) ^ np.uint64(0xB198FA1458A7836C)
    v3 = U0
    v4 = np.uint64(2654435761) * np.uint64(a1 & 0xFFFFFFFF) ^ np.uint64(0xC5C9AFD93FF67D70)

    v20 = np.zeros(1024, dtype=np.uint64)

    for i in range(1024):
        t = v2 + np.uint64(i) - np.uint64(0x61C8864680B583EB)
        t = t ^ (t >> np.uint64(30))
        v6 = np.uint64(0xBF58476D1CE4E5B9) * t
        r1 = (v6 >> np.uint64(27)) ^ v6
        p1 = np.uint64(0x94D049BB133111EB) * r1
        v2 = (p1 >> np.uint64(31)) ^ p1

        v7 = v3 ^ v2
        v3 = v3 + np.uint64(0x100000001B3)

        t2 = (v7 ^ v4) ^ ((v7 ^ v4) >> np.uint64(30))
        v8 = np.uint64(0xBF58476D1CE4E5B9) * t2
        r2 = (v8 >> np.uint64(27)) ^ v8
        p2 = np.uint64(0x94D049BB133111EB) * r2
        v4 = (p2 >> np.uint64(31)) ^ p2

        v20[i] = v2 ^ _rol64(v4, np.uint64(i))

    v9 = U0
    v10 = U0
    for v11 in range(1536):
        idx1 = (np.uint64(v11) ^ (v4 ^ v2)) & np.uint64(0x3FF)
        v12 = v20[idx1]
        idx2 = (v12 ^ (v10 ^ (v2 >> np.uint64(17)))) & np.uint64(0x3FF)
        v13 = v20[idx2]

        t3 = v12 + v2 + v9
        t3 = t3 ^ (t3 >> np.uint64(30))
        v14 = np.uint64(0xBF58476D1CE4E5B9) * t3
        r3 = (v14 >> np.uint64(27)) ^ v14
        p3 = np.uint64(0x94D049BB133111EB) * r3
        v2 = (p3 >> np.uint64(31)) ^ p3

        v4 ^= _rol64(v13 + v2, v2 >> np.uint64(59))

        v15 = v12 + np.uint64(v11)
        idx3 = (v4 ^ ((np.uint64(v11) << np.uint64(7)) ^ v12)) & np.uint64(0x3FF)

        t4 = v13 + v15
        t4 = t4 ^ (t4 >> np.uint64(30))
        v17 = np.uint64(0xBF58476D1CE4E5B9) * t4
        r4 = (v17 >> np.uint64(27)) ^ v17
        p4 = np.uint64(0x94D049BB133111EB) * r4
        v20[idx3] = v2 ^ v4 ^ ((p4 >> np.uint64(31)) ^ p4)

        v10 += np.uint64(131)
        v9 -= np.uint64(0x2917014799A6026D)

    idx_final = (v2 + v4) & np.uint64(0x3FF)
    v18 = v20[idx_final] ^ v2 ^ v4 ^ np.uint64(0x51474C5950484153)
    t5 = v18 ^ (v18 >> np.uint64(30))
    t6 = np.uint64(0xBF58476D1CE4E5B9) * t5
    r5 = (t6 >> np.uint64(27)) ^ t6
    p5 = np.uint64(0x94D049BB133111EB) * r5
    return (p5 >> np.uint64(31)) ^ p5


@njit
def _rol64(x, n):
    n &= np.uint64(63)
    return (x << n) | (x >> (np.uint64(64) - n))


def solve_witness3(charset_bytes, target, hashfn):
    """穷举 Witness-3"""
    inv = 1
    c = 13756821
    for _ in range(5):
        inv = (inv * (2 - c * inv)) & M64
    inv_24 = inv & 0xFFFFFF

    B = 11792179

    for v121 in range(0x1000000):
        x = ((v121 - B) * inv_24) & 0xFFFFFF
        if hashfn(x) == target:
            # 解码 v121 -> 5 chars
            d0 = v121 // 1048576
            r = v121 - d0 * 1048576
            d1 = r // 32768
            r -= d1 * 32768
            d2 = r // 1024
            r -= d2 * 1024
            d3 = r // 32
            d4 = r - d3 * 32
            mid = (chr(charset_bytes[d0]) + chr(charset_bytes[d1]) +
                   chr(charset_bytes[d2]) + chr(charset_bytes[d3]) + chr(charset_bytes[d4]))
            return v121, mid

    return 0, ""


def main():
    print("[*] QuorumGlyph — 求解脚本")
    print()

    # 验证 JIT 版
    print("[*] 编译并验证 JIT hash...")
    import time
    t0 = time.time()
    h_jit = hash_401CA0(0x0C0DE5)
    t1 = time.time()
    print(f"[*] hash_jit(0x0C0DE5) = 0x{h_jit:016x} (编译: {t1-t0:.1f}s)")

    if h_jit == TARGET_HASH:
        print("[*] JIT 结果正确! 开始穷举...")
        hashfn = hash_401CA0
    else:
        print("[*] JIT 结果错误! 使用 Python 版本...")
        hashfn = hash_401CA0_py

    print()

    # 穷举 Witness-3
    print(f"[*] Flag 骨架: ISCC{{QRM_{{*****}}_3_w1tness_no_single_path!!}}")
    print(f"[*] Target Hash: 0x{TARGET_HASH:016x}")
    print(f"[*] 字符集: {CHARSET.decode()}")
    print(f"[*] 搜索空间: 2^24 = 16,777,216")
    print()

    t2 = time.time()
    v121, middle = solve_witness3(np.frombuffer(CHARSET, dtype=np.uint8), TARGET_HASH, hashfn)
    t3 = time.time()

    if not middle:
        print("[-] 未找到匹配!")
        return

    print(f"[*] 穷举耗时: {t3 - t2:.1f}s")
    print(f"[*] 中间 5 字符: {middle}")
    print(f"[*] 编码值 v121 = 0x{v121:06x} ({v121})")

    # 仿射验证
    inv = 1
    c = 13756821
    for _ in range(5):
        inv = (inv * (2 - c * inv)) & M64
    inv_24 = inv & 0xFFFFFF
    x_val = ((v121 - 11792179) * inv_24) & 0xFFFFFF
    h_check = hashfn(x_val)
    print(f"[*] 仿射 x = 0x{x_val:06x}")
    print(f"[*] hash(x) = 0x{h_check:016x} {'OK' if h_check == TARGET_HASH else 'FAIL'}")

    flag = f"ISCC{{QRM_{middle}_3_w1tness_no_single_path!!}}"
    print()
    print(f"[+] FLAG: {flag}")
    print(f"[+] 长度: {len(flag)}")

    if len(flag) == 42:
        print("[+] 验证通过")


if __name__ == '__main__':
    main()
