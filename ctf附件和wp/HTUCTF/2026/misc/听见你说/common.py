#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_common.py —— 画布 / 字体 / 绘图小工具

只做「把结论画成图」这件事，不含任何解题逻辑。
step1 ~ step8 与 solve.py 共用，避免八份排版代码各自跑偏。
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SHOTS = HERE / "步骤截图"
OUT = HERE / "输出"
FRAMES = HERE / "frames"
WORK = HERE / "work"

W = 1280
INK = (28, 32, 40)
SUB = (112, 120, 132)
LINE = (224, 228, 235)
BG = (255, 255, 255)
RED = (192, 45, 45)
GREEN = (22, 122, 70)
BLUE = (30, 110, 200)
ORANGE = (222, 126, 20)
CARD = (250, 251, 253)


def _f(path, size, index=0):
    try:
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.load_default()


def cjk(size, bold=False):
    return _f("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc", size)


def mono(size):
    return _f("C:/Windows/Fonts/consola.ttf", size)


def has_cjk(s):
    return any(ord(ch) > 0x2E80 for ch in s)


def prepare():
    """确保输出目录存在。"""
    for p in (SHOTS, OUT, FRAMES, WORK):
        p.mkdir(exist_ok=True)


class Sheet:
    """一张 1280 宽的画布，带标题 / 页脚 / 卡片 / 代码块 / 终端面板。"""

    def __init__(self, h):
        self.h = h
        self.img = Image.new("RGB", (W, h), BG)
        self.d = ImageDraw.Draw(self.img)

    def head(self, title, sub=""):
        self.d.text((56, 40), title, font=cjk(29, True), fill=INK)
        if sub:
            self.d.text((56, 84), sub, font=cjk(15), fill=SUB)
        self.d.line([(56, 120), (W - 56, 120)], fill=LINE, width=2)

    def foot(self, txt):
        self.d.text((56, self.h - 44), txt, font=cjk(13), fill=(158, 164, 174))

    def card(self, box, title=None, fill=CARD, radius=10):
        x0, y0, x1, y1 = box
        self.d.rounded_rectangle(box, radius=radius, fill=fill, outline=LINE, width=2)
        if title:
            self.d.rounded_rectangle([x0, y0, x1, y0 + 38], radius=radius, fill=(238, 241, 246))
            self.d.rectangle([x0, y0 + 26, x1, y0 + 38], fill=(238, 241, 246))
            self.d.text((x0 + 14, y0 + 9), title, font=cjk(15, True), fill=(66, 72, 84))

    def lines(self, xy, rows, size=15, lh=25, color=(58, 64, 76), mark=None):
        """逐行写字；含中文的行自动换中文字体，避免方块乱码。"""
        x, y = xy
        for i, t in enumerate(rows, 1):
            f = cjk(size - 1) if has_cjk(t) else mono(size)
            c = RED if mark and i in mark else color
            self.d.text((x, y + (i - 1) * lh), t, font=f, fill=c)

    def matrix(self, xy, M, cell=14, gap=1):
        """按像素画模块矩阵：黑块 + 浅灰空格。"""
        x, y = xy
        for r in range(M.shape[0]):
            for c in range(M.shape[1]):
                fill = (34, 40, 50) if M[r, c] else (238, 241, 246)
                self.d.rectangle([x + c * cell, y + r * cell,
                                  x + c * cell + cell - gap, y + r * cell + cell - gap], fill=fill)

    def terminal(self, box, rows):
        x0, y0, x1, y1 = box
        self.d.rounded_rectangle(box, radius=10, fill=(24, 26, 32))
        self.d.rounded_rectangle([x0, y0, x1, y0 + 32], radius=10, fill=(38, 42, 52))
        self.d.rectangle([x0, y0 + 24, x1, y0 + 32], fill=(38, 42, 52))
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            self.d.ellipse([x0 + 16 + i * 22, y0 + 11, x0 + 26 + i * 22, y0 + 21], fill=c)
        self.d.text((x0 + 96, y0 + 8), "Windows PowerShell", font=cjk(12), fill=(150, 156, 168))
        y = y0 + 48
        for kind, text in rows:
            color = {"prompt": (126, 214, 122), "out": (208, 214, 224),
                     "ok": (110, 210, 155), "flag": (255, 210, 96), "dim": (138, 146, 160)}[kind]
            line = ("PS> " if kind == "prompt" else "     ") + text
            f = cjk(14) if has_cjk(line) else mono(15)
            self.d.text((x0 + 20, y), line, font=f, fill=color)
            y += 22
        return y

    def paste(self, im, box, checker=False):
        x0, y0, x1, y1 = box
        bw, bh = x1 - x0, y1 - y0
        k = min(bw / im.width, bh / im.height)
        nw, nh = max(1, int(im.width * k)), max(1, int(im.height * k))
        im2 = im.resize((nw, nh), Image.NEAREST)
        px, py = x0 + (bw - nw) // 2, y0 + (bh - nh) // 2
        if checker:
            bgc = Image.new("RGB", (nw, nh), (255, 255, 255))
            dc = ImageDraw.Draw(bgc)
            s = 14
            for yy in range(0, nh, s):
                for xx in range(0, nw, s):
                    if (xx // s + yy // s) % 2:
                        dc.rectangle([xx, yy, xx + s - 1, yy + s - 1], fill=(231, 234, 239))
            self.img.paste(bgc, (px, py))
            self.img.paste(im2, (px, py), im2 if im2.mode == "RGBA" else None)
        else:
            self.img.paste(im2.convert("RGB"), (px, py))
        return px, py, nw, nh

    def save(self, name):
        p = SHOTS / name
        self.img.save(p)
        print(f"    → {p.relative_to(HERE)}  ({p.stat().st_size // 1024} KB)")
        return p


# ---------------------------------------------------------------- 共用常量
N = 29
FINDER = ["#######", "#.....#", "#.###.#", "#.###.#", "#.###.#", "#.....#", "#######"]
# (8×8 空白块左上角, 7×7 图形左上角)：右上 / 左下必须内缩 1 格，把最外一行一列留成白色分隔符
BLOCKS = [((0, 0), (0, 0)), ((0, N - 8), (0, N - 7)), ((N - 8, 0), (N - 7, 0))]


def render(M, scale=10, quiet=4):
    """把布尔矩阵画成干净的黑白二维码。"""
    n = M.shape[0]
    side = (n + 2 * quiet) * scale
    img = Image.new("RGB", (side, side), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for r in range(n):
        for c in range(n):
            if M[r, c]:
                d.rectangle([(c + quiet) * scale, (r + quiet) * scale,
                             (c + quiet + 1) * scale - 1, (r + quiet + 1) * scale - 1], fill=(0, 0, 0))
    return img


def load_frame(i):
    return Image.open(FRAMES / f"f{i:02d}.png").convert("RGBA")


def frame_stats(i):
    fr = load_frame(i)
    cols = fr.convert("RGB").getcolors(maxcolors=1 << 20) or []
    bb = fr.split()[3].getbbox()
    return len(cols), (f"{bb[2]-bb[0]}×{bb[3]-bb[1]}" if bb else "空")
