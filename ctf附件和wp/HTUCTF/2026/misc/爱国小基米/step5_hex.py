#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 5 / 6　数值序列 → 十六进制数位 → 字节流
---------------------------------------------------------------
输入 : work/values.json
输出 : work/hex.txt                     118 个十六进制数位
       work/stage2.bin                  59 字节
       步骤截图/05_扩展标记与字节流.png

扩展标记怎么吃：
    v ∈ 0..9    → 直接当作一个十六进制数位
    v == 10     → 再读一个词组 n，数位 = 10 + n
    v == 11     → 再读一个词组 n，数位 = 6  + n
两种写法都落在 0xa ~ 0xf，区别只在起点。

134 个词组里有 16 个扩展标记被消耗，所以最终数位 = 134 - 16 = 118 个 → 59 字节。
"""

import json

from _common import AMBER, BLUE, GREEN, INK, LINE, RED, SUB, WORK, Sheet, cjk, mono, prepare


def expand(values):
    digits, used = [], []
    i = 0
    while i < len(values):
        v = values[i]
        i += 1
        if v in (10, 11):
            if i >= len(values):
                raise ValueError("扩展标记出现在末尾，后面没有词组可吃")
            nxt = values[i]
            i += 1
            base = 10 if v == 10 else 6
            used.append({"at": len(digits), "mark": v, "next": nxt, "value": base + nxt})
            v = base + nxt
        if not 0 <= v <= 15:
            raise ValueError(f"数位越界：{v}")
        digits.append(v)
    return digits, used


def hexdump(data, per=10):
    rows = []
    for off in range(0, len(data), per):
        chunk = data[off:off + per]
        hx = " ".join(f"{b:02x}" for b in chunk)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        rows.append((off, hx, asc))
    return rows


def draw(values, digits, used, data, hex_text):
    s = Sheet(880)
    s.head("⑤ 扩展标记 → 十六进制数位 → 字节流",
           f"{len(values)} 个数值里消耗 {len(used)} 个扩展标记，得 {len(digits)} 个十六进制数位 = {len(data)} 字节")

    # ---- 上：扩展规则 + 实际命中位置
    s.d.text((60, 152), "扩展标记在序列里怎么被吃掉", font=cjk(16, True), fill=INK)
    ex = used[0]
    at = ex["at"]
    # 找到这个数位在 values 里的原始下标
    idx, count = 0, 0
    while count < at:
        if values[idx] in (10, 11):
            idx += 2
        else:
            idx += 1
        count += 1
    frag = values[max(0, idx - 2):idx + 4]
    s.lines((60, 190), [
        f"序列片段（原始词组值）：{(t := frag)}",
        f"读到 {ex['mark']}（{'诚信' if ex['mark'] == 10 else '友善'}）时，再吃一个 {ex['next']}：",
        f"  数位 = {'10' if ex['mark'] == 10 else '6'} + {ex['next']} = {ex['value']} = 0x{ex['value']:x}",
    ], size=14, lh=26)

    # 用小方块把这段画出来：红 = 扩展标记，虚线 = 被它吃掉的词组
    mark_at = frag.index(ex["mark"])
    x = 60
    for i, v in enumerate(frag):
        hot = i == mark_at
        eaten = i == mark_at + 1
        box = [x, 286, x + 62, 330]
        s.d.rounded_rectangle(box, radius=5,
                              fill=(255, 236, 236) if hot else ((255, 248, 235) if eaten else (245, 247, 250)),
                              outline=RED if hot else (AMBER if eaten else LINE), width=2)
        s.d.text((x + 22, 295), str(v), font=mono(16), fill=RED if hot else INK)
        if hot:
            s.d.text((x + 6, 314), "标记", font=cjk(11), fill=RED)
        if eaten:
            s.d.text((x + 6, 314), "被吃", font=cjk(11), fill=AMBER)
        x += 72
    # 括号：两格合成一个数位
    x1 = 60 + mark_at * 72
    x2 = x1 + 72 + 62
    s.d.line([(x1, 344), (x1, 356)], fill=SUB, width=2)
    s.d.line([(x2, 344), (x2, 356)], fill=SUB, width=2)
    s.d.line([(x1, 356), (x2, 356)], fill=SUB, width=2)
    s.d.text((x1 + 40, 362), f"两格合成一个数位 0x{ex['value']:x}", font=cjk(12), fill=SUB)

    # ---- 中：hexdump
    s.d.text((60, 400), "恢复出来的字节（59 个）", font=cjk(16, True), fill=INK)
    rows = hexdump(data)
    y = 438
    for off, hx, asc in rows:
        s.d.text((60, y), f"{off:04x}", font=mono(13), fill=SUB)
        s.d.text((116, y), hx, font=mono(14), fill=INK)
        s.d.text((470, y), asc, font=mono(14), fill=BLUE)
        y += 24
    s.d.line([(460, 430), (460, y - 8)], fill=LINE, width=1)

    # ---- 右：统计
    x = 700
    s.d.text((x, 400), "统计", font=cjk(16, True), fill=INK)
    s.lines((x, 438), [
        f"词组数        {len(values)}",
        f"扩展消耗      {len(used)} 个词组",
        f"十六进制数位  {len(digits)}",
        f"字节数        {len(data)}",
        f"数位长度      {len(hex_text)}（偶数：{len(hex_text) % 2 == 0}）",
    ], size=14, lh=26)

    s.d.text((x, 600), "16 处扩展的分布", font=cjk(16, True), fill=INK)
    marks = [u["mark"] for u in used]
    s.lines((x, 638), [
        f"诚信(10)   {marks.count(10)} 处",
        f"友善(11)   {marks.count(11)} 处",
        f"首处位于第 {used[0]['at']} 个数位",
        f"末处位于第 {used[-1]['at']} 个数位",
    ], size=14, lh=26)

    # ---- 底部：完整 hex 串
    s.d.text((60, 620), f"完整十六进制串（{len(hex_text)} 位，每行 {len(hex_text)//2} 个字符）", font=cjk(16), fill=INK)
    half = len(hex_text) // 2
    s.d.text((60, 656), hex_text[:half], font=mono(15), fill=INK)
    s.d.text((60, 682), hex_text[half:], font=mono(15), fill=INK)
    s.d.text((60, 722), "59 个字节，全部落在可打印 ASCII 区间 —— 这就是明文的原始字节。",
             font=cjk(15), fill=GREEN)
    s.foot("步骤 5 / 6　·　到这一步已经拿到字节，只差一次 UTF-8 解码")
    s.save("05_扩展标记与字节流.png")

    return rows


def run():
    prepare()
    print("[step5] 扩展标记 → 数位 → 字节")
    values = json.loads((WORK / "values.json").read_text(encoding="utf-8"))
    digits, used = expand(values)
    hex_text = "".join(format(d, "x") for d in digits)
    (WORK / "hex.txt").write_text(hex_text, encoding="utf-8")
    data = bytes.fromhex(hex_text)
    (WORK / "stage2.bin").write_bytes(data)
    print(f"    数位 {len(digits)}，扩展消耗 {len(used)}，字节 {len(data)}")
    u0 = used[0]
    base = 10 if u0["mark"] == 10 else 6
    print(f"    首处扩展：第 {u0['at']} 个数位，{u0['mark']}→{base} + {u0['next']} = {u0['value']}")
    print(f"    hex: {hex_text}")
    draw(values, digits, used, data, hex_text)
    return digits, data


if __name__ == "__main__":
    run()
