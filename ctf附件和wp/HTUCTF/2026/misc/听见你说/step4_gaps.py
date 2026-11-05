#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 4 / 8　定位缺口：三个角各空了一个 8×8
---------------------------------------------------------------
输入 : frames/f16.png, work/M_raw.npy
输出 : 步骤截图/04_定位缺口.png

为什么缺口一定是 8×8，而不是 7×7：
    定位图形（finder）7×7 + 白色分隔符 1 圈 = 8×8。
    三个角的这一块连同分隔符一起被抠掉，所以补的时候要连分隔符一起给回去。

为什么不能把回字直接贴在角上：
    QR 的三个定位图形分别在 左上、右上、左下。左上的图形贴着 (0,0)；
    右上要从第 22 列开始（第 21 列是分隔符），左下要从第 22 行开始。
    贴到角上 = 分隔符跑到外面，扫码器按 1:1:3:1:1 找图形时会直接判失败。
    这一点踩过坑：第一版按「贴角」补，三个回字看着都在，两个主流解码器全不认。
"""

import numpy as np
from PIL import Image

from _common import BLOCKS, FRAMES, N, INK, LINE, RED, SUB, WORK, Sheet, cjk, prepare


def gap_report(M):
    """统计三个 8×8 空白块里黑模块的个数——应该是 0。"""
    out = []
    for (br, bc), (fr, fc) in BLOCKS:
        blk = M[br:br + 8, bc:bc + 8]
        out.append((br, bc, int(blk.sum())))
    return out


def draw(M, report):
    s = Sheet(760)
    s.head("④ 定位缺口：三个角各空一个 8×8",
           "定位图形 7×7 + 分隔符 1 格 = 8×8；三个角连同分隔符一起被抠掉，只伤功能区，不伤数据区")

    img = Image.open(FRAMES / "f16.png").convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.alpha_composite(img)
    big = bg.convert("RGB").resize((img.width * 2, img.height * 2), Image.NEAREST)
    s.img.paste(big, (56, 150))
    s.d.rectangle([56, 150, 56 + big.width, 150 + big.height], outline=LINE, width=2)

    ox, oy = 15 * 2 + 56, 15 * 2 + 150
    step = 211 / N * 2
    labels = ["左上", "右上", "左下"]
    for (br, bc, cnt), nm in zip(report, labels):
        x0, y0 = ox + bc * step, oy + br * step
        s.d.rectangle([x0, y0, x0 + 8 * step, y0 + 8 * step], outline=RED, width=4)
        # 名字标在框外上方，数量写在框心，避免标签压到旁边的数据区
        nw = s.d.textlength(nm, font=cjk(13, True))
        s.d.rectangle([x0 + 4, y0 - 26, x0 + 12 + nw, y0 - 2], fill=RED)
        s.d.text((x0 + 8, y0 - 24), nm, font=cjk(13, True), fill=(255, 255, 255))
        t = f"{cnt} 个黑模块"
        tw = s.d.textlength(t, font=cjk(12))
        cx, cy = x0 + 4 * step, y0 + 4 * step
        s.d.text((cx - tw / 2, cy - 9), t, font=cjk(12), fill=SUB)

    s.d.text((700, 150), "缺口尺寸怎么来的", font=cjk(16, True), fill=INK)
    s.lines((700, 188), [
        "定位图形        7 × 7",
        "分隔符（白）    1 格",
        "合计            8 × 8",
    ], size=15, lh=28)

    s.d.text((700, 300), "补回去不能直接贴在角上", font=cjk(16, True), fill=RED)
    s.lines((700, 338), [
        "左上：图形贴 (0, 0)",
        "右上：图形从第 22 列起，第 21 列留白",
        "左下：图形从第 22 行起，第 21 行留白",
        "（贴到角上 = 分隔符跑到外侧，扫码器认不出）",
    ], size=14, lh=26, mark={4})

    s.d.text((700, 470), "右下角本来就没有定位图形，但有对齐图形", font=cjk(16, True), fill=INK)
    s.lines((712, 508), ["#####", "#...#", "#.#.#", "#...#", "#####"], size=17, lh=22)
    s.d.text((822, 506), "5×5，中心一个黑点，\nVersion ≥ 2 才有。\n补角时不要碰它。", font=cjk(13), fill=SUB)
    s.foot("步骤 4 / 8　·　缺角不可怕，可怕的是把回字贴到角上——那会把自己的答案堵死")
    s.save("04_定位缺口.png")


def run():
    prepare()
    print("[step4] 检查三个角")
    M = np.load(WORK / "M_raw.npy")
    report = gap_report(M)
    for (br, bc, cnt) in report:
        print(f"    块 ({br:2d},{bc:2d}) 8×8 内黑模块 = {cnt}")
    assert all(c == 0 for _, _, c in report), "角上有黑模块，说明缺口位置判断错了"
    draw(M, report)
    return report


if __name__ == "__main__":
    run()
