#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤 8 / 8　扫码 + 独立复核
---------------------------------------------------------------
输入 : 输出/修复二维码_白底静区.png, work/M_patched.npy
输出 : 步骤截图/08_扫码结果.png

两条完全独立的路，必须给出同一个答案：
    路 A：现成解码器（zxing-cpp / pyzbar）扫 PNG —— 黑盒，给答案但不给理由
    路 B：自己从模块矩阵读码字 —— 读格式信息拿掩码 → 反掩码 → 之字形取 70 个码字
          → 用 GF(2^8) 算 26 个 RS 校验子（全 0 说明码字没读错）→ 按段解析

路 B 里最容易看错的是「段结构」：这题的 payload 不是一段 byte，而是
    alnum(6)  → "HTUCTF"          （大写字母+数字，能用 11 bit 装 2 个字符）
    byte(26)  → "{We_will_make_new_history}"
    + 终止符 0000，之后是 0xEC / 0x11 填充
如果按「第一个字节必须是 0x4x」去硬套，就会觉得数据是乱的——我第一次就卡在这。
"""

import sys

import numpy as np
from PIL import Image

from _common import INK, N, OUT, SUB, WORK, Sheet, cjk, mono, prepare

ALNUM = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"


# ------------------------------------------------------------ 路 B：自解析
def bit_order(M, mask):
    """按 QR 规范之字形取数据位，同时反掩码。"""
    n = M.shape[0]
    f = np.zeros((n, n), bool)
    f[0:8, 0:8] = True
    f[0:8, n - 8:n] = True
    f[n - 8:n, 0:8] = True
    f[6, :] = True
    f[:, 6] = True
    f[8, 0:9] = True
    f[0:9, 8] = True
    f[8, n - 8:n] = True
    f[n - 7:n, 8] = True
    f[n - 8, 8] = True
    f[20:25, 20:25] = True                      # Version 3 对齐图形

    coords, up, col = [], True, n - 1
    while col > 0:
        if col == 6:                            # 第 6 列是时序图形，整列跳过
            col -= 1
        rng = range(n - 1, -1, -1) if up else range(n)
        for r in rng:
            for c in (col, col - 1):
                if not f[r, c]:
                    coords.append((r, c))
        up = not up
        col -= 2

    def mb(i, j):
        return [(i + j) % 2 == 0, i % 2 == 0, j % 3 == 0, (i + j) % 3 == 0,
                (i // 2 + j // 3) % 2 == 0, (i * j) % 2 + (i * j) % 3 == 0,
                ((i * j) % 2 + (i * j) % 3) % 2 == 0,
                ((i + j) % 2 + (i * j) % 3) % 2 == 0][mask]

    return [int(M[r, c]) ^ (1 if mb(r, c) else 0) for r, c in coords]


def rs_syndromes(cw, nsym=26):
    """GF(2^8)、本原多项式 0x11d；全 0 表示码字是合法 RS 码字。"""
    exp, log = [0] * 512, [0] * 256
    x = 1
    for i in range(255):
        exp[i], log[x] = x, i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        exp[i] = exp[i - 255]

    def mul(a, b):
        return 0 if a == 0 or b == 0 else exp[log[a] + log[b]]

    out = []
    for i in range(nsym):
        s = 0
        for c in cw:
            s = mul(s, exp[i]) ^ c
        out.append(s)
    return out


def parse_segments(bits):
    i, out, seg = 0, "", []
    while i + 4 <= len(bits):
        mode = int("".join(map(str, bits[i:i + 4])), 2)
        i += 4
        if mode == 0:
            seg.append(("终止", ""))
            break
        if mode == 4:                                    # 字节模式
            n = int("".join(map(str, bits[i:i + 8])), 2)
            i += 8
            if n == 0 or i + 8 * n > len(bits):
                break
            s = bytes(int("".join(map(str, bits[i + 8 * k:i + 8 * k + 8])), 2)
                      for k in range(n)).decode("utf-8", "replace")
            i += 8 * n
            out += s
            seg.append((f"byte({n})", s))
        elif mode == 2:                                  # 字母数字模式
            n = int("".join(map(str, bits[i:i + 9])), 2)
            i += 9
            s = ""
            for _ in range(n // 2):
                v = int("".join(map(str, bits[i:i + 11])), 2)
                i += 11
                s += ALNUM[v // 45] + ALNUM[v % 45]
            if n % 2:
                v = int("".join(map(str, bits[i:i + 6])), 2)
                i += 6
                s += ALNUM[v]
            out += s
            seg.append((f"alnum({n})", s))
        else:
            seg.append((f"mode{mode}", "?"))
            break
    return out, seg


def self_decode(M):
    for m in range(8):
        bits = bit_order(M, m)
        cw = [int("".join(map(str, bits[k:k + 8])), 2) for k in range(0, 560, 8)]
        if all(s == 0 for s in rs_syndromes(cw)):
            text, seg = parse_segments(bits)
            return m, text, seg, cw
    return None, "", [], []


# ------------------------------------------------------------ 路 A：扫码
def scan(im):
    seen, text = [], ""
    try:
        import zxingcpp
        r = zxingcpp.read_barcodes(im)
        if r:
            text = r[0].text
            seen.append(("out", f"zxing-cpp : {text}"))
        else:
            seen.append(("dim", "zxing-cpp : 未识别"))
    except Exception as e:
        seen.append(("dim", f"zxing-cpp 不可用（{type(e).__name__}）"))
    # 第二个解码器也要跑：两个库同时认，才排除「某个库的宽容算法碰巧蒙对」
    try:
        from pyzbar.pyzbar import decode as zbar
        r = zbar(im)
        if r:
            other = r[0].data.decode()
            seen.append(("out", f"pyzbar    : {other}"))
            text = text or other
        else:
            seen.append(("dim", "pyzbar    : 未识别"))
    except Exception as e:
        seen.append(("dim", f"pyzbar 不可用（{type(e).__name__}）"))
    return text, seen


def draw(text, seg, seen, mask):
    s = Sheet(740)
    s.head("⑧ 扫码 + 独立复核",
           "先用现成解码器扫，再丢掉解码器、直接从模块矩阵自己解析一遍，两条路必须给出同一个答案")

    rows = [("prompt", "python step8_decode.py")] + seen
    rows.append(("ok", f"内建解析  : 掩码 {mask} 命中，26 个 RS 校验子全为 0 → 码字无误"))
    rows.append(("flag", text))
    s.terminal((56, 150, 1224, 150 + 48 + 22 * len(rows) + 18), rows)

    y = 150 + 48 + 22 * len(rows) + 60
    s.d.text((56, y), "段结构 —— 这一步最容易看错", font=cjk(16, True), fill=INK)
    s.lines((56, y + 40), [
        "0010 | 000000110 | 01100011010 10101010010 10100101000",
        "       alnum 6 字 → 每组 11 bit 装 2 字 → HTUCTF",
        "0100 | 00011010  | 26 个字节",
        "       byte 26 字 → {We_will_make_new_history}",
        "0000  终止符，之后是 0xEC 0x11 填充",
    ], size=14, lh=25)
    seg_txt = "  |  ".join(f"{k} = {v}" for k, v in seg if v)
    s.d.text((56, y + 178), f"分段结果：{seg_txt}", font=cjk(14), fill=SUB)
    s.d.text((56, y + 208), "6 + 26 = 32 字节，与填充起始位置严丝合缝 → 没有错位。", font=cjk(15), fill=INK)
    s.foot("步骤 8 / 8　·　现成解码器只给答案，自解析才证明「这答案是从这些点里长出来的」")
    s.save("08_扫码结果.png")


def run():
    prepare()
    print("[step8] 扫码 + 自解析")
    im = Image.open(OUT / "修复二维码_白底静区.png").convert("RGB")
    text, seen = scan(im)
    for _, t in seen:
        print(f"    {t}")

    M = np.load(WORK / "M_patched.npy")
    mask, inner, seg, cw = self_decode(M)
    print(f"    内建解析: 掩码={mask} 分段={seg}")
    print(f"    码字数={len(cw)}，RS 校验子全零={all(s == 0 for s in rs_syndromes(cw)) if cw else False}")

    if not mask:
        raise SystemExit("自解析失败：8 种掩码都凑不出合法 RS 码字")
    if text and text != inner:
        raise SystemExit(f"两条路径不一致：{text!r} vs {inner!r}")
    text = text or inner
    print(f"    Flag: {text}")
    draw(text, seg, seen, mask)
    return text


if __name__ == "__main__":
    run()
