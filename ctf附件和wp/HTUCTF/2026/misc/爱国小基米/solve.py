#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
solve.py —— 一键跑完整条链

    python solve.py

它只是把 step1 ~ step6 依次调起来；想单独跑某一步（比如只想重画第 3 张图），
直接执行对应的 step 脚本即可，它会自动读上一步落在 work/ 里的产物：

    python step1_unpack.py    解包 + 字符集普查
    python step2_parse.py     按 15 一组解析头部
    python step3_shift.py     循环左移 + 码点还原
    python step4_values.py    词组 → 数值
    python step5_hex.py       扩展标记 → 十六进制数位 → 字节
    python step6_flag.py      UTF-8 解码 + 交叉校验
"""

import time

import step1_unpack
import step2_parse
import step3_shift
import step4_values
import step5_hex
import step6_flag

STEPS = [
    ("解包 + 字符集普查", step1_unpack),
    ("分组与头部参数", step2_parse),
    ("循环左移与码点", step3_shift),
    ("词组映射与数值", step4_values),
    ("扩展标记与字节流", step5_hex),
    ("解码与交叉校验", step6_flag),
]


def main():
    t0 = time.time()
    flag = None
    for i, (name, mod) in enumerate(STEPS, 1):
        print(f"\n=== [{i}/6] {name} ===")
        flag = mod.run()
    print(f"\n全部完成，用时 {time.time() - t0:.1f}s")
    print(f"Flag: {flag}")


if __name__ == "__main__":
    main()
