#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 1 / 6　解包 + 字符集普查
---------------------------------------------------------------
输入 : 哈基米南北绿豆.zip
输出 : work/cipher.txt                    纯密文（4020 字符）
       步骤截图/01_解包与字符集普查.png

这一步只做三件事，全部是"先看再猜"：
    1. 解包，确认里面只有一个 txt；
    2. 数清字符集——只有 {哈, 基, 米} 三种，说明是"三态 → 三进制"；
    3. 量长度——4020。这个数不是随便定的：4020 = 268 × 15，
       而 15 正好是"3 位头部 + 12 位数据"的一组，暗示后面是按组解析。
"""

from collections import Counter
from zipfile import ZipFile

from _common import (AMBER, BLUE, HERE, INK, LINE, RED, SUB, TRIT_COLOR, WORK,
                     Sheet, cjk, mono, prepare)

TRIT = {"哈": 0, "基": 1, "米": 2}


def unpack():
    zips = sorted(HERE.glob("*.zip"))
    if not zips:
        raise SystemExit("当前目录没有 .zip")
    src = zips[0]
    with ZipFile(src) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".txt")]
        if not names:
            raise SystemExit("压缩包里没有 txt")
        info = z.getinfo(names[0])
        data = z.read(names[0]).decode("utf-8").strip()
    (WORK / "cipher.txt").write_text(data, encoding="utf-8")
    return data, src.name, names[0], info.file_size


def draw(data, zipname, txtname, size):
    s = Sheet(880)
    s.head("① 解包 + 字符集普查",
           f"{zipname} → {txtname}（{size} 字节）；{len(data)} 个字符，字符集只有 3 个字")

    # ---- 左：整个密文画成三色带（一字符 = 一个 6×6 方块）
    cols, cell = 67, 6
    x0, y0 = 60, 176
    for i, ch in enumerate(data):
        r, c = divmod(i, cols)
        s.d.rectangle([x0 + c * cell, y0 + r * cell,
                       x0 + c * cell + cell - 1, y0 + r * cell + cell - 1],
                      fill=TRIT_COLOR[ch])
    rows = (len(data) + cols - 1) // cols
    s.d.rectangle([x0 - 1, y0 - 1, x0 + cols * cell, y0 + rows * cell], outline=LINE, width=2)
    s.d.text((60, 176 + rows * cell + 14), f"整段密文 {len(data)} 字符（{rows} 行 × {cols} 列，一字一格）",
             font=cjk(14), fill=SUB)

    # 图例
    lx = 60
    for ch, col in TRIT_COLOR.items():
        s.d.rectangle([lx, 176 + rows * cell + 44, lx + 14, 176 + rows * cell + 58], fill=col)
        s.d.text((lx + 20, 176 + rows * cell + 43), f"{ch} = {TRIT[ch]}", font=cjk(14), fill=INK)
        lx += 110
    s.d.text((lx + 20, 176 + rows * cell + 43), "三种颜色均匀分布，没有成片空白",
             font=cjk(14), fill=SUB)

    # ---- 右：统计
    cnt = Counter(data)
    x = 700
    s.d.text((x, 170), "普查结果", font=cjk(17, True), fill=INK)
    s.lines((x, 208), [
        f"字符总数        {len(data)}",
        f"字符集          哈 / 基 / 米   共 {len(cnt)} 种",
        f"换行、空格      0",
        f"哈 出现         {cnt['哈']} 次",
        f"基 出现         {cnt['基']} 次",
        f"米 出现         {cnt['米']} 次",
    ], size=15, lh=27)

    s.d.text((x, 400), "两条推断", font=cjk(17, True), fill=INK)
    s.lines((x, 438), [
        "① 3 个字 → 天然就是三进制的一位数。",
        "② 4020 = 268 × 15，能整除以 15；",
        "   而 15 = 3 + 12，正好是「3 位头部 +",
        "   12 位数据」一组。",
    ], size=14, lh=26)

    s.d.text((x, 590), "为什么不是摩斯/培根/替换密码", font=cjk(17, True), fill=INK)
    s.lines((x, 628), [
        "替换密码：只有 3 个符号，无法表达字母表；",
        "摩斯：需要分隔符，这里 4020 是连续流；",
        "培根：5 位一组，4020 不能被 5 之外的 15 整除得这么整齐。",
    ], size=14, lh=26)

    s.d.text((56, 800), "结论：三个字当三进制数字，按 15 一组的变长单元来切。",
             font=cjk(16, True), fill=RED)
    s.foot("步骤 1 / 6　·　字符集决定进制，长度决定分组")
    s.save("01_解包与字符集普查.png")


def run():
    prepare()
    print("[step1] 解包 + 字符集普查")
    data, zipname, txtname, size = unpack()
    cnt = Counter(data)
    print(f"    {zipname} → {txtname}（{size} 字节）")
    print(f"    字符数 {len(data)}，字符集 {sorted(cnt)}，分布 {dict(cnt)}")
    print(f"    4020 % 15 = {len(data) % 15}")
    draw(data, zipname, txtname, size)
    return data


if __name__ == "__main__":
    run()
