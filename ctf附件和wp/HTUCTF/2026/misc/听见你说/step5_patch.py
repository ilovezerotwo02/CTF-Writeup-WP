#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 5 / 8　补回定位图形（关键在于内缩一格）
---------------------------------------------------------------
输入 : work/M_raw.npy
输出 : work/M_patched.npy          补好三个角的矩阵
       步骤截图/05_补定位图形.png   补前 / 补后对照

算法三步，一步都不能省：
    1. 把每个角的 8×8 先清成白   → 顺便得到分隔符
    2. 在 8×8 内的正确位置画 7×7 → 左上 (0,0)，右上 (0,22)，左下 (22,0)
    3. 其余模块一个都不许动      → 数据区、格式信息、对齐图形全部保留

为什么是「内缩」：三个 8×8 块里，回字只有左上是贴角的。
QR 规范里三个定位图形分别占 rows 0-6 / cols 0-6、rows 0-6 / cols 22-28、rows 22-28 / cols 0-6，
剩下的那一行一列是白色分隔符。
"""

import numpy as np

from _common import BLOCKS, FINDER, GREEN, INK, RED, SUB, WORK, Sheet, cjk, render, prepare


def patch(M):
    P = M.copy()
    for (br, bc), (fr, fc) in BLOCKS:
        P[br:br + 8, bc:bc + 8] = False          # 先清 8×8（连分隔符一起重置）
        for i, row in enumerate(FINDER):
            for j, ch in enumerate(row):
                if ch == "#":
                    P[fr + i, fc + j] = True          # 再画 7×7 回字
    return P


def draw(M, P):
    s = Sheet(780)
    s.head("⑤ 补回定位图形：关键是「内缩一格」",
           "先把三个 8×8 清成白色（顺带得到分隔符），再按模板画回 7×7；右上与左下各留出最外一行 / 列")

    a = render(M, scale=16, quiet=3)
    b = render(P, scale=16, quiet=3)
    s.d.text((70, 150), "补之前", font=cjk(17, True), fill=RED)
    s.paste(a, (70, 180, 600, 690))
    s.d.text((70, 702), "三个角空空如也，解码器连二维码都定位不到", font=cjk(14), fill=SUB)

    s.d.text((690, 150), "补之后", font=cjk(17, True), fill=GREEN)
    s.paste(b, (690, 180, 1220, 690))
    s.d.text((690, 702), "三个回字归位，右下对齐图形原封不动", font=cjk(14), fill=SUB)
    s.foot("步骤 5 / 8　·　改动范围仅限三个 8×8；其余 567 个数据模块一个字节都没碰")
    s.save("05_补定位图形.png")


def run():
    prepare()
    print("[step5] 补三个角的定位图形")
    M = np.load(WORK / "M_raw.npy")
    P = patch(M)
    np.save(WORK / "M_patched.npy", P)
    changed = P ^ M
    diff = int(changed.sum())
    corner = np.zeros_like(changed)
    for (br, bc), _ in BLOCKS:
        corner[br:br + 8, bc:bc + 8] = True
    assert not (changed & ~corner).any(), "改动溢出到三个 8×8 之外"
    print(f"    改动 {diff} 个模块，全部落在三个 8×8 块内")
    draw(M, P)
    return P


if __name__ == "__main__":
    run()
