#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
solve.py —— 一键跑完整条链

    python solve.py

它只是把 step1 ~ step8 依次调起来，方便一次跑完；想单独跑某一步
（比如只想重画第 5 张图），直接执行对应的 step 脚本：

    python step1_unpack.py     解包 + 拆帧
    python step2_find_odd.py   找异常帧
    python step3_sample.py     采样 29×29
    python step4_gaps.py       定位三个缺口
    python step5_patch.py      补定位图形
    python step6_verify.py     自检
    python step7_render.py     出图
    python step8_decode.py     扫码 + 自解析
"""

import time

import step1_unpack
import step2_find_odd
import step3_sample
import step4_gaps
import step5_patch
import step6_verify
import step7_render
import step8_decode

STEPS = [
    ("拆帧", step1_unpack),
    ("找异常帧", step2_find_odd),
    ("采样矩阵", step3_sample),
    ("定位缺口", step4_gaps),
    ("补定位图形", step5_patch),
    ("自检", step6_verify),
    ("出图", step7_render),
    ("扫码 + 复核", step8_decode),
]


def main():
    t0 = time.time()
    flag = None
    for i, (name, mod) in enumerate(STEPS, 1):
        print(f"\n=== [{i}/8] {name} ===")
        flag = mod.run()
    print(f"\n全部完成，用时 {time.time() - t0:.1f}s")
    print(f"Flag: {flag}")


if __name__ == "__main__":
    main()
