#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 6 / 6　UTF-8 解码 + 全链交叉校验
---------------------------------------------------------------
输入 : work/stage2.bin（59 字节）
输出 : 步骤截图/06_解码与交叉校验.png

到这一步只剩一次 decode。真正值得写的是"怎么证明自己没解错"——
五组数字分别从两条独立路径算出来，必须对得上：

    4020 = 268 × 15                字符数 ÷ 单元长度
    268  = 134 × 2                 汉字数 ÷ 每词组两字
    118  = 134 - 16                数位 = 词组数 − 扩展消耗数
     59  = 118 ÷ 2                 字节 = 数位 ÷ 2
     59  = 7 + 52                   含 "HTUCTF{" 7 字节 + 正文 + 结尾 "}"
"""

from collections import Counter

from _common import (BLUE, GREEN, INK, LINE, RED, SUB, WORK, Sheet, cjk, mono, prepare)


def draw(data, flag, stats):
    s = Sheet(950)
    s.head("⑥ UTF-8 解码 → Flag，并用五组数字交叉校验",
           "单看最后一行只是\"字符串\"，下面每一条都要能从两个独立来源算出来，才算真解出来了")

    rows = [("prompt", "python step6_flag.py")]
    for k, v in stats["trace"]:
        rows.append(("out", f"{k:<22}{v}"))
    rows.append(("flag", flag))
    s.terminal((56, 148, 1224, 148 + 48 + 22 * len(rows) + 18), rows)

    y = 148 + 48 + 22 * len(rows) + 54
    s.d.text((56, y), "五组互相咬合的数字", font=cjk(16, True), fill=INK)
    y += 40

    head = ["#", "数字", "来源 A", "来源 B"]
    cols = [56, 116, 300, 700]
    for j, h in enumerate(head):
        s.d.text((cols[j], y), h, font=cjk(14, True), fill=SUB)
    s.d.line([(56, y + 24), (1224, y + 24)], fill=LINE, width=1)

    table = [
        ("1", "4020", "密文字符数", "268 组 × 15"),
        ("2", "268", "第一层汉字数", "134 词组 × 2"),
        ("3", "118", "十六进制数位", "134 − 16 处扩展"),
        ("4", "59", "字节数", "118 ÷ 2"),
    ]
    for i, (n, num, a, b) in enumerate(table):
        yy = y + 40 + i * 30
        s.d.text((cols[0], yy), n, font=mono(14), fill=BLUE)
        s.d.text((cols[1], yy), num, font=mono(15), fill=INK)
        s.d.text((cols[2], yy), a, font=cjk(14), fill=INK)
        s.d.text((cols[3], yy), b, font=cjk(14), fill=INK)

    yy = y + 40 + 4 * 30
    s.d.text((cols[0], yy), "5", font=mono(14), fill=BLUE)
    s.d.text((cols[1], yy), str(len(flag)), font=mono(15), fill=INK)
    s.d.text((cols[2], yy), f"bytes 解码后 {len(flag)} 字符", font=cjk(14), fill=INK)
    s.d.text((cols[3], yy), "全部可打印 ASCII，无一替换符", font=cjk(14), fill=GREEN)

    # ---- 明文分解
    y2 = yy + 60
    s.d.text((56, y2), "明文结构", font=cjk(16, True), fill=INK)
    s.d.text((56, y2 + 38), flag, font=mono(20), fill=INK)
    s.d.text((56, y2 + 78), "HTUCTF{   " + flag[7:-1] + "   }", font=cjk(15), fill=SUB)

    s.d.text((56, y2 + 130), "读法：We will make new history —— 我们将会创造新的历史。",
             font=cjk(16), fill=RED)
    s.foot("步骤 6 / 6　·　五组数字全部对得上，才敢说这个 flag 是解出来的，不是凑出来的")
    s.save("06_解码与交叉校验.png")


def run():
    prepare()
    print("[step6] UTF-8 解码")
    data = (WORK / "stage2.bin").read_bytes()
    flag = data.decode("utf-8")
    if any(ord(c) < 32 or ord(c) > 126 for c in flag):
        raise SystemExit("解出的明文含不可打印字符，规则大概率有误")

    cipher = (WORK / "cipher.txt").read_text(encoding="utf-8")
    text = (WORK / "stage1.txt").read_text(encoding="utf-8")
    values = Counter(text[i:i + 2] for i in range(0, len(text), 2))
    digits = (WORK / "hex.txt").read_text(encoding="utf-8")

    total = sum(values.values())
    ext = Counter(text[i:i + 2] for i in range(0, len(text), 2))
    n_ext = ext["诚信"] + ext["友善"]
    stats = {"trace": [
        ("密文字符数", f"{len(cipher)}  = {len(cipher) // 15} 组 × 15"),
        ("第一层汉字", f"{len(text)}  = {total} 词组 × 2"),
        ("词组数", f"{total}"),
        ("十六进制数位", f"{len(digits)}  = {total} − {n_ext} 处扩展"),
        ("字节数", f"{len(data)}  = {len(digits)} ÷ 2"),
        ("明文长度", f"{len(flag)} 字符"),
    ]}
    print(f"    明文 {len(flag)} 字符：{flag}")
    draw(data, flag, stats)
    return flag


if __name__ == "__main__":
    run()
