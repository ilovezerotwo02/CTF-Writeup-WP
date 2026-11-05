#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 4 / 6　核心价值观词组 → 数值序列
---------------------------------------------------------------
输入 : work/stage1.txt（268 个汉字）
输出 : work/values.json                134 个数值 + 扩展标记位置
       步骤截图/04_词组映射与数值序列.png

第二层的字母表是固定的 12 个词组，按官方顺序编号 0~11：

    富强 0   民主 1   文明 2   和谐 3
    自由 4   平等 5   公正 6   法治 7
    爱国 8   敬业 9   诚信 10  友善 11

268 个字 = 134 个词组。这里先只做"字 → 数"的映射，并找出 10 / 11 的位置——
它们不是普通数位，而是"扩展标记"，要吃掉后面一个词组才凑得出 0xa~0xf。
"""

import json
from collections import Counter

from _common import AMBER, BLUE, GREEN, INK, LINE, RED, SUB, WORK, Sheet, cjk, mono, prepare

ALPHABET = "富强民主文明和谐自由平等公正法治爱国敬业诚信友善"
PHRASES = [ALPHABET[i:i + 2] for i in range(0, len(ALPHABET), 2)]
VALUE_OF = {w: i for i, w in enumerate(PHRASES)}


def to_values(text):
    if len(text) % 2:
        raise ValueError(f"字符数 {len(text)} 是奇数，无法两字一组")
    return [VALUE_OF[text[i:i + 2]] for i in range(0, len(text), 2)]


def draw(text, values):
    s = Sheet(900)
    s.head("④ 核心价值观词组 → 数值序列",
           f"{len(text)} 个字按两字一组切，得到 {len(values)} 个数值；其中 10 / 11 是扩展标记，不是普通数位")

    # ---- 左：映射表
    s.d.text((60, 156), "固定字母表（12 个词组 = 0~11）", font=cjk(16, True), fill=INK)
    for i, w in enumerate(PHRASES):
        col, row = divmod(i, 6)
        x = 60 + col * 230
        y = 194 + row * 46
        ext = i >= 10
        s.d.rounded_rectangle([x, y, x + 214, y + 38], radius=6,
                              fill=(255, 240, 240) if ext else (247, 249, 252),
                              outline=RED if ext else LINE, width=2)
        s.d.text((x + 12, y + 8), w, font=cjk(17, True), fill=INK)
        s.d.text((x + 150, y + 9), str(i), font=mono(16), fill=RED if ext else BLUE)

    # ---- 右：前 10 个词组的映射
    s.d.text((600, 156), "前 10 个词组逐字对照", font=cjk(16, True), fill=INK)
    for i in range(10):
        x = 600 + (i % 5) * 124
        y = 194 + (i // 5) * 84
        pair = text[i * 2:i * 2 + 2]
        s.d.rounded_rectangle([x, y, x + 112, y + 66], radius=6, fill=(247, 249, 252), outline=LINE, width=1)
        s.d.text((x + 8, y + 6), pair, font=cjk(15), fill=INK)
        s.d.text((x + 8, y + 32), f"= {values[i]}", font=mono(16), fill=BLUE)

    # ---- 扩展标记统计
    cnt = Counter(values)
    s.d.text((600, 386), "扩展标记（10 / 11）", font=cjk(16, True), fill=INK)
    s.lines((600, 424), [
        f"诚信 = 10   出现 {cnt[10]} 次",
        f"友善 = 11   出现 {cnt[11]} 次",
        f"两者合计    {cnt[10] + cnt[11]} 处",
        f"→ 每处再吃一个词组，所以数位 = {len(values)} - {cnt[10] + cnt[11]} = {len(values) - cnt[10] - cnt[11]}",
    ], size=15, lh=27)

    s.d.text((600, 560), "为什么要有扩展标记", font=cjk(16, True), fill=INK)
    s.lines((600, 598), [
        "12 个词组只能表示 0~11，但十六进制要 0~15。",
        "于是 10 / 11 改当\"进位开关\"：",
        "  10 + 下一个  →  0xa ~ 0xf",
        "  6  + 下一个  →  0xa ~ 0xf",
        "两条路都能到 10~15，取哪条由后一个词组的取值范围自然决定。",
    ], size=14, lh=25)

    # ---- 底部：134 个数值的色带
    y0 = 760
    s.d.text((60, y0 - 34), f"{len(values)} 个数值（灰 = 0~9，红 = 10，蓝 = 11）", font=cjk(14), fill=SUB)
    bw = 8
    for i, v in enumerate(values):
        c = RED if v == 10 else (BLUE if v == 11 else (198, 202, 210))
        x = 60 + i * bw
        s.d.rectangle([x, y0, x + bw, y0 + 42], fill=c)
    s.d.text((60, y0 + 54), "整条序列里扩展标记分布零散，不是集中在尾部——说明它是按数据本身的需要插入的，不能简单按位置跳过。",
             font=cjk(14), fill=INK)
    s.foot("步骤 4 / 6　·　到这一步还没有还原任何字节，只是把汉字翻译成了数字")
    s.save("04_词组映射与数值序列.png")


def run():
    prepare()
    print("[step4] 词组 → 数值")
    text = (WORK / "stage1.txt").read_text(encoding="utf-8")
    values = to_values(text)
    cnt = Counter(values)
    bad = [w for w in set(text[i:i + 2] for i in range(0, len(text), 2)) if w not in VALUE_OF]
    assert not bad, f"出现字母表外的词组：{bad}"
    (WORK / "values.json").write_text(json.dumps(values), encoding="utf-8")
    print(f"    词组数 {len(values)}，取值集合 {sorted(cnt)}")
    print(f"    10 出现 {cnt[10]} 次，11 出现 {cnt[11]} 次，合计 {cnt[10] + cnt[11]}")
    print(f"    预计数位 = {len(values)} - {cnt[10] + cnt[11]} = {len(values) - cnt[10] - cnt[11]}")
    draw(text, values)
    return values


if __name__ == "__main__":
    run()
