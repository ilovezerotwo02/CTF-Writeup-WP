#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 1 / 8　解包 GIF，逐帧导出
---------------------------------------------------------------
输入 : 陀螺.zip
输出 : frames/f00.png ... f16.png      （17 帧，统一转成 RGBA）
       步骤截图/01_拆帧与异常帧.png      （每帧缩略图 + 色数 + alpha 包围盒）

为什么先拆帧: GIF 是逐帧动画，异常信息最常藏在「某一帧里」，拆开按体积 / 色数排一遍，
异常帧自己会跳出来。这里统计两个指标：
    1. RGB 唯一色数      正常画面 200+ 色，纯色图只有 1 色
    2. alpha 包围盒      非透明区域的外接矩形，能看出这帧到底画了多大一块
"""

from zipfile import ZipFile

from PIL import Image, ImageSequence

from _common import FRAMES, HERE, N, SUB, INK, RED, CARD, LINE, Sheet, cjk, mono, prepare


def unpack():
    """解压并拆帧，返回 (帧列表, 画布尺寸, 来源描述, 每帧统计)。"""
    prepare()
    zips = sorted(HERE.glob("*.zip"))
    if not zips:
        raise SystemExit("当前目录没有 .zip")
    src = zips[0]

    with ZipFile(src) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".gif")]
        if not names:
            raise SystemExit("压缩包里没有 gif")
        z.extract(names[0], HERE / "work" / "_unzip")
        gif = HERE / "work" / "_unzip" / names[0]
        info = f"{src.name} → {names[0]}（{z.getinfo(names[0]).file_size} 字节）"

    im = Image.open(gif)
    frames = [fr.convert("RGBA") for fr in ImageSequence.Iterator(im)]

    stats = []
    for i, fr in enumerate(frames):
        fr.save(FRAMES / f"f{i:02d}.png")
        cols = fr.convert("RGB").getcolors(maxcolors=1 << 20) or []
        bb = fr.split()[3].getbbox()
        stats.append((len(cols), f"{bb[2]-bb[0]}×{bb[3]-bb[1]}" if bb else "空"))

    return frames, im.size, info, stats


def draw(frames, size, info, stats):
    s = Sheet(1000)
    s.head("① 解包 GIF，逐帧导出",
           f"{info}；画布 {size[0]}×{size[1]}，共 {len(frames)} 帧（P 模式调色板 + 透明色）")

    cols, cw, ch = 6, 192, 240
    x0, y0 = 56, 152
    for i, fr in enumerate(frames):
        r, c = divmod(i, cols)
        bx, by = x0 + c * cw, y0 + r * ch
        odd = i == len(frames) - 1
        s.d.rounded_rectangle([bx, by, bx + cw - 16, by + ch - 16], radius=8,
                              fill=(255, 245, 245) if odd else CARD,
                              outline=RED if odd else LINE, width=3 if odd else 1)
        bg = Image.new("RGBA", fr.size, (255, 255, 255, 255))
        bg.alpha_composite(fr)
        s.paste(bg, (bx + 12, by + 12, bx + cw - 28, by + ch - 72))
        ncol, area = stats[i]
        s.d.text((bx + 10, by + ch - 62), f"f{i:02d}", font=cjk(14, True), fill=RED if odd else INK)
        s.d.text((bx + 52, by + ch - 61), f"{ncol} 色", font=cjk(13), fill=RED if odd else SUB)
        s.d.text((bx + 10, by + ch - 40), f"alpha {area}", font=mono(12), fill=SUB)

    s.d.text((56, 900),
             "前 16 帧都是 200+ 色的动画画面；只有最后一帧 f16 只剩 1 种颜色、alpha 只剩 211×211。",
             font=cjk(16), fill=INK)
    s.d.text((56, 930), "它根本不是「画面」，是一张二维码。", font=cjk(16, True), fill=RED)
    s.foot("步骤 1 / 8　·　判据：色数 + alpha 包围盒，两个数字同时塌缩的那一帧就是异物")
    s.save("01_拆帧与异常帧.png")


def run():
    print("[step1] 解包 + 拆帧")
    frames, size, info, stats = unpack()
    print(f"    画布 {size[0]}×{size[1]}，{len(frames)} 帧")
    for i, (n, a) in enumerate(stats):
        print(f"    f{i:02d}.png  色数 {n:4d}  alpha {a}")
    draw(frames, size, info, stats)
    return frames, size, info, stats


if __name__ == "__main__":
    run()
