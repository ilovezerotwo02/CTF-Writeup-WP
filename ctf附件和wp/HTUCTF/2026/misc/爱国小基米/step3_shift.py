#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 3 / 6　循环左移 + 码点还原（第一层真正解出汉字）
---------------------------------------------------------------
输入 : work/groups.json
输出 : work/stage1.txt                  268 个汉字（第一层结果）
       步骤截图/03_循环左移与码点.png

三件事，顺序不能反：
    1. 数据位是「循环左移 r 位」之后才存进去的，先移回来：shifted = digits[r:] + digits[:r]
    2. 移回来的 12 位三进制转十进制，得 v
    3. codepoint = v - 3 - r，才是真正的 Unicode 码点

-3 是固定偏移，-r 是让不同 r 的码点区间互相错开：如果只减 3，那么"左移后在末尾补 r 个 0"
会让多个不同的 r 落到同一个 v 上，码点就会撞车；减掉 r 之后映射是一一对应的。
"""

import json

import numpy as np

from _common import BLUE, HERE, INK, LINE, RED, SUB, WORK, Sheet, cjk, mono, prepare


def decode(groups):
    out = []
    for i, g in enumerate(groups):
        d = g["digits"]
        r = g["r"]
        shifted = d[r:] + d[:r]                     # 循环左移 r 位 = 把头部切下来贴到尾部
        v = int(shifted, 3)
        cp = v - 3 - r
        out.append({**g, "no": i + 1, "shifted": shifted, "v": v, "cp": cp, "char": chr(cp)})
    return out


def draw(rows, g):
    s = Sheet(900)
    s.head("③ 循环左移 r 位 → 三进制转十进制 → 减偏移得码点",
           f"以第 {g['no']} 组「{g['header']}」为例：数据 12 位循环左移 {g['r']} 位，转成 v，再减去 3 + r")

    # ---- 上：两行 12 格，上=原始，下=移位后
    cw, ch, gap = 64, 46, 4
    x0 = 120
    n = len(g["digits"])

    def row(y, digits, title, hot_from=None):
        s.d.text((x0, y - 26), title, font=cjk(14), fill=SUB)
        for i, chd in enumerate(digits):
            x = x0 + i * (cw + gap)
            hot = hot_from is not None and i >= hot_from
            s.d.rounded_rectangle([x, y, x + cw, y + ch], radius=5,
                                  fill=(255, 242, 242) if hot else (245, 247, 250),
                                  outline=RED if hot else (BLUE if hot_from is not None else LINE),
                                  width=2)
            s.d.text((x + cw / 2 - 6, y + 10), chd, font=mono(19), fill=INK)

    row(176, g["digits"], f"原始数据位   {g['digits']}")
    row(258, g["shifted"], f"循环左移 {g['r']} 位后   {g['shifted']}", hot_from=n - g["r"])

    # 移位箭头：前 r 位搬到尾部
    ax = x0 + n * (cw + gap) + 6
    s.d.line([(ax + 12, 176 + ch / 2), (ax + 12, 258 + ch / 2)], fill=SUB, width=2)
    s.d.polygon([(ax + 12, 258 + ch / 2), (ax + 6, 258 + ch / 2 - 9), (ax + 18, 258 + ch / 2 - 9)], fill=SUB)
    s.d.text((ax + 26, 206), "前 r 位", font=cjk(12), fill=SUB)
    s.d.text((ax + 26, 226), "接到末尾", font=cjk(12), fill=SUB)

    # ---- 左下：算到底
    s.d.text((120, 350), f"算到底（第 {g['no']} 组）", font=cjk(17, True), fill=INK)
    s.lines((120, 388), [
        f"digits    {g['digits']}",
        f"shifted   {g['shifted']}",
        f"v         = int(shifted, 3) = {g['v']}",
        f"cp        = v - 3 - r = {g['v']} - 3 - {g['r']} = {g['cp']}",
        f"chr(cp)   = {g['char']}",
    ], size=15, lh=28, mark={5})

    # ---- 右下：前三组表
    s.d.text((700, 350), "前三组连算", font=cjk(17, True), fill=INK)
    head = ["组", "头部", "r", "v", "码点", "字符"]
    offs = [0, 56, 176, 216, 316, 416]
    for j, h in enumerate(head):
        s.d.text((700 + offs[j], 392), h, font=cjk(13, True), fill=SUB)
    s.d.line([(700, 418), (1180, 418)], fill=LINE, width=1)
    for i, r in enumerate(rows[:3]):
        y = 430 + i * 32
        vals = [str(i + 1), r["header"], str(r["r"]), str(r["v"]), str(r["cp"]), r["char"]]
        for j, v in enumerate(vals):
            f = mono(14) if j in (2, 3, 4) else cjk(15)
            s.d.text((700 + offs[j], y), v, font=f, fill=INK)

    # ---- 底部：输出
    text = "".join(r["char"] for r in rows)
    (WORK / "stage1.txt").write_text(text, encoding="utf-8")

    s.d.text((120, 560), f"按同样方法解完 {len(rows)} 组，得到 {len(text)} 个汉字（下面是前 78 个）：",
             font=cjk(16, True), fill=INK)
    prev = text[:78]
    s.d.text((120, 596), prev[:26], font=cjk(20), fill=INK)
    s.d.text((120, 632), prev[26:52], font=cjk(20), fill=INK)
    s.d.text((120, 668), prev[52:], font=cjk(20), fill=INK)

    s.d.text((120, 724), f"{len(text)} 个字里只有 {len(set(text))} 个不同的字，而且全部来自一个固定集合：",
             font=cjk(15), fill=SUB)
    s.d.text((120, 754), "富强 民主 文明 和谐 自由 平等 公正 法治 爱国 敬业 诚信 友善",
             font=cjk(16, True), fill=RED)
    s.foot("步骤 3 / 6　·　第一层到此结束：从「三个字的三进制」变成了「核心价值观词组」")
    s.save("03_循环左移与码点.png")


def run():
    prepare()
    print("[step3] 循环左移 + 码点还原")
    groups = json.loads((WORK / "groups.json").read_text(encoding="utf-8"))
    rows = decode(groups)
    # 选一组做「移位」演示：前 r 位不能全是 0，否则图上看起来像没动
    ex = next(r for r in rows if r["r"] > 0 and len(set(r["digits"][:r["r"]])) > 1)
    for r in rows[:3]:
        print(f"    {r['header']} r={r['r']} {r['digits']} → {r['shifted']} → v={r['v']} cp={r['cp']} {r['char']}")
    bad = [r for r in rows if not (0x4E00 <= r["cp"] <= 0x9FFF)]
    print(f"    268 组中超出 CJK 基本区的：{len(bad)}")
    assert not bad, "出现了非汉字码点，说明规则有误"
    text = "".join(r["char"] for r in rows)
    print(f"    第一层输出 {len(text)} 字，不同字 {len(set(text))} 个")
    print(f"    开头：{text[:40]}")
    print(f"    演示组：第 {ex['no']} 组 {ex['header']} r={ex['r']} {ex['digits']} → {ex['shifted']}")
    draw(rows, ex)
    return text


if __name__ == "__main__":
    run()
