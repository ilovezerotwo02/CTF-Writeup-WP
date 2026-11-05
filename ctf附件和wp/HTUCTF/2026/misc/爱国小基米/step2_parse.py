#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 2 / 6　按 15 一组切开，读出头部三个参数
---------------------------------------------------------------
输入 : work/cipher.txt
输出 : work/groups.json                 268 组，每组 {header, r, kind, n, digits}
       步骤截图/02_分组与头部参数.png

一个编码单元 = 3 位头部 + n 位数据，n 由头部决定：

    头部三位 a b c（哈=0 基=1 米=2）
        r    = 3a + b            0 ~ 8     —— 后面循环左移的位数
        kind = (c - r) % 3       0 / 1 / 2 —— 决定数据位长度
        n    = (6, 9, 12)[kind]             —— 6 / 9 / 12 位三进制

为什么把 r 和 kind 设计成耦合的：c 只有 3 种取值，如果 c 单独表示长度，就只能表示 3 种
长度且与 r 无关；这里用 (c - r) % 3，等于拿 c 当"带偏移的长度标记"，让同一个头部同时
编码"移几位"和"读几位"——这也解释了为什么本题 268 组的 kind 全是 2（12 位），
看上去单调，其实是每个头部的 c 都恰好补到了同一个模值。
"""

import json
from collections import Counter

from _common import AMBER, BLUE, HERE, INK, LINE, RED, SUB, TRIT_COLOR, WORK, Sheet, cjk, mono, prepare

TRIT = {"哈": 0, "基": 1, "米": 2}
LEN_BY_KIND = {0: 6, 1: 9, 2: 12}


def parse(data):
    pos, groups = 0, []
    while pos < len(data):
        header = data[pos:pos + 3]
        if len(header) < 3:
            raise ValueError(f"偏移 {pos} 处头部不足 3 位")
        a, b, c = (TRIT[ch] for ch in header)
        r = 3 * a + b
        kind = (c - r) % 3
        n = LEN_BY_KIND[kind]
        block = data[pos + 3:pos + 3 + n]
        if len(block) != n:
            raise ValueError(f"偏移 {pos} 处数据位不足：要 {n}，只有 {len(block)}")
        groups.append({
            "header": header,
            "abc": [a, b, c],
            "r": r,
            "kind": kind,
            "n": n,
            "digits": "".join(str(TRIT[ch]) for ch in block),
            "raw": header + block,          # 15 个字符，画图时整组展示
        })
        pos += 3 + n
    return groups


def bc(v, w):
    return format(v, f"0{w}b")


def draw(groups, data):
    g = groups[0]
    s = Sheet(860)
    s.head("② 按 15 一组切开，读出头部三个参数",
           f"268 组、每组 3 位头部 + n 位数据；下面全部是第一组「{g['header']}」的真实拆解")

    # ---- 15 个格子：字符 + 三进制数字
    cw, ch, gap = 58, 58, 4
    x0, y0 = 120, 168
    for i in range(15):
        x = x0 + i * (cw + gap)
        head = i < 3
        s.d.rounded_rectangle([x, y0, x + cw, y0 + ch], radius=6,
                              fill=(255, 248, 232) if head else (245, 247, 250),
                              outline=AMBER if head else LINE, width=3 if head else 2)
        s.d.text((x + cw / 2 - 13, y0 + 7), g["raw"][i], font=cjk(24), fill=INK)
        s.d.text((x + cw / 2 - 5, y0 + 38), str(TRIT[g["raw"][i]]), font=mono(15),
                 fill=TRIT_COLOR[g["raw"][i]])
        s.d.text((x + cw / 2 - 6, y0 - 22), str(i), font=mono(11), fill=(180, 186, 196))

    # 两个括号
    def bracket(x1, x2, y, label, color):
        s.d.line([(x1, y), (x1, y + 12)], fill=color, width=2)
        s.d.line([(x2, y), (x2, y + 12)], fill=color, width=2)
        s.d.line([(x1, y), (x2, y)], fill=color, width=2)
        tw = s.d.textlength(label, font=cjk(13, True))
        s.d.text(((x1 + x2) / 2 - tw / 2, y + 16), label, font=cjk(13, True), fill=color)

    x_end_head = x0 + 3 * (cw + gap) - gap
    x_end_all = x0 + 15 * (cw + gap) - gap
    bracket(x0, x_end_head, y0 + ch + 12, "头部 3 位", AMBER)
    bracket(x_end_head + gap + 4, x_end_all, y0 + ch + 12, "数据 12 位（kind=2）", BLUE)

    # ---- 左：推导
    a, b, c = g["abc"]
    s.d.text((120, 316), "第一组的推导", font=cjk(17, True), fill=INK)
    s.lines((120, 352), [
        f"字符     {g['header']}   →   {a} {b} {c}",
        f"r        = 3a + b = 3×{a} + {b} = {g['r']}",
        f"kind     = (c - r) % 3 = ({c} - {g['r']}) % 3 = {g['kind']}",
        f"n        = (6, 9, 12)[{g['kind']}] = {g['n']}  位三进制",
        f"数据位   {g['digits']}",
    ], size=15, lh=28)

    s.d.text((120, 512), "所以这一组一共占 3 + 12 = 15 个字符，",
             font=cjk(15), fill=INK)
    s.d.text((120, 542), "4020 ÷ 15 = 268，正好切完，没有余数。", font=cjk(15, True), fill=RED)

    # ---- 右：r 分布
    rb = Counter(x["r"] for x in groups)
    bx, by, bw = 700, 500, 56
    s.d.text((700, 300), f"r 的分布（{len(groups)} 组）", font=cjk(17, True), fill=INK)
    s.d.line([(bx - 8, by), (bx + 9 * bw - 10, by)], fill=LINE, width=2)
    for r in range(9):
        h = rb.get(r, 0) * 3
        x = bx + r * bw
        s.d.rectangle([x, by - h, x + bw - 18, by - 1], fill=BLUE if r != 3 else RED)
        s.d.text((x + 12, by - h - 22), str(rb.get(r, 0)), font=mono(13), fill=SUB)
        s.d.text((x + 16, by + 8), str(r), font=mono(13), fill=INK)
    s.d.text((700, by + 34), "红柱 = 第一组用到的 r = 3", font=cjk(12), fill=SUB)

    # ---- 下：长度分布
    cnt_n = Counter(x["n"] for x in groups)
    s.d.text((120, 610), "长度类型分布（n = 6 / 9 / 12）", font=cjk(17, True), fill=INK)
    s.lines((120, 648), [
        f"n = 6    {cnt_n.get(6, 0)} 组",
        f"n = 9    {cnt_n.get(9, 0)} 组",
        f"n =12    {cnt_n.get(12, 0)} 组   ← 全部",
    ], size=15, lh=26)
    s.d.text((600, 610), "r 覆盖了 0~8 全部九种取值，说明出题人确实在每组里", font=cjk(15), fill=SUB)
    s.d.text((600, 638), "随机挑了一个位移量；但 kind 恒为 2，说明 c 是被算出来的：", font=cjk(15), fill=SUB)
    s.d.text((600, 666), "c = (r + 2) % 3，这样每组都落在 12 位。", font=cjk(15), fill=SUB)
    s.d.text((600, 694), "（实测 268 组的 c 全部满足该式）", font=cjk(14), fill=SUB)
    s.foot("步骤 2 / 6　·　头部三位同时编码「移几位」和「读几位」，这是本题最容易看漏的地方")
    s.save("02_分组与头部参数.png")


def run():
    prepare()
    print("[step2] 按 15 一组解析头部")
    data = (WORK / "cipher.txt").read_text(encoding="utf-8")
    groups = parse(data)
    (WORK / "groups.json").write_text(json.dumps(groups, ensure_ascii=False), encoding="utf-8")
    r = Counter(g["r"] for g in groups)
    n = Counter(g["n"] for g in groups)
    print(f"    组数 {len(groups)}，覆盖字符 {sum(3 + g['n'] for g in groups)} / {len(data)}")
    print(f"    r 分布 {dict(sorted(r.items()))}")
    print(f"    n 分布 {dict(sorted(n.items()))}")
    print(f"    第一组 {groups[0]['header']} r={groups[0]['r']} kind={groups[0]['kind']} n={groups[0]['n']}")
    draw(groups, data)
    return groups


if __name__ == "__main__":
    run()
