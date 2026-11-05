#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 7 / 8　出图：白底 + 4 模块静区 + 整数倍放大
---------------------------------------------------------------
输入 : work/M_patched.npy
输出 : 输出/修复二维码_白底静区.png
       输出/修复二维码_无静区.png
       步骤截图/07_出图.png

为什么必须重绘，而不是在原图上涂两笔：
  1. 原图模块边长 7.2758 像素，非整数，任何缩放都会让边界抖动；
  2. 原图是透明底、没有静区（quiet zone），不少解码器见到没有白边直接拒识；
  3. 重绘相当于把结论固定成一张「只依赖矩阵」的图，后人可以拿它复核。
"""

import numpy as np

from _common import INK, LINE, N, OUT, SUB, WORK, Sheet, cjk, prepare, render


def build(P, scale=10, quiet=4):
    return render(P, scale=scale, quiet=quiet)


def draw(P, im):
    s = Sheet(720)
    s.head("⑦ 出图：白底 + 4 模块静区 + 整数倍放大",
           "原图透明底、无静区，不少解码器直接拒识；重绘只动画布，不动一个数据模块")

    s.img.paste(im, (110, 160))
    s.d.rectangle([110, 160, 110 + im.width, 160 + im.height], outline=LINE, width=2)
    s.d.text((110, 160 + im.height + 12), f"{im.width} × {im.height}，每模块 10×10 px", font=cjk(14), fill=SUB)

    s.d.text((620, 160), "重绘参数", font=cjk(16, True), fill=INK)
    s.lines((620, 198), [
        "modules = 29",
        "quiet   = 4     静区（规范要求 ≥ 4 模块）",
        "scale   = 10    一模块 10×10 像素",
        f"画布    = {(N + 8) * 10} × {(N + 8) * 10}",
    ], size=15, lh=27)

    s.d.text((620, 330), "为什么不在原图上直接涂", font=cjk(16, True), fill=INK)
    s.lines((620, 368), [
        "1. 原图模块 7.28 px，非整数，缩放会抖；",
        "2. 原图没有静区，白边得靠重绘补；",
        "3. 重绘把结论固定成一张可复核的图。",
    ], size=14, lh=26)
    s.foot("步骤 7 / 8")
    s.save("07_出图.png")


def run():
    prepare()
    print("[step7] 渲染")
    P = np.load(WORK / "M_patched.npy")
    im = build(P, 10, 4)
    im.save(OUT / "修复二维码_白底静区.png")
    build(P, 8, 0).save(OUT / "修复二维码_无静区.png")
    print(f"    {im.width}×{im.height} → 输出/修复二维码_白底静区.png")
    draw(P, im)
    return im


if __name__ == "__main__":
    run()
