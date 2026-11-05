#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 3 / 8　按 29×29 切格子，把像素变成模块矩阵
---------------------------------------------------------------
输入 : frames/f16.png
输出 : work/M_raw.npy                  29×29 布尔矩阵（补角之前的原始采样）
       步骤截图/03_模块采样.png

两个关键决定：
  1. 模块数不是数出来的，是算出来的：29 = 17 + 4×3 → Version 3。
     图上的时序图形（第 6 行 / 第 6 列的黑白交替）长度也正好对上 29。
  2. 不用「格子中心点」取样。211 / 29 = 7.2758，格子宽 7~8 像素不均匀，
     中心点会踩到边界；改成整格多数表决（≥50% 黑即黑）更稳。
"""

import numpy as np
from PIL import Image

from _common import FRAMES, N, INK, LINE, RED, SUB, WORK, Sheet, cjk, mono, prepare


def alpha_sub(path):
    """取 alpha 通道，裁到非透明包围盒，返回 (布尔数组, 包围盒)。"""
    a = np.array(Image.open(path).convert("RGBA"))[:, :, 3] > 0
    ys, xs = np.where(a)
    x0, y0 = int(xs.min()), int(ys.min())
    x1, y1 = int(xs.max()) + 1, int(ys.max()) + 1
    return a[y0:y1, x0:x1], (x0, y0, x1 - x0, y1 - y0)


def bounds(total, n):
    """把 total 像素均分成 n 格，返回 n+1 个边界（四舍五入，最后一格吃掉余数）。"""
    return [round(i * total / n) for i in range(n + 1)]


def sample(sub):
    h, w = sub.shape
    by, bx = bounds(h, N), bounds(w, N)
    M = np.zeros((N, N), bool)
    for r in range(N):
        for c in range(N):
            M[r, c] = sub[by[r]:by[r + 1], bx[c]:bx[c + 1]].mean() >= 0.5
    return M, by, bx


def draw(M, bbox, by, bx):
    s = Sheet(830)
    s.head("③ 按 29×29 切格子：把像素变成模块矩阵",
           "模块边长 211/29 ≈ 7.28，格子实际是 7 或 8 像素——所以按整格多数表决，不按中心点取样")

    img = Image.open(FRAMES / "f16.png").convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.alpha_composite(img)
    big = bg.convert("RGB").resize((img.width * 2, img.height * 2), Image.NEAREST)
    s.img.paste(big, (56, 150))
    s.d.rectangle([56, 150, 56 + big.width, 150 + big.height], outline=LINE, width=2)

    # 网格线直接用采样时的边界坐标，保证「画出来的格子」和「取样的格子」是同一套
    ox, oy = bbox[0] * 2 + 56, bbox[1] * 2 + 150
    for i, x in enumerate(bx):
        col = (250, 170, 170) if i % 5 == 0 else (252, 216, 216)
        s.d.line([(ox + x * 2, oy), (ox + x * 2, oy + (by[-1] - by[0]) * 2)], fill=col, width=1)
    for i, y in enumerate(by):
        col = (250, 170, 170) if i % 5 == 0 else (252, 216, 216)
        s.d.line([(ox, oy + y * 2), (ox + (bx[-1] - bx[0]) * 2, oy + y * 2)], fill=col, width=1)
    for i in range(0, N, 4):
        s.d.text((ox + bx[i] * 2 - 5, oy - 20), str(i), font=mono(12), fill=(170, 60, 60))

    s.d.text((700, 150), "采样结果（左上 = 模块 0,0）", font=cjk(16, True), fill=INK)
    s.matrix((712, 186), M, cell=15)
    s.d.text((700, 186 + N * 15 + 16), "行 6 / 列 6 已经是 #.#.# 交替 → 网格没歪", font=cjk(14), fill=(22, 122, 70))
    s.d.text((700, 186 + N * 15 + 44), "数据模块 567 个 = 70 码字 × 8 + 7 余位（Version 3 正好如此）",
             font=cjk(14), fill=SUB)
    s.foot("步骤 3 / 8　·　先验知识：模块数 = 17 + 4×版本，29 → Version 3")
    s.save("03_模块采样.png")


def run():
    prepare()
    print("[step3] 采样 29×29")
    sub, bbox = alpha_sub(FRAMES / "f16.png")
    M, by, bx = sample(sub)
    np.save(WORK / "M_raw.npy", M)
    print(f"    包围盒 {bbox}，模块 {bbox[2] / N:.4f} px")
    row = "".join("#" if M[6, c] else "." for c in range(8, 21))
    print(f"    时序行 row6[8..20] = {row}")
    draw(M, bbox, by, bx)
    return M, bbox


if __name__ == "__main__":
    run()
