#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 2 / 8　锁定异常帧，并放大看它到底是什么
---------------------------------------------------------------
输入 : frames/f00.png ... f16.png
输出 : 步骤截图/02_异常帧放大.png

判据只有两条，都不需要「看图猜」：
    1. RGB 唯一色数最少的那一帧
    2. alpha 只有 0/255 两个值（不是渐变的抗锯齿边缘）

f16 的结果：RGB 唯一值 1 个 (#000000)，alpha 唯一值 2 个，非透明包围盒 211×211。
黑底 + 只有透明度在变 = 一张「透明底黑模块」的二维码。
"""

import numpy as np
from PIL import Image

from _common import FRAMES, N, INK, LINE, RED, SUB, Sheet, cjk, prepare


def pick_odd(frames_dir=FRAMES):
    """按色数挑出异常帧，返回 (下标, 统计表)。"""
    stats = []
    for p in sorted(frames_dir.glob("f*.png")):
        fr = Image.open(p).convert("RGBA")
        cols = fr.convert("RGB").getcolors(maxcolors=1 << 20) or []
        bb = fr.split()[3].getbbox()
        stats.append((p.name, len(cols), f"{bb[2]-bb[0]}×{bb[3]-bb[1]}" if bb else "空"))
    idx = min(range(len(stats)), key=lambda i: stats[i][1])
    return idx, stats


def inspect(path):
    """把一帧拆成人话：色数、alpha 取值、包围盒、模块尺寸。"""
    fr = Image.open(path).convert("RGBA")
    a = np.array(fr)
    alpha = a[:, :, 3]
    ys, xs = np.where(alpha > 0)
    w = xs.max() - xs.min() + 1
    return {
        "colors": len(fr.convert("RGB").getcolors(maxcolors=1 << 20) or []),
        "alpha_values": sorted(set(alpha.ravel().tolist())),
        "rgb": [int(v) for v in a[ys[0], xs[0], :3]],
        "bbox": (int(xs.min()), int(ys.min()), int(w), int(ys.max() - ys.min() + 1)),
        "module_px": w / N,
        "image": fr,
    }


def draw(info):
    s = Sheet(830)
    s.head("② 异常帧放大：一张被挖掉三个角的二维码",
           "f16 的 RGB 全为 #000000，只有 alpha 在 0 / 255 之间跳；棋盘格处即透明像素")

    s.paste(info["image"], (56, 150, 620, 700), checker=True)
    s.d.rectangle([56, 150, 620, 700], outline=LINE, width=2)
    s.d.text((56, 714), "棋盘格 = 透明；中间那块黑色 211×211 才是图案本体", font=cjk(15), fill=SUB)

    # 左上角 8×8：拿 11×11 模块的画面，红框圈出空掉的那 8×8
    x0, y0 = info["bbox"][0], info["bbox"][1]
    crop = info["image"].crop((x0, y0, x0 + 80, y0 + 80)).resize((300, 300), Image.NEAREST)
    bg = Image.new("RGBA", crop.size, (255, 255, 255, 255))
    bg.alpha_composite(crop)
    s.img.paste(bg.convert("RGB"), (700, 190))
    s.d.rectangle([700, 190, 1000, 490], outline=LINE, width=2)
    s.d.text((700, 156), "左上角放大（含右侧数据区）", font=cjk(16, True), fill=INK)
    st = 300 / 80 * info["module_px"]
    s.d.rectangle([700, 190, 700 + 8 * st, 190 + 8 * st], outline=RED, width=3)
    s.d.text((700, 494), "红框内 8×8 全空 —— 本该是 7×7 回字 + 一圈白分隔符", font=cjk(14), fill=RED)

    s.d.text((700, 536), "像素统计", font=cjk(16, True), fill=INK)
    s.lines((700, 572), [
        "RGB  唯一值    : {}   (#{:02x}{:02x}{:02x})".format(
            info["colors"], *info["rgb"]),
        "alpha 唯一值   : {}   {}".format(len(info["alpha_values"]), info["alpha_values"]),
        "非透明包围盒   : {} × {} px".format(info["bbox"][2], info["bbox"][3]),
        "211 / 29       = {:.4f} px 每模块".format(info["module_px"]),
    ], size=15, lh=27)
    s.foot("步骤 2 / 8　·　只用三个汉字做密文的题是编码题，只用一种颜色做画面的帧就是二维码")
    s.save("02_异常帧放大.png")


def run():
    prepare()
    idx, stats = pick_odd()
    print(f"[step2] 异常帧 = {stats[idx][0]}（色数 {stats[idx][1]}）")
    info = inspect(FRAMES / stats[idx][0])
    print(f"    RGB {info['colors']} 色, alpha {info['alpha_values']}, bbox {info['bbox']}")
    print(f"    模块边长 {info['module_px']:.4f} px")
    draw(info)
    return idx, info


if __name__ == "__main__":
    run()
