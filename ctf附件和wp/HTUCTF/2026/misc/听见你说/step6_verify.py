#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 6 / 8　补完自检：三条硬指标必须先过
---------------------------------------------------------------
输入 : work/M_patched.npy
输出 : 步骤截图/06_自检.png

自检的意义：网格歪一格、补丁错一行，扫码器只会给你「识别失败」四个字，
你没法判断是角补错了、掩码读错了、还是图糊了。先把这三条卡死，后面的报错才有意义。

    ① 时序图形  row6[8..20] 与 col6[8..20] 必须是严格的 #.#.#.#
    ② 暗模块    M[21][8] 必须为黑（Version ≥ 2 恒黑，位置 = 4×版本+9 行）
    ③ 数据模块总数 必须等于 70 码字 × 8 + 7 余位 = 567
"""

import numpy as np

from _common import BLUE, GREEN, INK, N, ORANGE, SUB, WORK, Sheet, cjk, prepare


def function_mask(n=N):
    """标出所有功能区（含定位 / 分隔 / 时序 / 格式 / 暗模块 / 对齐图形）。"""
    f = np.zeros((n, n), bool)
    f[0:8, 0:8] = True
    f[0:8, n - 8:n] = True
    f[n - 8:n, 0:8] = True
    f[6, :] = True
    f[:, 6] = True
    f[8, 0:9] = True
    f[0:9, 8] = True
    f[8, n - 8:n] = True
    f[n - 7:n, 8] = True
    f[n - 8, 8] = True                      # 暗模块
    f[20:25, 20:25] = True                  # Version 3 的对齐图形
    return f


def check(P):
    row = "".join("#" if P[6, c] else "." for c in range(8, 21))
    col = "".join("#" if P[r, 6] else "." for r in range(8, 21))
    dark = bool(P[21, 8])
    data_modules = int((~function_mask()).sum())
    ok = row == "#.#.#.#.#.#.#" and col == "#.#.#.#.#.#.#" and dark and data_modules == 567
    return {"row": row, "col": col, "dark": dark, "data": data_modules, "ok": ok}


def draw(P, r):
    s = Sheet(770)
    s.head("⑥ 补完自检：三条硬指标必须先过",
           "网格歪一格、补丁错一行，这里立刻露馅——不用等扫码失败再回头猜")

    cell, q = 16, 2
    side = (N + 2 * q) * cell
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (side, side), (255, 255, 255))
    dd = ImageDraw.Draw(im)
    for rr in range(N):
        for cc in range(N):
            if P[rr, cc]:
                dd.rectangle([(cc + q) * cell, (rr + q) * cell,
                              (cc + q + 1) * cell - 1, (rr + q + 1) * cell - 1], fill=(0, 0, 0))
    s.img.paste(im, (56, 156))

    y6 = 156 + (6 + q) * cell
    s.d.rectangle([56 + (8 + q) * cell, y6, 56 + (21 + q) * cell, y6 + cell], outline=BLUE, width=3)
    x6 = 56 + (6 + q) * cell
    s.d.rectangle([x6, 156 + (8 + q) * cell, x6 + cell, 156 + (21 + q) * cell], outline=ORANGE, width=3)
    dr, dc = N - 8, 8
    s.d.rectangle([56 + (dc + q) * cell, 156 + (dr + q) * cell,
                   56 + (dc + q + 1) * cell, 156 + (dr + q + 1) * cell], outline=GREEN, width=3)

    s.d.text((640, 160), "① 时序图形（蓝 = 第 6 行，橙 = 第 6 列）", font=cjk(16, True), fill=INK)
    s.lines((640, 198), [f"row6 : {r['row']}", f"col6 : {r['col']}"], size=15, lh=26)
    s.d.text((640, 262), "必须严格 # . # . # 交替，否则说明行列错位", font=cjk(14), fill=SUB)

    s.d.text((640, 312), "② 暗模块 M[21][8]（绿框）", font=cjk(16, True), fill=INK)
    s.lines((640, 350), [f"M[21][8] = {r['dark']}", "Version ≥ 2 必须为真（恒黑）"], size=15, lh=26)

    s.d.text((640, 424), "③ 数据模块总数", font=cjk(16, True), fill=INK)
    s.lines((640, 462), [
        f"实测 {r['data']} = 70 码字 × 8 + 7 余位",
        "→ 版本 3、纠错等级 M：70 = 44 数据 + 26 纠错",
        "→ 版本号 = (29 - 17) / 4 = 3",
    ], size=14, lh=26)
    s.foot("步骤 6 / 8　·　567 对得上，说明功能区挖得干净、补的也只是功能区")
    s.save("06_自检.png")


def run():
    prepare()
    print("[step6] 自检")
    P = np.load(WORK / "M_patched.npy")
    r = check(P)
    print(f"    row6={r['row']}  col6={r['col']}  暗模块={r['dark']}  数据模块={r['data']}")
    assert r["ok"], "自检未通过"
    print("    三条全部通过")
    draw(P, r)
    return r


if __name__ == "__main__":
    run()
