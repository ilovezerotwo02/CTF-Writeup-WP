#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_common.py —— 画布 / 字体 / 绘图小工具（只负责出图，不含解题逻辑）

step1 ~ step6 与 solve.py 共用，避免六份排版代码各自跑偏。
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SHOTS = HERE / "步骤截图"
WORK = HERE / "work"

W = 1280
INK = (28, 32, 40)
SUB = (112, 120, 132)
LINE = (224, 228, 235)
BG = (255, 255, 255)
RED = (192, 45, 45)
GREEN = (22, 122, 70)
BLUE = (47, 111, 235)
AMBER = (222, 150, 10)
CARD = (250, 251, 253)

# 三个字的三色约定（后面每张图都用同一套颜色，方便对照）
TRIT_COLOR = {"哈": (47, 111, 235), "基": (224, 161, 0), "米": (214, 69, 69)}


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
    for p in (SHOTS, WORK):
        p.mkdir(exist_ok=True)


class Sheet:
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

    def lines(self, xy, rows, size=15, lh=25, color=(58, 64, 76), mark=None, markcolor=RED):
        """逐行写字；含中文的行自动换中文字体，避免方块乱码。"""
        x, y = xy
        for i, t in enumerate(rows, 1):
            f = cjk(size - 1) if has_cjk(t) else mono(size)
            c = markcolor if mark and i in mark else color
            self.d.text((x, y + (i - 1) * lh), t, font=f, fill=c)

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

    def save(self, name):
        p = SHOTS / name
        self.img.save(p)
        print(f"    → {p.relative_to(HERE)}  ({p.stat().st_size // 1024} KB)")
        return p
